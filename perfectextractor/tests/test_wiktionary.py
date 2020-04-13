# -*- coding: utf-8 -*-

import unittest

from requests.exceptions import ConnectionError

from perfectextractor.apps.extractor.wiktionary import get_translations


class TestWiktionary(unittest.TestCase):
    def test_translations(self):
        try:
            self.assertIn('prove', get_translations('aantonen', 'nl', 'en'))
            self.assertIn('blijken', get_translations('prove', 'en', 'nl'))
            self.assertIn('arriver', get_translations('arriveren', 'nl', 'fr'))
        except ConnectionError as e:
            # No connection available, skipping tests
            pass
