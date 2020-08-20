# -*- encoding: utf-8 -*-

import glob
import os

from lxml import etree

from perfectextractor.apps.extractor.base import BaseExtractor
from perfectextractor.apps.extractor.utils import XML
from .base import BaseDPC, TEI_NS
from .utils import is_nl, NL


class DPCExtractor(BaseDPC, BaseExtractor):
    def list_filenames(self, dir_name):
        return sorted(glob.glob(os.path.join(dir_name, '*[0-9]-' + self.l_from + '-tei.xml')))

    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        raise NotImplementedError

    def generate_translations(self, alignment_trees, translation_trees, sentence):
        result = []

        for language_to in self.l_to:
            if language_to in translation_trees:
                translated_lines, alignment_type = self.get_translated_lines(alignment_trees, self.l_from, language_to, sentence.get('n'))
                translated_sentences = [self.get_line_as_xml(translation_trees[language_to], line) for line in translated_lines]
                result.append('\n'.join([self.mark_sentence(ts) for ts in translated_sentences]) if translated_sentences else '')
            else:
                # If no translation is available, add empty columns
                result.extend([''] * 2)

        return result

    def get_line_as_xml(self, tree, segment_number):
        return tree.xpath('//ns:s[@n="' + segment_number + '"]', namespaces=TEI_NS)[0]

    def mark_sentence(self, sentence, match=None):
        # TODO: this is copied from apps/models.py. Consider refactoring!
        s = []
        # TODO: this xPath-expression is specific for a corpus
        for w in sentence.xpath('.//ns:w', namespaces=TEI_NS):
            s.append(w.text.strip() if w.text else ' ')
        return ' '.join(s)

    def parse_alignment_trees(self, filename):
        document = filename.split(self.l_from + '-tei.xml')[0]
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

        return alignment_trees, translation_trees

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
            for link in alignment_trees[not_nl].xpath('//ns:link', namespaces=TEI_NS):  # TODO: simplify this
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
        return element.xpath('ancestor::ns:s', namespaces=TEI_NS)[0]

    def get_siblings(self, element, sentence_id, check_preceding):
        return element.itersiblings(preceding=check_preceding)

    def sort_by_alignment_certainty(self, file_names):
        raise NotImplementedError

    def filter_by_file_size(self, file_names):
        raise NotImplementedError

    def get_type(self, sentence, mwe=None):
        # TODO: implement
        raise NotImplementedError
