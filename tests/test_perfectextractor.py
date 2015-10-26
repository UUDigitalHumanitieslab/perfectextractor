
import unittest

from extractor.perfectextractor import PerfectExtractor
from extractor.presentperfect import PresentPerfect


class TestPerfectExtractor(unittest.TestCase):
    def setUp(self):
        self.en_extractor = PerfectExtractor('en', ['nl', 'fr'])

        self.pp = PresentPerfect('has', 'have')
        self.pp.add_word('always', 'always', False)
        self.pp.add_word('loved', 'love', True)

    def test_init(self):
        self.assertIn('devenir', self.en_extractor.aux_be_list['fr'])