import ConfigParser
import codecs
import glob
import string
import os
import time

from lxml import etree

from .utils import UnicodeWriter
from .models import PresentPerfect
from .wiktionary import get_translations
from .xml_utils import get_sentence, get_sentence_from_element, get_siblings, get_original_language

CORPUS_CONFIG = os.path.join(os.path.dirname(__file__), '../config/europarl.cfg')
AUX_BE_CONFIG = os.path.join(os.path.dirname(__file__), '../config/{language}_aux_be.txt')


class PerfectExtractor:
    def __init__(self, language_from, languages_to):
        self.l_from = language_from
        self.l_to = languages_to

        # Read the config
        config = ConfigParser.RawConfigParser()
        config.readfp(codecs.open(CORPUS_CONFIG, 'r', 'utf8'))
        self.config = config

        # Read the list of verbs that use 'to be' as auxiliary verb per language
        self.aux_be_list = {}
        for language in [language_from] + languages_to:
            aux_be_list = []
            if self.config.get(language, 'lexical_bound'):
                with codecs.open(AUX_BE_CONFIG.format(language=language), 'rb', 'utf-8') as lexicon:
                    aux_be_list = lexicon.read().split()
            self.aux_be_list[language] = aux_be_list

    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        """
        Returns the translated segment numbers (could be multiple) for a segment number in the original text.

        Alignment line look like this:
            <linkGrp targType="s" fromDoc="en/ep-00-01-17.xml.gz" toDoc="nl/ep-00-01-17.xml.gz">
                <link xtargets="1;1" />
                <link xtargets="2;2 3" />
                <link xtargets="3;4 5" />
            </linkGrp>

        To get from language A to B, we should order the languages

        This function supports n-to-n alignments, as it will return both the source and translated lines as a list.
        """
        from_lines = []
        to_lines = []

        sl = sorted([language_from, language_to])
        for xtargets in alignment_trees[language_to]:
            if sl[0] == language_from:
                if segment_number in xtargets[0]:
                    from_lines = xtargets[0]
                    to_lines = xtargets[1]
                    break
            else:
                if segment_number in xtargets[1]:
                    from_lines = xtargets[1]
                    to_lines = xtargets[0]
                    break

        alignment = '{} => {}'.format(len(from_lines), len(to_lines)) if to_lines else ''

        return from_lines, to_lines, alignment

    def get_line_by_number(self, tree, language_to, segment_number):
        """
        Returns the full line for a segment number, as well as the PresentPerfect found (or None if none found).
        TODO: handle more than one here? => bug
        """
        sentence = '-'
        pp = None

        line = tree.xpath('//s[@id="' + segment_number + '"]')
        if line:
            s = line[0]
            first_w = s.xpath('.//w')[0]
            sentence = get_sentence_from_element(first_w)
            for e in s.xpath(self.config.get(language_to, 'xpath')):
                pp = self.check_present_perfect(e, language_to)
                if pp:
                    sentence = pp.mark_sentence()
                    break

        return etree.tostring(s), sentence, pp

    def is_lexically_bound(self, language, aux_verb, perfect):
        """
        Checks if the perfect is lexically bound to the auxiliary verb.
        If not, we are not dealing with a present perfect here.
        """
        aux_be = self.config.get(language, 'lexical_bound')

        # If lexical bounds do not exist or we're dealing with an auxiliary verb that is unbound, return True
        if not aux_be or aux_verb.get('lem') != aux_be:
            return True
        # Else, check whether the perfect is in the list of bound verbs
        else:
            return perfect.get('lem') in self.aux_be_list[language]

    def check_present_perfect(self, element, language, check_ppc=True, check_preceding=False):
        """
        Checks whether this element is the start of a present perfect (or pp continuous).
        If it is, the present perfect is returned as a list.
        If not, None is returned.
        """
        perfect_tag = self.config.get(language, 'perfect_tag')
        check_ppc = check_ppc and self.config.getboolean(language, 'ppc')
        ppc_lemma = self.config.get(language, 'ppc_lemma')
        stop_tags = tuple(self.config.get(language, 'stop_tags').split(','))
        allow_reversed = self.config.getboolean(language, 'allow_reversed')

        # Collect all parts of the present perfect as tuples with text and whether it's verb
        pp = PresentPerfect(element.text, element.get('lem'), element.get('id'), get_sentence(element))

        is_pp = False
        for sibling in get_siblings(element, pp.get_sentence_id(), check_preceding):
            # If the tag of the sibling is the perfect tag, we found a present perfect!
            sibling_pos = sibling.get(self.config.get(language, 'pos'))
            if sibling_pos == perfect_tag:
                # Check if the sibling is lexically bound to the auxiliary verb
                # (only if we're not checking for present perfect continuous)
                if check_ppc and not self.is_lexically_bound(language, element, sibling):
                    break
                pp.add_word(sibling.text, sibling.get('lem'), True, sibling.get('id'))
                is_pp = True
                # ... now check whether this is a present perfect continuous (by recursion)
                if check_ppc and sibling.get('lem') == ppc_lemma:
                    ppc = self.check_present_perfect(sibling, language, False)
                    if ppc:
                        pp.extend(ppc)
                break
            # Stop looking at punctuation or stop tags
            elif sibling.text in string.punctuation or (sibling_pos and sibling_pos.startswith(stop_tags)):
                break
            # No break? Then add as a non-verb part
            else:
                pp.add_word(sibling.text, sibling.get('lem'), False, sibling.get('id'))

        if not is_pp and allow_reversed and not check_preceding:
            pp = self.check_present_perfect(element, language, check_ppc, True)
            if pp:
                is_pp = True

        return pp if is_pp else None

    def find_translated_present_perfects(self, translated_tree, language_to, translated_lines):
        """
        Finds present perfects in translated sentences.
        """
        translated_pps = []
        translated_sentences = []
        translated_marked_sentences = []

        if translated_lines and any(translated_lines):
            for t in translated_lines:
                sentence, translation, translated_pp = self.get_line_by_number(translated_tree, language_to, t)
                translated_pps.append(translated_pp)
                translated_sentences.append(sentence)
                translated_marked_sentences.append(translation)

        return translated_pps, translated_sentences, translated_marked_sentences

    def process_folder(self, dir_name):
        """
        Creates a result file and processes each file in a folder.
        """
        result_file = '-'.join([dir_name, self.l_from]) + '.csv'
        with open(result_file, 'wb') as f:
            f.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
            csv_writer = UnicodeWriter(f, delimiter=';')

            header = [
                'document',
                'original_language',
                'present perfect ' + self.l_from,
                'present perfect ids',
                'xml',
                self.l_from]
            for language in self.l_to:
                header.append('present perfect ' + language)
                header.append('is translation?')
                header.append('alignment type')
                header.append('xml')
                header.append(language)
            csv_writer.writerow(header)

            for filename in glob.glob(os.path.join(dir_name, '*.xml')):
                results = self.process_file(filename)
                csv_writer.writerows(results)

    def check_translated_pps(self, pp, translated_present_perfects, language_to):
        """
        Checks whether the translated present perfects found form an actual translation of the present perfect.
        """
        results = []
        for tpp in translated_present_perfects:
            if tpp:
                translations = get_translations(pp.perfect_lemma(), self.l_from, language_to)
                if tpp.perfect_lemma() in translations:
                    results.append('yes')
                else:
                    results.append('unknown')
        return results

    def process_file(self, filename):
        """
        Processes a single file.
        """
        t0 = time.time()
        print 'Now processing ' + filename + '...'

        document = os.path.basename(filename)
        results = []

        # Parse the current tree
        tree = etree.parse(filename)

        # Parse the trees with the translations
        alignment_trees = dict()
        translation_trees = dict()
        for language_to in self.l_to:
            sl = sorted([self.l_from, language_to])
            alignment_file = os.path.join('data', '-'.join(sl) + '.xml')
            if os.path.isfile(alignment_file):
                alignment_tree = etree.parse(alignment_file)
                sl = sorted([self.l_from, language_to])
                doc = '{}/{}.gz'.format(sl[0], document)
                links = [link.get('xtargets').split(';') for link in alignment_tree.xpath('//linkGrp[@fromDoc="' + doc + '"]/link')]
                alignment_trees[language_to] = [[la.split(' '), lb.split(' ')] for la, lb in links]

            translation_file = filename.replace(self.l_from, language_to)
            if os.path.isfile(translation_file):
                translation_trees[language_to] = etree.parse(translation_file)

        t1 = time.time()
        print 'Finished alignment trees, took {:.3} seconds'.format(t1 - t0)

        # Find potential present perfects
        for e in tree.xpath(self.config.get(self.l_from, 'xpath')):
            pp = self.check_present_perfect(e, self.l_from)

            # If this is really a present perfect, add it to the result
            if pp:
                result = list()
                result.append(document)
                result.append(get_original_language(e))
                result.append(pp.verbs_to_string())
                result.append(pp.verb_ids())

                # Write the complete segment with mark-up
                result.append('<root>' + etree.tostring(pp.xml_sentence) + '</root>')
                result.append(pp.mark_sentence())

                # Find the translated lines
                segment_number = pp.get_sentence_id()
                for language_to in self.l_to:
                    if language_to in translation_trees:
                        # TODO: deal with source_lines
                        source_lines, translated_lines, alignment_type = self.get_translated_lines(alignment_trees,
                                                                                                   self.l_from,
                                                                                                   language_to,
                                                                                                   segment_number)
                        translated_present_perfects, translated_sentences, translated_marked_sentences = \
                             self.find_translated_present_perfects(translation_trees[language_to], language_to, translated_lines)
                        result.append('\n'.join([tpp.verbs_to_string() if tpp else '' for tpp in translated_present_perfects]))
                        # result.append('\n'.join(self.check_translated_pps(pp, translated_present_perfects, language_to)))
                        result.append('')
                        result.append(alignment_type)
                        result.append('<root>' + '\n'.join(translated_sentences) + '</root>' if translated_sentences else '')
                        result.append('\n'.join(translated_marked_sentences))
                    else:
                        # If no translation is available, add empty columns
                        result.extend([''] * 5)

                results.append(result)

        print 'Finished finding present perfects, took {:.3} seconds'.format(time.time() - t1)

        return results
