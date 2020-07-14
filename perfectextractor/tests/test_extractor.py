# -*- coding: utf-8 -*-

import unittest

from lxml import etree

from perfectextractor.apps.extractor.models import Perfect
from perfectextractor.corpora.europarl.extractor import EuroparlPerfectExtractor


class TestPerfectExtractor(unittest.TestCase):
    def test_is_lexically_bound(self):
        extractor = EuroparlPerfectExtractor('en', ['de', 'es', 'fr', 'nl'], search_in_to=True)
        lemma_attr = extractor.config.get('all', 'lemma_attr')
        mock_pp = Perfect('is', 'be', 'w1.1.1')

        # Default case: English (no lexical bounds)
        mock_aux_verb = {lemma_attr: 'have'}
        mock_participle = {lemma_attr: 'collided'}
        self.assertTrue(extractor.is_lexically_bound('en', mock_pp, mock_aux_verb, mock_participle))

        # Checking Dutch (ik ben gebotst vs. *ik ben gehad)
        mock_aux_verb = {lemma_attr: 'zijn'}
        mock_participle = {lemma_attr: 'botsen'}
        self.assertTrue(extractor.is_lexically_bound('nl', mock_pp, mock_aux_verb, mock_participle))

        mock_aux_verb = {lemma_attr: 'zijn'}
        mock_participle = {lemma_attr: 'hebben'}
        self.assertFalse(extractor.is_lexically_bound('nl', mock_pp, mock_aux_verb, mock_participle))

        # Checking French (*je suis regardé vs. je suis revenu)
        mock_aux_verb = {lemma_attr: u'être'}
        mock_participle = {lemma_attr: 'regarder'}
        self.assertFalse(extractor.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle))

        mock_aux_verb = {lemma_attr: u'être'}
        mock_participle = {lemma_attr: 'revenir'}
        self.assertTrue(extractor.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle))

        # Checking reflexive passé composés (je me suis couché)
        mock_pp = Perfect('suis', u'être', 'w1.1.1')
        mock_aux_verb = {lemma_attr: u'être'}
        mock_participle = {lemma_attr: 'coucher'}
        self.assertFalse(extractor.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle))

        mock_sentence = etree.Element('s')
        me = etree.SubElement(mock_sentence, 'w')
        me.text = 'me'
        me.set(lemma_attr, 'me')
        me.set('pos', 'PRO:PER')
        je = etree.SubElement(mock_sentence, 'w')
        je.text = 'je'
        je.set(lemma_attr, 'je')
        je.set('pos', 'PRO:PER')

        self.assertTrue(extractor.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle, mock_sentence))
        self.assertEqual(len(mock_pp.words), 2)
        self.assertEqual(mock_pp.verbs_to_string(), 'me suis')
        self.assertTrue(mock_pp.is_reflexive)

        # Checking reflexive passé composés (puis nous sommes restés)
        mock_pp = Perfect('sommes', u'être', 'w1.1.1')
        mock_aux_verb = {lemma_attr: u'être'}
        mock_participle = {lemma_attr: 'rester'}
        self.assertTrue(extractor.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle))

        mock_sentence = etree.Element('s')
        nous = etree.SubElement(mock_sentence, 'w')
        nous.text = 'nous'
        nous.set(lemma_attr, 'nous')
        nous.set('pos', 'PRO:PER')
        puis = etree.SubElement(mock_sentence, 'w')
        puis.text = 'puis'
        puis.set(lemma_attr, 'puis')
        puis.set('pos', 'ADV')

        # This should be lexically bound, but 'nous' should not be part of the passé composé
        self.assertTrue(extractor.is_lexically_bound('fr', mock_pp, mock_aux_verb, mock_participle, mock_sentence))
        self.assertEqual(mock_pp.verbs_to_string(), 'sommes')
        self.assertEqual(len(mock_pp.words), 1)
        self.assertFalse(mock_pp.is_reflexive)
