# -*- encoding: utf-8 -*-

import os

from lxml import etree

from perfectextractor.apps.extractor.base import BaseExtractor
from perfectextractor.apps.extractor.utils import XML
from .base import BaseBNC


class BNCExtractor(BaseBNC, BaseExtractor):
    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        # TODO: implement
        raise NotImplementedError

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

    def parse_alignment_trees(self, filename):
        # Not implemented as the BNC is a monolingual corpus.
        return None, None

    def sort_by_alignment_certainty(self, file_names):
        # Not implemented as the BNC is a monolingual corpus.
        raise NotImplementedError

    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        # Not implemented as the BNC is a monolingual corpus.
        raise NotImplementedError

    def filter_by_file_size(self, file_names):
        # TODO: implement
        raise NotImplementedError

    def get_type(self, sentence, mwe=None):
        # TODO: implement
        raise NotImplementedError

    def mark_sentence(self, sentence, match=None):
        # TODO: implement
        raise NotImplementedError
