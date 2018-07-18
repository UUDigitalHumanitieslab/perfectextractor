# -*- coding: utf-8 -*-

import os
import unittest

from lxml import etree

from corpora.europarl.extractor import EuroparlPerfectExtractor, EuroParlRecentPastExtractor, EuroParlPoSExtractor

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data/europarl')


class TestEuroparlPerfectExtractor(unittest.TestCase):
    def setUp(self):
        self.nl_filename = os.path.join(DATA_FOLDER, 'nl/ep-00-12-15.xml')
        self.en_filename = os.path.join(DATA_FOLDER, 'en/ep-00-12-15.xml')
        self.fr_filename = os.path.join(DATA_FOLDER, 'fr/ep-00-12-15.xml')

        self.nl_extractor = EuroparlPerfectExtractor('nl', ['en'])
        self.nl_tree = etree.parse(self.nl_filename)
        self.nl_alignmenttrees, self.nl_translationtrees = self.nl_extractor.parse_alignment_trees(self.nl_filename)

        self.en_extractor = EuroparlPerfectExtractor('en', ['nl'])
        self.en_tree = etree.parse(self.en_filename)
        self.en_alignmenttrees, self.en_translationtrees = self.en_extractor.parse_alignment_trees(self.en_filename)

    def test_init(self):
        self.assertEqual(self.nl_extractor.config.get('nl', 'perfect_tags'), 'verbpapa')
        self.assertIn('dunken', self.nl_extractor.aux_be_list['nl'])

    def test_get_translated_lines(self):
        from_lines, to_lines, align = self.nl_extractor.get_translated_lines(self.nl_alignmenttrees, 'nl', 'en', '17')
        self.assertEqual(from_lines, ['17'])
        self.assertEqual(to_lines, ['11'])
        self.assertEqual(align, '1 => 1')

        from_lines, to_lines, align = self.nl_extractor.get_translated_lines(self.nl_alignmenttrees, 'nl', 'en', '18')
        self.assertEqual(from_lines, ['18', '19'])
        self.assertEqual(to_lines, ['12'])
        self.assertEqual(align, '2 => 1')

        from_lines, to_lines, align = self.nl_extractor.get_translated_lines(self.nl_alignmenttrees, 'nl', 'en', '57')
        self.assertEqual(from_lines, ['57'])
        self.assertEqual(to_lines, ['46', '47'])
        self.assertEqual(align, '1 => 2')

        from_lines, to_lines, align = self.nl_extractor.get_translated_lines(self.nl_alignmenttrees, 'nl', 'en', '9')
        self.assertEqual(from_lines, ['9'])
        self.assertEqual(to_lines, [])
        self.assertEqual(align, '')

        from_lines, to_lines, align = self.en_extractor.get_translated_lines(self.en_alignmenttrees, 'en', 'nl', '19')
        self.assertEqual(from_lines, ['19'])
        self.assertEqual(to_lines, ['27'])
        self.assertEqual(align, '1 => 1')

        from_lines, to_lines, align = self.en_extractor.get_translated_lines(self.en_alignmenttrees, 'en', 'nl', '8')
        self.assertEqual(from_lines, ['8'])
        self.assertEqual(to_lines, ['13', '14'])
        self.assertEqual(align, '1 => 2')

        from_lines, to_lines, align = self.en_extractor.get_translated_lines(self.en_alignmenttrees, 'en', 'nl', '234')
        self.assertEqual(from_lines, ['234', '235'])
        self.assertEqual(to_lines, ['290'])
        self.assertEqual(align, '2 => 1')

    def test_get_line_by_number(self):
        xml_sentence, _, pp = self.nl_extractor.get_line_by_number(self.nl_tree, 'nl', '4')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '4')
        self.assertEqual(pp.get_sentence_id(), '4')
        self.assertEqual(pp.verbs(), ['is', 'aangebroken'])
        self.assertEqual(pp.verb_ids(), 'w4.9 w4.19')
        self.assertEqual(pp.words_between(), 9)
        self.assertFalse(pp.is_passive)
        self.assertFalse(pp.is_continuous)

        xml_sentence, _, pp = self.nl_extractor.get_line_by_number(self.nl_tree, 'nl', '15')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '15')
        self.assertEqual(pp.verbs(), ['heeft', 'bemoeid'])
        self.assertEqual(pp.words_between(), 0)
        self.assertFalse(pp.is_passive)
        self.assertFalse(pp.is_continuous)

        xml_sentence, _, pp = self.nl_extractor.get_line_by_number(self.nl_translationtrees['en'], 'en', '6')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '6')
        self.assertEqual(pp.verbs(), ['has', 'said'])
        self.assertEqual(pp.words_between(), 1)
        self.assertFalse(pp.is_passive)
        self.assertFalse(pp.is_continuous)

        xml_sentence, _, pp = self.en_extractor.get_line_by_number(self.en_tree, 'en', '89')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '89')
        self.assertEqual(pp.verbs(), ['has', 'been', 'mentioned'])
        self.assertEqual(pp.words_between(), 1)
        self.assertTrue(pp.is_passive)
        self.assertFalse(pp.is_continuous)

        xml_sentence, _, pp = self.en_extractor.get_line_by_number(self.en_tree, 'en', '121')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '121')
        self.assertEqual(pp.verbs(), ['has', 'been', 'carrying'])
        self.assertEqual(pp.words_between(), 0)
        self.assertFalse(pp.is_passive)
        self.assertTrue(pp.is_continuous)

        xml_sentence, _, pp = self.en_extractor.get_line_by_number(self.en_tree, 'en', '180')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '180')
        self.assertEqual(pp.verbs(), ['has', 'brought'])
        self.assertEqual(pp.words_between(), 1)
        self.assertFalse(pp.is_passive)
        self.assertFalse(pp.is_continuous)

    def test_list_filenames(self):
        files = self.nl_extractor.list_filenames(os.path.join(DATA_FOLDER, 'nl'))
        self.assertEqual([os.path.basename(f) for f in files], ['ep-00-12-15.xml'])

    def test_recent_past_extraction(self):
        fr_extractor = EuroParlRecentPastExtractor('fr', ['en', 'nl'])

        results = fr_extractor.process_file(self.fr_filename)
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0][3], u'vient de dire')
        self.assertEqual(results[1][3], u'viens d\' aborder')
        self.assertEqual(results[2][3], u'viens d\' évoquer')
        self.assertEqual(results[3][3], u'vient d\' être dit')

    def test_append_extractor(self):
        perfect_extractor = EuroparlPerfectExtractor('en', ['nl'], search_in_to=False)
        for_extractor = EuroParlPoSExtractor('en', ['nl'], lemmata=['for'])
        year_extractor = EuroParlPoSExtractor('en', ['nl'], lemmata=['year'])

        results = for_extractor.generate_results(os.path.join(DATA_FOLDER, 'en'))
        self.assertEqual(len(results), 177)

        for_extractor.add_extractor(year_extractor)
        results = for_extractor.generate_results(os.path.join(DATA_FOLDER, 'en'))
        self.assertEqual(len(results), 14)

        for_extractor.add_extractor(perfect_extractor)
        results = for_extractor.generate_results(os.path.join(DATA_FOLDER, 'en'))
        self.assertEqual(len(results), 7)
        self.assertEqual(results[0][3], u'has been focused')
