import glob
import os

from lxml import etree

from perfectextractor.apps.extractor.base import BaseExtractor
from perfectextractor.apps.extractor.perfectextractor import PerfectExtractor
from .utils import is_nl, NL

DPC_CONFIG = os.path.join(os.path.dirname(__file__), 'dpc.cfg')
TEI = {'ns': 'http://www.tei-c.org/ns/1.0'}


class DPCExtractor(BaseExtractor):
    def get_config(self):
        return DPC_CONFIG

    def process_file(self, filename):
        raise NotImplementedError

    def list_filenames(self, dir_name):
        return sorted(glob.glob(os.path.join(dir_name, '*[0-9]-' + self.l_from + '-tei.xml')))

    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        """
        Returns the translated segment numbers (could be multiple) for a segment number in the original text.

        The translation document file format either ends with nl-en-tei.xml or nl-fr-tei.xml.

        Alignment lines look like this:
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

    def get_sentence(self, element):
        return element.xpath('ancestor::ns:s', namespaces=TEI)[0]

    def get_siblings(self, element, sentence_id, check_preceding):
        return element.itersiblings(preceding=check_preceding)

    def sort_by_alignment_certainty(self, file_names):
        raise NotImplementedError

    def filter_by_file_size(self, file_names):
        raise NotImplementedError


class DPCPerfectExtractor(PerfectExtractor, DPCExtractor):
    def get_line_and_pp(self, tree, language_to, segment_number):
        """
        Returns the full line for a segment number, as well as the Perfect found (or None if none found).
        TODO: handle more than one here? => bug
        """
        sentence = '-'
        pp = None

        line = tree.xpath('//ns:s[@n="' + segment_number + '"]', namespaces=TEI)
        if line:
            s = line[0]
            sentence = s.getprevious().text

            if self.search_in_to:
                for e in s.xpath(self.config.get(language_to, 'xpath'), namespaces=TEI):
                    pp = self.check_perfect(e, language_to)
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

        # Find potential Perfects
        for e in tree.xpath('//' + self.config.get(self.l_from, 'xpath'), namespaces=TEI):
            pp = self.check_perfect(e, self.l_from)

            # If this is really a Perfect, add it to the result
            if pp:
                result = list()
                result.append(document[:-1])
                result.append(self.get_original_language(document))
                result.append(pp.verbs_to_string())

                # Write the complete segment with mark-up
                result.append(pp.mark_sentence())

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
