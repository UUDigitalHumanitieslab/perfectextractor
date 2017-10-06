from abc import ABCMeta, abstractmethod
import ConfigParser
import codecs

from .base import BaseExtractor
from .models import MultiWordExpression


class RecentPastExtractor(BaseExtractor):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to=[]):
        """
        Initializes the extractor for the given source and target language(s).
        Reads in the config for the source language,
        as well as the list of verbs that use 'to be' as auxiliary verb for both source and target language(s).
        :param language_from: the source language
        :param languages_to: the target language(s)
        """
        self.l_from = language_from
        self.l_to = languages_to

        # Read the config
        config = ConfigParser.RawConfigParser()
        config.readfp(codecs.open(self.get_config(), 'r', 'utf8'))
        self.config = config

    def check_recent_past(self, w):
        is_recent_past = False

        lemma_attr = self.config.get('all', 'lemma_attr')
        pos_attr = self.config.get(self.l_from, 'pos')
        rp_pre_pos = self.config.get(self.l_from, 'rp_pre_pos').split(',')
        rp_pre_lem = self.config.get(self.l_from, 'rp_pre_lem')
        rp_inf_pos = self.config.get(self.l_from, 'rp_inf_pos')

        sentence = self.get_sentence(w)

        mwe = MultiWordExpression(sentence)
        mwe.add_word(w.text, w.get(lemma_attr), True, w.get('id'))
        w_next = w.getnext()
        if w_next.get(pos_attr) in rp_pre_pos and w_next.get(lemma_attr) == rp_pre_lem:
            mwe.add_word(w_next.text, w_next.get(lemma_attr), True, w_next.get('id'))
            for s in self.get_siblings(w_next, sentence.get('id'), False):
                if s.get(pos_attr) == rp_inf_pos:
                    is_recent_past = True
                    mwe.add_word(s.text, s.get(lemma_attr), True, s.get('id'))
                    break
                else:
                    mwe.add_word(s.text, s.get(lemma_attr), False, s.get('id'))

        return mwe if is_recent_past else None
