# -*- coding: utf-8 -*-

import os
import unittest

from corpora.bnc.extractor import BNCPerfectExtractor

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data/bnc')


class TestBNCPerfectExtractor(unittest.TestCase):
    def setUp(self):
        self.language = 'en'
        self.extractor = BNCPerfectExtractor(self.language)

    def test_init(self):
        self.assertEqual(self.extractor.config.get(self.language, 'perfect_tags'), 'VBN,VDN,VHN,VVN')
        self.assertEqual(self.extractor.config.get(self.language, 'pos'), 'c5')

    def test_list_filenames(self):
        filenames = self.extractor.list_filenames(DATA_FOLDER)
        self.assertEqual(os.path.basename(filenames[0]), 'ALP-formatted.xml')

    def test_process(self):
        VERBS_COLUMN = 3

        filename = os.path.join(DATA_FOLDER, 'ALP-formatted.xml')
        results = self.extractor.process_file(filename)
        self.assertEqual(len(results), 60)
        self.assertEqual(results[0][VERBS_COLUMN], 'has been presented')
        self.assertEqual(results[1][VERBS_COLUMN], 'has pointed')
        self.assertEqual(results[2][VERBS_COLUMN], 'has shown')
        self.assertEqual(results[3][VERBS_COLUMN], 'has been running')
        self.assertEqual(results[4][VERBS_COLUMN], 'has devoted')

        # Test whether present perfect continuous are ignored when check_ppc is set to False
        self.extractor.config.set(self.language, 'check_ppc', False)
        results = self.extractor.process_file(filename)
        self.assertEqual(results[3][VERBS_COLUMN], 'has been running')

        # Test whether the lemmata_list will exclude
        self.extractor = BNCPerfectExtractor(self.language, lemmata=['show', 'run'])
        results = self.extractor.process_file(filename)
        self.assertEqual(results[0][VERBS_COLUMN], 'has shown')
        self.assertEqual(results[1][VERBS_COLUMN], 'has been running')
        self.assertEqual(results[2][VERBS_COLUMN], 'has shown')
        self.assertEqual(results[3][VERBS_COLUMN], 'have been shown')
        self.assertEqual(results[4][VERBS_COLUMN], 'has shown')

    def test_not_implemented(self):
        self.assertRaises(NotImplementedError, self.extractor.get_line_by_number, None, None, None)
        self.assertRaises(NotImplementedError, self.extractor.get_translated_lines, None, None, None, None)
