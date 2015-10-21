import unittest

from presentperfect import PresentPerfect


class TestPresentPerfect(unittest.TestCase):
    def setUp(self):
        self.pp = PresentPerfect('has', 'have')
        self.pp.add_word('always', 'always', False)
        self.pp.add_word('loved', 'love', True)

    def test_extractions(self):
        self.assertEqual(self.pp.perfect_lemma(), 'love')
        self.assertEqual(self.pp.verbs(), ['has', 'loved'])
        self.assertEqual(self.pp.verbs_to_string(), 'has loved')
        self.assertEqual(self.pp.words_between(), 1)

    def test_extend(self):
        ppc = PresentPerfect('has', 'have')
        ppc.add_word('been', 'be', True)
        pp_extend = PresentPerfect('been', 'be')
        pp_extend.add_word('created', 'create', True)
        ppc.extend(pp_extend)

        self.assertEqual(ppc.perfect_lemma(), 'create')
        self.assertEqual(ppc.verbs(), ['has', 'been', 'created'])
        self.assertEqual(ppc.verbs_to_string(), 'has been created')
        self.assertEqual(ppc.words_between(), 0)

    def test_mark_sentence(self):
        marked = self.pp.mark_sentence('She has always loved him.')
        self.assertEqual(marked, u'She **has** always **loved** him.')
        marked = self.pp.mark_sentence('She has always hated him.')
        self.assertEqual(marked, u'She has always hated him.')
