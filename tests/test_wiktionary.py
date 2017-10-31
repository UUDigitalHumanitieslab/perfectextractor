# -*- coding: utf-8 -*-

import unittest

from apps.extractor.wiktionary import get_translations


class TestWiktionary(unittest.TestCase):
    def test_translations(self):
        self.assertIn('prove', get_translations('aantonen', 'nl', 'en'))
        self.assertIn('blijken', get_translations('prove', 'en', 'nl'))
        self.assertIn('arriver', get_translations('arriveren', 'nl', 'fr'))
