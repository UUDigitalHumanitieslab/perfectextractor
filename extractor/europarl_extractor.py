import glob
import os
import time

from lxml import etree

from .perfectextractor import PerfectExtractor
from .xml_utils import get_sentence_from_element, get_original_language

EUROPARL_CONFIG = os.path.join(os.path.dirname(__file__), '../config/europarl.cfg')


class EuroparlExtractor(PerfectExtractor):
    def get_config(self):
        return EUROPARL_CONFIG

    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        """
        Returns the translated segment numbers (could be multiple) for a segment number in the original text.

        Alignment lines in the Europarl corpus look like this:
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

        if not any(to_lines):
            to_lines = []

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

            if self.search_in_to:
                for e in s.xpath(self.config.get(language_to, 'xpath')):
                    pp = self.check_present_perfect(e, language_to)
                    if pp:
                        sentence = pp.mark_sentence()
                        break

        return etree.tostring(s), sentence, pp

    def get_sentence(self, element):
        return element.xpath('ancestor::s')[0]

    def get_siblings(self, element, sentence_id, check_preceding):
        path = ('preceding' if check_preceding else 'following') + '::w[ancestor::s[@id="' + sentence_id + '"]]'
        siblings = element.xpath(path)
        if check_preceding:
            siblings = siblings[::-1]
        return siblings

    def list_filenames(self, dir_name):
        return glob.glob(os.path.join(dir_name, '*.xml'))

    def process_file(self, filename):
        """
        Processes a single file.
        """
        t0 = time.time()
        print 'Now processing ' + filename + '...'

        # Parse the current tree
        tree = etree.parse(filename)

        # Parse the alignment and translation trees
        alignment_trees, translation_trees = self.parse_alignment_trees(filename)

        t1 = time.time()
        print 'Finished parsing trees, took {:.3} seconds'.format(t1 - t0)

        results = []
        # Find potential present perfects
        for e in tree.xpath(self.config.get(self.l_from, 'xpath')):
            pp = self.check_present_perfect(e, self.l_from)

            # If this is really a present perfect, add it to the result
            if pp:
                result = list()
                result.append(os.path.basename(filename))
                result.append('')
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

    def parse_alignment_trees(self, filename):
        base_filename = os.path.basename(filename)
        data_folder = os.path.dirname(os.path.dirname(filename))

        alignment_trees = dict()
        translation_trees = dict()
        for language_to in self.l_to:
            sl = sorted([self.l_from, language_to])
            alignment_file = os.path.join(data_folder, '-'.join(sl) + '.xml')
            if os.path.isfile(alignment_file):
                alignment_tree = etree.parse(alignment_file)
                doc = '{}/{}.gz'.format(self.l_from, base_filename)
                path = '@fromDoc="{}"' if sl[0] == self.l_from else '@toDoc="{}"'
                linkGrps = alignment_tree.xpath('//linkGrp[{}]'.format(path.format(doc)))

                if not linkGrps:
                    print 'No translation found for {} to {}'.format(filename, language_to)
                elif len(linkGrps) == 1:
                    linkGrp = linkGrps[0]

                    translation_link = linkGrp.get('toDoc') if sl[0] == self.l_from else linkGrp.get('fromDoc')
                    translation_file = os.path.join(data_folder, translation_link[:-3])
                    translation_trees[language_to] = etree.parse(translation_file)

                    links = [link.get('xtargets').split(';') for link in linkGrp.xpath('./link')]
                    alignment_trees[language_to] = [[la.split(' '), lb.split(' ')] for la, lb in links]
                else:
                    print 'Multiple translations found for {} to {}'.format(filename, language_to)

        return alignment_trees, translation_trees
