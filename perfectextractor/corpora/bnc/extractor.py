# -*- encoding: utf-8 -*-

import os

from lxml import etree

from perfectextractor.apps.extractor.base import BaseExtractor
from perfectextractor.apps.extractor.utils import XML
from .base import BaseBNC


class BNCExtractor(BaseBNC, BaseExtractor):
    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        raise NotImplementedError

    def parse_alignment_trees(self, filename):
        # The BNC has no alignment trees, as it's a monolingual corpus.
        raise NotImplementedError

    def process_file(self, filename):
        results = []

        # Retrieve the genre
        tree = etree.parse(filename)
        genre = self.get_genre(tree)

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag='s')

        # Find potential Perfects
        for _, s in s_trees:
            if self.sentence_ids and s.get('n') not in self.sentence_ids:
                continue

            result = list()
            result.append(os.path.basename(filename))
            result.append(s.get('n'))
            result.append(genre)
            result.append('')
            result.append('')
            if self.output == XML:
                result.append('<root>' + etree.tostring(s) + '</root>')
            else:
                result.append(self.get_sentence_words(s))

            results.append(result)
        return results

    def get_sentence(self, element):
        return element.xpath('ancestor::s')[0]

    def get_siblings(self, element, sentence_id, check_preceding):
        return element.itersiblings(tag='w', preceding=check_preceding)

    def get_sentence_words(self, sentence):
        """
        Returns all words in the sentence.
        Note that in the BNC, these can be either in w or c tags (the latter are for punctuation)
        :param sentence: the s element
        :return: all w and c texts, joined with a space.
        """
        s = []
        for w in sentence.xpath('.//w | .//c'):
            s.append(w.text.strip() if w.text else ' ')
        return ' '.join(s)

    def sort_by_alignment_certainty(self, file_names):
        raise NotImplementedError

    def filter_by_file_size(self, file_names):
        raise NotImplementedError

    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        raise NotImplementedError
