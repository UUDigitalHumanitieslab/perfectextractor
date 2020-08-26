# -*- coding: utf-8 -*-

import os
import unittest

from lxml import etree

from perfectextractor.apps.extractor.models import Perfect
from perfectextractor.corpora.dpc.perfect import DPCPerfectExtractor
from perfectextractor.corpora.dpc.pos import DPCPoSExtractor

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

    def merge_results(self, generator):
        return sum(list(generator), [])

    def test_init(self):
        self.assertEqual(self.en_extractor.config.get('en', 'perfect_tags'), 'VBN')
        self.assertIn('devenir', self.en_extractor.aux_be_list['fr'])

    def test_get_translated_lines(self):
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'en', 'nl', 'p1.s3')
        self.assertEqual(lines, {'p1.s3'})
        self.assertEqual(alignment, '2=>1')
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'nl', 'en', 'p1.s3')
        self.assertEqual(lines, {'p1.s3', 'p1.s4'})
        self.assertEqual(alignment, '1=>2')
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'fr', 'nl', 'p1.s13')
        self.assertEqual(lines, {'p1.s12'})
        self.assertEqual(alignment, '1=>1')
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'nl', 'fr', 'p1.s13')
        self.assertEqual(lines, {'p1.s14'})
        self.assertEqual(alignment, '2=>1')
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'en', 'fr', 'p1.s16')
        self.assertEqual(lines, {'p1.s16'})
        self.assertEqual(alignment, '1=>1')
        lines, alignment = self.en_extractor.get_translated_lines(self.alignmenttrees, 'fr', 'en', 'p1.s4')
        self.assertEqual(lines, {'p1.s3', 'p1.s4'})
        self.assertEqual(alignment, '2=>2')

    def test_get_line_by_number(self):
        tree = etree.parse(self.document + 'en-tei.xml')
        line = self.en_extractor.get_line_and_pp(tree, 'en', 'p1.s16')
        mock_s = etree.Element('s')
        pp = Perfect(mock_s)
        pp.add_word('have', 'have', 'VERB', 'test_id')
        pp.add_word('attained', 'attain', 'VERB', 'test_id')
        # self.assertIn(u'**have attained**', line[0])
        self.assertEqual(pp.construction_to_string(), line[2].construction_to_string())

    def test_get_original_language(self):
        orig_lang = self.en_extractor.get_original_language(self.document)
        self.assertEqual(orig_lang, 'unknown')

    def test_en_extractor(self):
        results = self.merge_results(self.en_extractor.generate_results(os.path.join(DATA_FOLDER)))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][2], u'present perfect')
        self.assertEqual(results[0][3], u'have attained')
        self.assertEqual(results[1][3], u'have been provided')

    def test_fr_extractor(self):
        results = self.merge_results(self.fr_extractor.generate_results(os.path.join(DATA_FOLDER)))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][3], u'avez dit')
        self.assertEqual(results[1][3], u'ont atteint')

    def test_nl_extractor(self):
        results = self.merge_results(self.nl_extractor.generate_results(os.path.join(DATA_FOLDER)))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][3], u'zijn verbonden')
        self.assertEqual(results[1][3], u'hebben bereikt')

    def test_sentence_filtering(self):
        extractor = DPCPerfectExtractor('fr', ['nl'], sentence_ids=['p1.s3'])
        results = self.merge_results(extractor.generate_results(os.path.join(DATA_FOLDER)))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][3], u'avez dit')

    def test_pos_extractor(self):
        extractor = DPCPoSExtractor('en', ['nl'], pos=['JJ'])
        results = self.merge_results(extractor.generate_results(os.path.join(DATA_FOLDER)))
        self.assertEqual(len(results), 41)

        extractor = DPCPoSExtractor('en', ['nl'], pos=['JJ'], regex=['cal$'])
        results = self.merge_results(extractor.generate_results(os.path.join(DATA_FOLDER)))
        self.assertEqual(len(results), 14)
