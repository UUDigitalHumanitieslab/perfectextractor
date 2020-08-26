# -*- coding: utf-8 -*-

import unittest

from lxml import etree

from perfectextractor.apps.extractor.models import Perfect
from perfectextractor.corpora.opus.perfect import OPUSPerfectExtractor


class TestPerfectExtractor(unittest.TestCase):
    def test_is_lexically_bound(self):
        en_ex = OPUSPerfectExtractor('en', ['de', 'es', 'fr', 'nl'])
        nl_ex = OPUSPerfectExtractor('nl', ['de', 'es', 'en', 'fr'])
        fr_ex = OPUSPerfectExtractor('fr', ['de', 'es', 'en', 'nl'])
        lemma_attr = en_ex.config.get('all', 'lemma_attr')
        mock_s = etree.Element('s')
        mock_pp = Perfect(mock_s)
        mock_pp.add_word('is', 'be', 'VERB', 'w1.1.1')

        mock_before1 = etree.Element('w')
        mock_before2 = etree.Element('w')
        mock_before = [mock_before1, mock_before2]

        # Default case: English (no lexical bounds)
        mock_aux_verb = etree.Element('w')
        mock_aux_verb.set(lemma_attr, 'have')
        mock_participle = etree.Element('w')
        mock_participle.set(lemma_attr, 'collided')
        self.assertTrue(en_ex.is_lexically_bound('en', mock_pp, mock_aux_verb, mock_participle, mock_before))

        # Checking Dutch (ik ben gebotst vs. *ik ben gehad)
        mock_aux_verb = etree.Element('w')
        mock_aux_verb.set(lemma_attr, 'zijn')
        mock_participle = etree.Element('w')
        mock_participle.set(lemma_attr, 'botsen')
        self.assertTrue(nl_ex.is_lexically_bound('nl', mock_pp, mock_aux_verb, mock_participle, mock_before))

        mock_aux_verb = etree.Element('w')
        mock_aux_verb.set(lemma_attr, 'zijn')
        mock_participle = etree.Element('w')
        mock_participle.set(lemma_attr, 'hebben')
        self.assertFalse(nl_ex.is_lexically_bound('nl', mock_pp, mock_aux_verb, mock_participle, mock_before))

        # Checking French (*je suis regardé vs. je suis revenu)
        mock_aux_verb = etree.Element('w')
        mock_aux_verb.set(lemma_attr, 'être')
        mock_participle = etree.Element('w')
        mock_participle.set(lemma_attr, 'regarder')
        self.assertFalse(fr_ex.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle, mock_before))

        mock_aux_verb = etree.Element('w')
        mock_aux_verb.set(lemma_attr, 'être')
        mock_participle = etree.Element('w')
        mock_participle.set(lemma_attr, 'revenir')
        self.assertTrue(fr_ex.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle, mock_before))

        # Checking reflexive passé composés (je me suis couché)
        mock_pp = Perfect(mock_s)
        mock_pp.add_word('suis', u'être', 'VERB', 'w1.1.1')
        mock_aux_verb = etree.Element('w')
        mock_aux_verb.set(lemma_attr, 'être')
        mock_participle = etree.Element('w')
        mock_participle.set(lemma_attr, 'coucher')
        self.assertFalse(fr_ex.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle, mock_before))

        mock_sentence = etree.Element('s')
        me = etree.SubElement(mock_sentence, 'w')
        me.text = 'me'
        me.set(lemma_attr, 'me')
        me.set('pos', 'PRO:PER')
        je = etree.SubElement(mock_sentence, 'w')
        je.text = 'je'
        je.set(lemma_attr, 'je')
        je.set('pos', 'PRO:PER')
        me_je = [me, je]

        self.assertTrue(fr_ex.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle, me_je))
        self.assertEqual(len(mock_pp.words), 2)
        self.assertEqual(mock_pp.construction_to_string(), 'me suis')
        self.assertTrue(mock_pp.is_reflexive)

        # Checking reflexive passé composés (puis nous sommes restés)
        mock_pp = Perfect(mock_s)
        mock_pp.add_word('sommes', u'être', 'VERB', 'w1.1.1')
        mock_aux_verb = etree.Element('w')
        mock_aux_verb.set(lemma_attr, 'être')
        mock_participle = etree.Element('w')
        mock_participle.set(lemma_attr, 'rester')
        self.assertTrue(fr_ex.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle, mock_before))

        mock_sentence = etree.Element('s')
        nous = etree.SubElement(mock_sentence, 'w')
        nous.text = 'nous'
        nous.set(lemma_attr, 'nous')
        nous.set('pos', 'PRO:PER')
        puis = etree.SubElement(mock_sentence, 'w')
        puis.text = 'puis'
        puis.set(lemma_attr, 'puis')
        puis.set('pos', 'ADV')
        nous_puis = [nous, puis]

        # This should be lexically bound, but 'nous' should not be part of the passé composé
        self.assertTrue(fr_ex.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle, nous_puis))
        self.assertEqual(mock_pp.construction_to_string(), 'sommes')
        self.assertEqual(len(mock_pp.words), 1)
        self.assertFalse(mock_pp.is_reflexive)
