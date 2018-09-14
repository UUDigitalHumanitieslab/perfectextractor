# -*- coding: utf-8 -*-

import unittest

from corpora.europarl.extractor import EuroparlPerfectExtractor


class TestPerfectExtractor(unittest.TestCase):
    def test_is_lexically_bound(self):
        extractor = EuroparlPerfectExtractor('en', ['de', 'es', 'fr', 'nl'], search_in_to=True)
        lemma_attr = extractor.config.get('all', 'lemma_attr')
        
        mock_aux_verb = {lemma_attr: 'zijn'}
        mock_perfect = {lemma_attr: 'botsen'}
        self.assertTrue(extractor.is_lexically_bound('nl', mock_aux_verb, mock_perfect))

        mock_aux_verb = {lemma_attr: 'zijn'}
        mock_perfect = {lemma_attr: 'hebben'}
        self.assertFalse(extractor.is_lexically_bound('nl', mock_aux_verb, mock_perfect))

        mock_aux_verb = {lemma_attr: u'être'}
        mock_perfect = {lemma_attr: 'regarder'}
        self.assertFalse(extractor.is_lexically_bound('fr', mock_aux_verb, mock_perfect))

        mock_aux_verb = {lemma_attr: u'être'}
        mock_perfect = {lemma_attr: 'revenir'}
        self.assertTrue(extractor.is_lexically_bound('fr', mock_aux_verb, mock_perfect))

        mock_aux_verb = {lemma_attr: 'have'}
        mock_perfect = {lemma_attr: 'collided'}
        self.assertTrue(extractor.is_lexically_bound('en', mock_aux_verb, mock_perfect))
