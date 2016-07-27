import unittest

from extractor.models import PresentPerfect


class TestPresentPerfect(unittest.TestCase):
    def setUp(self):
        self.pp = PresentPerfect('has', 'have', 'test_id')
        self.pp.add_word('always', 'always', False, 'test_id')
        self.pp.add_word('loved', 'love', True, 'test_id')

    def test_extractions(self):
        self.assertEqual(self.pp.perfect_lemma(), 'love')
        self.assertEqual(self.pp.verbs(), ['has', 'loved'])
        self.assertEqual(self.pp.verbs_to_string(), 'has loved')
        self.assertEqual(self.pp.words_between(), 1)

    def test_extend(self):
        ppc = PresentPerfect('has', 'have', 'test_id')
        ppc.add_word('been', 'be', True, 'test_id')
        pp_extend = PresentPerfect('been', 'be', 'test_id')
        pp_extend.add_word('created', 'create', True, 'test_id')
        ppc.extend(pp_extend)

        self.assertEqual(ppc.perfect_lemma(), 'create')
        self.assertEqual(ppc.verbs(), ['has', 'been', 'created'])
        self.assertEqual(ppc.verbs_to_string(), 'has been created')
        self.assertEqual(ppc.words_between(), 0)
