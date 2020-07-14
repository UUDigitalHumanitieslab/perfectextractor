import unittest

from perfectextractor.apps.extractor.models import Perfect

XML_ID = 'test_id'


class TestPerfect(unittest.TestCase):
    def setUp(self):
        self.pp = Perfect('has', 'have', XML_ID)
        self.pp.add_word('always', 'always', False, XML_ID)
        self.pp.add_word('loved', 'love', True, XML_ID)

    def test_extractions(self):
        self.assertEqual(self.pp.perfect_lemma(), 'love')
        self.assertEqual(self.pp.verbs(), ['has', 'loved'])
        self.assertEqual(self.pp.verbs_to_string(), 'has loved')
        self.assertEqual(self.pp.words_between(), 1)

    def test_extend(self):
        ppp = Perfect('has', 'have', XML_ID)
        ppp.add_word('been', 'be', True, XML_ID)
        pp_extend = Perfect('been', 'be', XML_ID)
        pp_extend.add_word('created', 'create', True, XML_ID)
        ppp.extend(pp_extend)

        self.assertEqual(ppp.perfect_lemma(), 'create')
        self.assertEqual(ppp.verbs(), ['has', 'been', 'created'])
        self.assertEqual(ppp.verbs_to_string(), 'has been created')
        self.assertEqual(ppp.words_between(), 0)
