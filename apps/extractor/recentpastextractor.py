from abc import ABCMeta
import ConfigParser
import codecs
import string

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

    def check_recent_past(self, w, language):
        """
        Checks if the element w is the start of a recent past construction
        :param w: the starting element
        :param language: the language
        :return: if found, the recent past construction as a MultiWordExpression, otherwise None
        """
        is_recent_past = False

        # Retrieve the configuration variables
        lemma_attr = self.config.get('all', 'lemma_attr')
        pos_attr = self.config.get(language, 'pos')
        rp_pre_pos = self.config.get(language, 'rp_pre_pos').split(',')
        rp_pre_lem = self.config.get(language, 'rp_pre_lem')
        rp_inf_pos = self.config.get(language, 'rp_inf_pos')
        check_ppp = self.config.get(language, 'ppp')
        ppp_lemma = self.config.get(language, 'ppp_lemma')
        perfect_tags = self.config.get(language, 'perfect_tags').split(',')
        stop_tags = tuple(self.config.get(language, 'stop_tags').split(','))

        sentence = self.get_sentence(w)

        # Start a new MWE at the first word
        mwe = MultiWordExpression(sentence)
        mwe.add_word(w.text, w.get(lemma_attr), True, w.get('id'))

        # Check if the next word is a the preposition of the recent past construction
        w_next = w.getnext()
        if w_next.get(pos_attr) in rp_pre_pos and w_next.get(lemma_attr) == rp_pre_lem:
            mwe.add_word(w_next.text, w_next.get(lemma_attr), True, w_next.get('id'))

            # Now look at the siblings to find an infinitive
            for s in self.get_siblings(w_next, sentence.get('id'), False):
                s_pos = s.get(pos_attr)
                if s_pos == rp_inf_pos:
                    is_recent_past = True
                    mwe.add_word(s.text, s.get(lemma_attr), True, s.get('id'))

                    # If the language has passive recent pasts, check if this is followed by a perfect
                    if check_ppp and s.get(lemma_attr) == ppp_lemma:
                        s_next = s.getnext()
                        if s_next.get(pos_attr) in perfect_tags:
                            mwe.add_word(s_next.text, s_next.get(lemma_attr), True, s_next.get('id'))

                    # Break out of the loop: we found our recent past construction
                    break
                # Stop looking at punctuation or stop tags
                elif (s.text and s.text in string.punctuation) or (s_pos and s_pos.startswith(stop_tags)):
                    break
                # Otherwise: add the word to the MWE
                else:
                    mwe.add_word(s.text, s.get(lemma_attr), False, s.get('id'))

        return mwe if is_recent_past else None
