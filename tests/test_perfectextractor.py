# -*- coding: utf-8 -*-

import unittest

from lxml import etree

from extractor.perfectextractor import PerfectExtractor
from extractor.presentperfect import PresentPerfect


class TestPerfectExtractor(unittest.TestCase):
    def setUp(self):
        self.en_extractor = PerfectExtractor('en', ['nl', 'fr'])
        self.document = 'data/dpc-bmm-001071-'

    def test_init(self):
        self.assertEqual(self.en_extractor.config.get('en', 'perfect_tag'), 'VBN')
        self.assertIn('devenir', self.en_extractor.aux_be_list['fr'])

    def test_get_translated_lines(self):
        lines = self.en_extractor.get_translated_lines(self.document, 'en', 'nl', 'p1.s3')
        self.assertEqual(lines, set(['p1.s3']))
        lines = self.en_extractor.get_translated_lines(self.document, 'nl', 'en', 'p1.s3')
        self.assertEqual(lines, set(['p1.s3', 'p1.s4']))
        lines = self.en_extractor.get_translated_lines(self.document, 'fr', 'nl', 'p1.s13')
        self.assertEqual(lines, set(['p1.s12']))
        lines = self.en_extractor.get_translated_lines(self.document, 'nl', 'fr', 'p1.s13')
        self.assertEqual(lines, set(['p1.s14']))
        lines = self.en_extractor.get_translated_lines(self.document, 'en', 'fr', 'p1.s16')
        self.assertEqual(lines, set(['p1.s16']))
        lines = self.en_extractor.get_translated_lines(self.document, 'fr', 'en', 'p1.s4')
        self.assertEqual(lines, set(['p1.s3', 'p1.s4']))

    def test_get_line_by_number(self):
        tree = etree.parse(self.document + 'en-tei.xml')
        line = self.en_extractor.get_line_by_number(tree, 'en', 'p1.s16')
        pp = PresentPerfect('have', 'have')
        pp.add_word('attained', 'attain', True)
        self.assertIn(u'**have attained**', line[0])
        self.assertEqual(str(pp), str(line[1]))

    def test_get_original_language(self):
        orig_lang = self.en_extractor.get_original_language(self.document)
        self.assertEqual(orig_lang, 'unknown')

    def test_is_lexically_bound(self):
        mock_aux_verb = {'lemma': 'zijn'}
        mock_perfect = {'lemma': 'botsen'}
        self.assertTrue(self.en_extractor.is_lexically_bound('nl', mock_aux_verb, mock_perfect))

        mock_aux_verb = {'lemma': 'zijn'}
        mock_perfect = {'lemma': 'hebben'}
        self.assertFalse(self.en_extractor.is_lexically_bound('nl', mock_aux_verb, mock_perfect))

        mock_aux_verb = {'lemma': u'être'}
        mock_perfect = {'lemma': 'regarder'}
        self.assertFalse(self.en_extractor.is_lexically_bound('fr', mock_aux_verb, mock_perfect))

        mock_aux_verb = {'lemma': u'être'}
        mock_perfect = {'lemma': 'revenir'}
        self.assertTrue(self.en_extractor.is_lexically_bound('fr', mock_aux_verb, mock_perfect))

        mock_aux_verb = {'lemma': 'have'}
        mock_perfect = {'lemma': 'collided'}
        self.assertTrue(self.en_extractor.is_lexically_bound('en', mock_aux_verb, mock_perfect))

    def test_check_present_perfect(self):
        pass

    def test_find_translated_present_perfects(self):
        pass

    def test_check_translated_pps(self):
        pass

    def test_process_file(self):
        pass
        #print self.en_extractor.process_file('data/dpc-bmm-001071-en-tei.xml')

