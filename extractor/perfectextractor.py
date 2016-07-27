import ConfigParser
import codecs
import glob
import string
import os

from lxml import etree

from .utils import UnicodeWriter, is_nl
from .models import PresentPerfect
from .wiktionary import get_translations

DPC_CONFIG = os.path.join(os.path.dirname(__file__), '../config/dpc.cfg')
AUX_BE_CONFIG = os.path.join(os.path.dirname(__file__), '../config/{language}_aux_be.txt')
TEI = {'ns': 'http://www.tei-c.org/ns/1.0'}
NL = 'nl'


class PerfectExtractor:
    def __init__(self, language_from, languages_to):
        self.l_from = language_from
        self.l_to = languages_to

        # Read the config
        config = ConfigParser.RawConfigParser()
        config.readfp(codecs.open(DPC_CONFIG, 'r', 'utf8'))
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

        The translation document file format either ends with nl-en-tei.xml or nl-fr-tei.xml.

        Alignment line look like this:
            <link type="A: 1-1" targets="p1.s1; p1.s1"/>
            <link type="A: 1-2" targets="p1.s9; p1.s9 p1.s10"/>
            <link type="B: 2-1" targets="p1.s24 p1.s25; p1.s25"/>
        
        To get from NL to EN/FR, we have to find the segment number in the targets attribute BEFORE the semicolon.
        For the reverse pattern, we have to find the segment number in the targets attribute AFTER the semicolon.
        
        To get from EN to FR or from FR to EN, we have to use NL as an in between language.

        This function supports 1-to-2 alignments, as it will return the translated lines as a list.

        TODO: deal with 2-to-2 and 2-to-1 alignments as well here.
        """
        result = []
        alignment_type = ''

        if NL in [language_from, language_to]:
            not_nl = language_to if language_to != NL else language_from
            for link in alignment_trees[not_nl].xpath('//ns:link', namespaces=TEI):  # TODO: simplify this
                alignment_type = link.get('type').split(': ')[1]
                if is_nl(language_to):
                    alignment_type = alignment_type[::-1]  # reverse the alignment type
                alignment_type = alignment_type.replace('-', '=>')
                targets = link.get('targets').split('; ')
                if segment_number in targets[1 - is_nl(language_from)].split(' '):
                    result = targets[is_nl(language_from)].split(' ')
                    break
        else:
            lookup, t = self.get_translated_lines(alignment_trees, language_from, NL, segment_number)
            alignment_type = t.split('=>')[0]
            for lookup_number in lookup:
                lines, _ = self.get_translated_lines(alignment_trees, NL, language_to, lookup_number)
                result.extend(lines)

            if result:
                alignment_type += '=>' + str(len(set(result)))
            else:
                alignment_type = ''

        if not result:
            alignment_type = ''

        return set(result), alignment_type

    def get_line_by_number(self, tree, language_to, segment_number):
        """
        Returns the full line for a segment number, as well as the PresentPerfect found (or None if none found).
        TODO: handle more than one here? => bug
        """
        sentence = '-'
        pp = None

        line = tree.xpath('//ns:s[@n="' + segment_number + '"]', namespaces=TEI)
        if line:
            s = line[0]
            sentence = s.getprevious().text
            for e in s.xpath(self.config.get(language_to, 'xpath'), namespaces=TEI):
                pp = self.check_present_perfect(e, language_to)
                if pp: 
                    sentence = pp.mark_sentence()
                    break

        return sentence, pp

    def get_original_language(self, document):
        """
        Returns the original language for a document.
        """
        metadata_tree = etree.parse(document + self.l_from + '-mtd.xml')
        return metadata_tree.getroot().find('metaTrans').find('Original').get('lang')

    def is_lexically_bound(self, language, aux_verb, perfect):
        """
        Checks if the perfect is lexically bound to the auxiliary verb.
        If not, we are not dealing with a present perfect here.
        """
        aux_be = self.config.get(language, 'lexical_bound')

        # If lexical bounds do not exist or we're dealing with an auxiliary verb that is unbound, return True
        if not aux_be or aux_verb.get('lemma') != aux_be:
            return True
        # Else, check whether the perfect is in the list of bound verbs
        else:
            return perfect.get('lemma') in self.aux_be_list[language]

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
        pp = PresentPerfect(element.text, element.get('lemma'), element.get('id'))

        is_pp = False
        for sibling in element.itersiblings(preceding=check_preceding):
            # If the tag of the sibling is the perfect tag, we found a present perfect! 
            if sibling.get('ana') == perfect_tag:
                # Check if the sibling is lexically bound to the auxiliary verb
                if not self.is_lexically_bound(language, element, sibling):
                    break
                pp.add_word(sibling.text, sibling.get('lemma'), True, sibling.get('id'))
                is_pp = True
                # ... now check whether this is a present perfect continuous (by recursion)
                if check_ppc and sibling.get('lemma') == ppc_lemma:
                    ppc = self.check_present_perfect(sibling, language, False)
                    if ppc:
                        pp.extend(ppc)
                break
            # Stop looking at punctuation or stop tags
            elif sibling.text in string.punctuation or sibling.get('ana').startswith(stop_tags):
                break
            # No break? Then add as a non-verb part
            else:
                pp.add_word(sibling.text, sibling.get('lemma'), False, sibling.get('id'))

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

        if translated_lines:
            for t in translated_lines:
                #f.write(get_line_by_number(translated_tree, get_adjacent_line_number(t, -1)) + '\n')
                translation, translated_pp = self.get_line_by_number(translated_tree, language_to, t)
                translated_pps.append(translated_pp)
                translated_sentences.append(translation)
                #f.write(get_line_by_number(translated_tree, get_adjacent_line_number(t, 1)) + '\n')

        return translated_pps, translated_sentences

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
                self.l_from]
            for language in self.l_to:
                header.append('present perfect ' + language)
                header.append('is translation?')
                header.append('alignment type')
                header.append(language)
            csv_writer.writerow(header)

            for filename in glob.glob(os.path.join(dir_name, '*[0-9]-' + self.l_from + '-tei.xml')):
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
        document = filename.split(self.l_from + '-tei.xml')[0]
        results = []

        # Parse the current tree
        tree = etree.parse(filename)

        # Parse the trees with the translations
        translation_trees = dict()
        alignment_trees = dict()
        for language_to in self.l_to:
            translation_file = document + language_to + '-tei.xml'
            if os.path.exists(translation_file):
                translation_trees[language_to] = etree.parse(translation_file)

            not_nl = language_to if language_to != NL else self.l_from
            alignment_file = document + NL + '-' + not_nl + '-tei.xml'
            if os.path.isfile(alignment_file):
                alignment_trees[not_nl] = etree.parse(alignment_file)

        # Find potential present perfects
        for e in tree.xpath('//' + self.config.get(self.l_from, 'xpath'), namespaces=TEI):
            pp = self.check_present_perfect(e, self.l_from)

            # If this is really a present perfect, add it to the result
            if pp:
                result = list()
                result.append(document[:-1])
                result.append(self.get_original_language(document))
                result.append(pp.verbs_to_string())

                # Write the complete segment with mark-up
                result.append(pp.mark_sentence(e.getparent().getprevious().text))

                # Find the translated lines
                segment_number = e.getparent().getparent().get('n')[4:]
                for language_to in self.l_to:
                    if language_to in translation_trees:
                        translated_lines, alignment_type = self.get_translated_lines(alignment_trees, self.l_from,
                                                                                     language_to, segment_number)
                        translated_present_perfects, translated_sentences = \
                            self.find_translated_present_perfects(translation_trees[language_to], language_to, translated_lines)
                        result.append('\n'.join([tpp.verbs_to_string() if tpp else '' for tpp in translated_present_perfects]))
                        result.append('\n'.join(self.check_translated_pps(pp, translated_present_perfects, language_to)))
                        result.append(alignment_type)
                        result.append('\n'.join(translated_sentences))
                    else:
                        # If no translation is available, add empty columns
                        result.extend([''] * 4)

                results.append(result)

        return results
