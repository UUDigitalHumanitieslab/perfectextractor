# -*- coding: utf-8 -*-

import os
import unittest

from lxml import etree

from perfectextractor.apps.extractor.models import Perfect
from perfectextractor.corpora.dpc.extractor import DPCPerfectExtractor

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data/dpc')


class TestDPCExtractor(unittest.TestCase):
    def setUp(self):
        self.en_extractor = DPCPerfectExtractor('en', ['nl', 'fr'], search_in_to=True)
        self.nl_extractor = DPCPerfectExtractor('nl', ['en', 'fr'], search_in_to=True)
        self.fr_extractor = DPCPerfectExtractor('fr', ['en', 'nl'], search_in_to=True)

        self.document = os.path.join(DATA_FOLDER, 'dpc-bmm-001071-')
        align_fr = etree.parse(os.path.join(DATA_FOLDER, 'dpc-bmm-001071-nl-fr-tei.xml'))
        align_en = etree.parse(os.path.join(DATA_FOLDER, 'dpc-bmm-001071-nl-en-tei.xml'))
        self.alignmenttrees = {'en': align_en, 'fr': align_fr}

    def test_init(self):
        self.assertEqual(self.en_extractor.config.get('en', 'perfect_tags'), 'VBN')
        self.assertIn('devenir', self.en_extractor.aux_be_list['fr'])

    def test_get_translated_lines(self):
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'en', 'nl', 'p1.s3')
        self.assertEqual(lines, set(['p1.s3']))
        self.assertEqual(alignment, '2=>1')
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'nl', 'en', 'p1.s3')
        self.assertEqual(lines, set(['p1.s3', 'p1.s4']))
        self.assertEqual(alignment, '1=>2')
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'fr', 'nl', 'p1.s13')
        self.assertEqual(lines, set(['p1.s12']))
        self.assertEqual(alignment, '1=>1')
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'nl', 'fr', 'p1.s13')
        self.assertEqual(lines, set(['p1.s14']))
        self.assertEqual(alignment, '2=>1')
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'en', 'fr', 'p1.s16')
        self.assertEqual(lines, set(['p1.s16']))
        self.assertEqual(alignment, '1=>1')
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'fr', 'en', 'p1.s4')
        self.assertEqual(lines, set(['p1.s3', 'p1.s4']))
        self.assertEqual(alignment, '2=>2')

    def test_get_line_by_number(self):
        tree = etree.parse(self.document + 'en-tei.xml')
        line = self.en_extractor.get_line_and_pp(tree, 'en', 'p1.s16')
        pp = Perfect('have', 'have', 'test_id')
        pp.add_word('attained', 'attain', True, 'test_id')
        # self.assertIn(u'**have attained**', line[0])
        self.assertEqual(pp.verbs_to_string(), line[1].verbs_to_string())

    def test_get_original_language(self):
        orig_lang = self.en_extractor.get_original_language(self.document)
        self.assertEqual(orig_lang, 'unknown')

    def test_check_present_perfect(self):
        pass

    def test_find_translated_present_perfects(self):
        pass

    def test_check_translated_pps(self):
        pass

    def test_process_file(self):
        pass
        #print self.en_extractor.process_file('data/dpc-bmm-001071-en-tei.xml')
