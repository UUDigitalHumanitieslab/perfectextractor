# -*- encoding: utf-8 -*-

import os

import click
from lxml import etree

from perfectextractor.apps.extractor.base import BaseExtractor
from perfectextractor.apps.extractor.models import Alignment, MARKUP
from perfectextractor.apps.extractor.utils import XML
from .base import BaseOPUS


class OPUSExtractor(BaseOPUS, BaseExtractor):
    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        """
        Fetches the results for a file
        :param filename: The current filename
        :param s_trees: The XML trees for all 's' elements in the file
        :param alignment_trees: The alignment XML trees, per target language
        :param translation_trees: The translation XML trees, per target language
        :return: All results in a list
        """
        results = list()
        # Loop over all sentences
        for _, s in s_trees:
            result = self.generate_result_line(filename, s)
            result.extend(self.generate_translations(alignment_trees, translation_trees, s))
            results.append(result)
        return results

    def generate_translations(self, alignment_trees, translation_trees, sentence):
        result = []

        for language_to in self.l_to:
            if language_to in translation_trees:
                # TODO: potentially deal with source_lines if len(source_lines) > 1
                source_lines, translated_lines, alignment_type = self.get_translated_lines(alignment_trees, self.l_from, language_to, sentence.get('id'))
                result.append(alignment_type)
                if self.output == XML:
                    translated_sentences = [self.get_line(translation_trees[language_to], line) for line in translated_lines]
                    result.append('<root>' + '\n'.join(translated_sentences) + '</root>' if translated_sentences else '')
                else:
                    translated_sentences = [self.get_line_as_xml(translation_trees[language_to], line) for line in translated_lines]
                    result.append('\n'.join([self.mark_sentence(ts) for ts in translated_sentences]) if translated_sentences else '')
            else:
                # If no translation is available, add empty columns
                result.extend([''] * 2)

        return result

    def get_type(self, sentence, mwe=None):
        raise NotImplementedError

    def mark_sentence(self, sentence, match=None):
        # TODO: this is copied from apps/models.py. Consider refactoring!
        s = []
        # TODO: this xPath-expression is specific for a corpus
        for w in sentence.xpath('.//w'):
            if match is not None and w.get('id') == match.get('id'):
                s.append(MARKUP.format(w.text.strip()))
            else:
                s.append(w.text.strip() if w.text else ' ')
        return ' '.join(s)

    def get_line_by_number(self, tree, segment_number):
        """
        Returns the full line for a segment number.
        TODO: handle more than one here? => bug
        """
        result = None

        line = tree.xpath('//s[@id="' + segment_number + '"]')
        if line is not None:
            result = line[0]

        return result

    def get_sentence(self, element):
        return element.xpath('ancestor::s')[0]

    def get_siblings(self, element, sentence_id, check_preceding):
        siblings = element.xpath('ancestor::s//w')
        if check_preceding:
            siblings = siblings[:siblings.index(element)]
            siblings = siblings[::-1]
        else:
            siblings = siblings[siblings.index(element) + 1:]
        return siblings

    def _segment_by_id(self, tree, id):
        if tree not in self._index:
            self._index[tree] = dict()
            for segment in tree.xpath('//s'):
                self._index[tree][segment.get('id')] = segment
        return self._index[tree].get(id)

    def get_line_as_xml(self, tree, segment_number):
        return self._segment_by_id(tree, segment_number)

    def get_line(self, tree, segment_number):
        line = self._segment_by_id(tree, segment_number)
        if line is not None:
            return etree.tostring(line, encoding=str)
        else:
            return None

    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        """
        Returns the translated segment numbers (could be multiple) for a segment number in the original text.

        Alignment lines in the OPUS corpora look like this:
            <linkGrp targType="s" fromDoc="en/ep-00-01-17.xml.gz" toDoc="nl/ep-00-01-17.xml.gz">
                <link xtargets="1;1" />
                <link xtargets="2;2 3" />
                <link xtargets="3;4 5" />
            </linkGrp>

        To get from language A to B, we should order the languages.

        This function supports n-to-n alignments, as it will return both the source and translated lines as a list.
        """
        from_lines = []
        to_lines = []
        certainty = None

        sl = sorted([language_from, language_to])
        for alignment in alignment_trees[language_to]:
            if sl[0] == language_from:
                if segment_number in alignment.sources:
                    from_lines = alignment.sources
                    to_lines = alignment.targets
                    certainty = alignment.certainty
                    break
            else:
                if segment_number in alignment.targets:
                    from_lines = alignment.targets
                    to_lines = alignment.sources
                    certainty = alignment.certainty
                    break

        if not any(to_lines):
            to_lines = []

        alignment_str = '{} => {}'.format(len(from_lines), len(to_lines)) if to_lines else ''

        return from_lines, to_lines, alignment_str

    def parse_alignment_trees(self, filename, include_translations=True):
        data_folder = os.path.dirname(os.path.dirname(filename))

        # Cache the alignment XMLs on the first run
        if not self.alignment_xmls:
            for language_to in self.l_to:
                sl = sorted([self.l_from, language_to])
                alignment_file = os.path.join(data_folder, '-'.join(sl) + '.xml')
                if os.path.isfile(alignment_file):
                    alignment_tree = etree.parse(alignment_file)
                    self.alignment_xmls[language_to] = alignment_tree
                elif include_translations:
                    click.echo('No alignment file found for {} to {}'.format(filename, language_to))

        alignment_trees = dict()
        translation_trees = dict()
        for language_to in self.alignment_xmls.keys():
            sl = sorted([self.l_from, language_to])
            alignment_tree = self.alignment_xmls[language_to]
            base_filename = os.path.basename(filename)
            doc = '{}/{}'.format(self.l_from, base_filename)
            doc_gz = doc + '.gz'  # OPUS uses .gz natively, deal with both options
            path = '@fromDoc="{}"' if sl[0] == self.l_from else '@toDoc="{}"'
            linkGrps = alignment_tree.xpath('//linkGrp[{} or {}]'.format(path.format(doc), path.format(doc_gz)))

            if not linkGrps:
                if include_translations:
                    click.echo('No translation found for {} to {}'.format(filename, language_to))
            elif len(linkGrps) == 1:
                linkGrp = linkGrps[0]

                if include_translations:
                    translation_link = linkGrp.get('toDoc') if sl[0] == self.l_from else linkGrp.get('fromDoc')
                    if translation_link.endswith('.gz'):   # See comment above: OPUS uses .gz as extension
                        translation_link = translation_link[:-3]
                    translation_file = os.path.join(data_folder, translation_link)
                    translation_trees[language_to] = etree.parse(translation_file)

                alignments = []
                for link in linkGrp.xpath('./link'):
                    xtargets = link.get('xtargets').split(';')
                    sources = xtargets[0].split(' ')
                    targets = xtargets[1].split(' ')
                    certainty = link.get('certainty', None)
                    alignments.append(Alignment(sources, targets, certainty))

                alignment_trees[language_to] = alignments
            else:
                click.echo('Multiple translations found for {} to {}'.format(filename, language_to))

        return alignment_trees, translation_trees

    def average_alignment_certainty(self, alignment_trees):
        certainties_sum = 0
        certainties_len = 0
        for language, alignments in alignment_trees.items():
            certainties = [float(a.certainty) if a.certainty else 0 for a in alignments]
            certainties_sum += sum(certainties)
            certainties_len += len(certainties)

        return certainties_sum / float(certainties_len) if certainties_len > 0 else 0

    def sort_by_alignment_certainty(self, file_names):
        certainties = dict()
        for file_name in file_names:
            alignment_trees, _ = self.parse_alignment_trees(file_name, include_translations=False)
            if len(alignment_trees) == len(self.l_to):  # Only add files that have translations in all languages
                certainties[file_name] = self.average_alignment_certainty(alignment_trees)

        sorted_by_value = sorted(certainties.items(), key=lambda kv: kv[1], reverse=True)
        return [f[0] for f in sorted_by_value]

    def filter_by_file_size(self, file_names):
        results = []
        for file_name in file_names:
            file_size = etree.parse(file_name).xpath('count(//s)')
            if self.min_file_size <= file_size <= self.max_file_size:
                results.append(file_name)

        return results

    def list_directories(self, path):
        return filter(lambda x: x.endswith(self.l_from), super().list_directories(path))
