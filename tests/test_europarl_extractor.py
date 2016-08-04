# -*- coding: utf-8 -*-

import os
import unittest

from lxml import etree

from extractor.europarl_extractor import EuroparlExtractor


class TestEuroparlExtractor(unittest.TestCase):
    def setUp(self):
        filename = os.path.join(os.path.dirname(__file__), 'data/europarl/nl/ep-00-12-15.xml')

        self.extractor = EuroparlExtractor('nl', ['en'])
        self.tree = etree.parse(filename)
        self.alignmenttrees = self.extractor.parse_alignment_trees(filename)
        self.translationtrees = self.extractor.parse_translation_trees(filename)

    def test_init(self):
        self.assertEqual(self.extractor.config.get('nl', 'perfect_tag'), 'verbpapa')
        self.assertIn('dunken', self.extractor.aux_be_list['nl'])

    def test_get_translated_lines(self):
        from_lines, to_lines, alignment = self.extractor.get_translated_lines(self.alignmenttrees, 'nl', 'en', '17')
        self.assertEqual(from_lines, ['17'])
        self.assertEqual(to_lines, ['11'])
        self.assertEqual(alignment, '1 => 1')

        from_lines, to_lines, alignment = self.extractor.get_translated_lines(self.alignmenttrees, 'nl', 'en', '18')
        self.assertEqual(from_lines, ['18', '19'])
        self.assertEqual(to_lines, ['12'])
        self.assertEqual(alignment, '2 => 1')

        from_lines, to_lines, alignment = self.extractor.get_translated_lines(self.alignmenttrees, 'nl', 'en', '57')
        self.assertEqual(from_lines, ['57'])
        self.assertEqual(to_lines, ['46', '47'])
        self.assertEqual(alignment, '1 => 2')

    def test_get_line_by_number(self):
        xml_sentence, full_sentence, pp = self.extractor.get_line_by_number(self.tree, 'nl', '4')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '4')
        self.assertEqual(pp.verbs(), ['is', 'aangebroken'])
        self.assertEqual(pp.words_between(), 9)

        xml_sentence, full_sentence, pp = self.extractor.get_line_by_number(self.translationtrees['en'], 'en', '6')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '6')
        self.assertEqual(pp.verbs(), ['has', 'said'])
        self.assertEqual(pp.words_between(), 1)
