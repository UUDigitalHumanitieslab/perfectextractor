from abc import ABC
import string
from typing import List, Optional

from lxml import etree

from .base import BaseExtractor
from .models import MultiWordExpression


class RecentPastExtractor(BaseExtractor, ABC):
    def __init__(self,
                 language_from: str,
                 languages_to: Optional[List[str]] = None,
                 **kwargs) -> None:
        """
        Initializes the extractor for the given source and target language(s).
        Reads in the config for the source language.
        :param language_from: the source language
        :param languages_to: the target language(s)
        """
        super().__init__(language_from, languages_to, **kwargs)

        self.check_language_in_config(language_from)

    def check_recent_past(self, w: etree._Element, language: str) -> Optional[MultiWordExpression]:
        """
        Checks if the element w is the start of a recent past construction
        :param w: the starting element
        :param language: the language
        :return: if found, the recent past construction as a MultiWordExpression, otherwise None
        """
        is_recent_past = False

        # Retrieve the configuration variables
        rp_pre_pos = self.config.get(language, 'rp_pre_pos').split('|')
        rp_pre_lem = self.config.get(language, 'rp_pre_lem')
        rp_inf_pos = self.config.get(language, 'rp_inf_pos')
        check_ppp = self.config.get(language, 'ppp')
        ppp_lemma = self.config.get(language, 'ppp_lemma')
        perfect_tags = self.config.get(language, 'perfect_tags').split('|')
        stop_tags = tuple(self.config.get(language, 'stop_tags').split('|'))

        sentence = self.get_sentence(w)

        # Start a new MWE at the first word
        mwe = MultiWordExpression(sentence)
        mwe.add_word(self.get_text(w), self.get_lemma(w), self.get_pos(language, w), self.get_id(w))

        # Check the siblings for the preposition of the recent past construction
        for pre in self.get_siblings(w, self.get_id(sentence), False):
            pre_text = self.get_text(pre)
            pre_lem = self.get_lemma(pre)
            pre_pos = self.get_pos(language, pre)
            pre_id = self.get_id(pre)
            if pre_pos in rp_pre_pos and pre_lem == rp_pre_lem:
                mwe.add_word(pre_text, pre_lem, pre_pos, pre_id)

                # Now look at the siblings to find an infinitive
                for inf in self.get_siblings(pre, self.get_id(sentence), False):
                    inf_text = self.get_text(inf)
                    inf_lem = self.get_lemma(inf)
                    inf_pos = self.get_pos(language, inf)
                    inf_id = self.get_id(inf)
                    if inf_pos == rp_inf_pos:
                        is_recent_past = True
                        mwe.add_word(inf_text, inf_lem, inf_pos, inf_id)

                        # If the language has passive recent pasts, check if this is followed by a perfect
                        if check_ppp and inf_lem == ppp_lemma:
                            s_next = inf.getnext()
                            if s_next is not None and self.get_pos(language, s_next) in perfect_tags:
                                mwe.add_word(self.get_text(s_next), self.get_lemma(s_next),
                                             self.get_pos(language, s_next), self.get_id(s_next))

                        # Break out of the loop: we found our recent past construction
                        break
                    # Stop looking at punctuation or stop tags
                    elif inf_text in string.punctuation or (inf_pos and inf_pos.startswith(stop_tags)):
                        break
                    # Otherwise: add the word to the MWE
                    else:
                        mwe.add_word(inf_text, inf_lem, inf_pos, inf_id, in_construction=False)

                # If we found our recent past construction: break out of the loop
                if is_recent_past:
                    break
            # Stop looking at punctuation or stop tags
            elif pre_text in string.punctuation or (pre_pos and pre_pos.startswith(stop_tags)):
                break
            # Otherwise: add the word to the MWE
            else:
                mwe.add_word(pre_text, pre_lem, pre_pos, pre_id, in_construction=False)

        return mwe if is_recent_past else None
