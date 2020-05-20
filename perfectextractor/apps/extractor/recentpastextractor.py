from abc import ABCMeta
import string

from .base import BaseExtractor
from .models import MultiWordExpression

try:
    import ConfigParser
except ImportError:
    import configparser as ConfigParser


class RecentPastExtractor(BaseExtractor):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to=None, **kwargs):
        """
        Initializes the extractor for the given source and target language(s).
        Reads in the config for the source language.
        :param language_from: the source language
        :param languages_to: the target language(s)
        """
        super(RecentPastExtractor, self).__init__(language_from, languages_to, **kwargs)

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

        # Check the siblings for the preposition of the recent past construction
        for pre in self.get_siblings(w, sentence.get('id'), False):
            pre_pos = pre.get(pos_attr)
            pre_lem = pre.get(lemma_attr)
            if pre_pos in rp_pre_pos and pre_lem == rp_pre_lem:
                mwe.add_word(pre.text, pre_lem, True, pre.get('id'))

                # Now look at the siblings to find an infinitive
                for inf in self.get_siblings(pre, sentence.get('id'), False):
                    inf_pos = inf.get(pos_attr)
                    inf_lem = inf.get(lemma_attr)
                    if inf_pos == rp_inf_pos:
                        is_recent_past = True
                        mwe.add_word(inf.text, inf_lem, True, inf.get('id'))

                        # If the language has passive recent pasts, check if this is followed by a perfect
                        if check_ppp and inf_lem == ppp_lemma:
                            s_next = inf.getnext()
                            if s_next.get(pos_attr) in perfect_tags:
                                mwe.add_word(s_next.text, s_next.get(lemma_attr), True, s_next.get('id'))

                        # Break out of the loop: we found our recent past construction
                        break
                    # Stop looking at punctuation or stop tags
                    elif (inf.text and inf.text in string.punctuation) or (inf_pos and inf_pos.startswith(stop_tags)):
                        break
                    # Otherwise: add the word to the MWE
                    else:
                        mwe.add_word(inf.text, inf_lem, False, inf.get('id'))

                # If we found our recent past construction: break out of the loop
                if is_recent_past:
                    break
            # Stop looking at punctuation or stop tags
            elif (pre.text and pre.text in string.punctuation) or (pre_pos and pre_pos.startswith(stop_tags)):
                break
            # Otherwise: add the word to the MWE
            else:
                mwe.add_word(pre.text, pre_lem, False, pre.get('id'))

        return mwe if is_recent_past else None
