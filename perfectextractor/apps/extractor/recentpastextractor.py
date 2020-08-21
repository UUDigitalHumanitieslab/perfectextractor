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
        id_attr = self.config.get('all', 'id')
        lemma_attr = self.config.get('all', 'lemma_attr')
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
        mwe.add_word(self.get_text(w), w.get(lemma_attr), self.get_pos(language, w), w.get(id_attr))

        # Check the siblings for the preposition of the recent past construction
        for pre in self.get_siblings(w, sentence.get(id_attr), False):
            pre_pos = self.get_pos(language, pre)
            pre_lem = pre.get(lemma_attr)
            if pre_pos in rp_pre_pos and pre_lem == rp_pre_lem:
                mwe.add_word(self.get_text(pre), pre_lem, self.get_pos(language, pre), pre.get(id_attr))

                # Now look at the siblings to find an infinitive
                for inf in self.get_siblings(pre, sentence.get(id_attr), False):
                    inf_pos = self.get_pos(language, inf)
                    inf_lem = inf.get(lemma_attr)
                    if inf_pos == rp_inf_pos:
                        is_recent_past = True
                        mwe.add_word(self.get_text(inf), inf_lem, self.get_pos(language, inf), inf.get(id_attr))

                        # If the language has passive recent pasts, check if this is followed by a perfect
                        if check_ppp and inf_lem == ppp_lemma:
                            s_next = inf.getnext()
                            if s_next is not None and self.get_pos(language, s_next) in perfect_tags:
                                mwe.add_word(self.get_text(s_next), s_next.get(lemma_attr), self.get_pos(language, s_next), s_next.get(id_attr))

                        # Break out of the loop: we found our recent past construction
                        break
                    # Stop looking at punctuation or stop tags
                    elif (self.get_text(inf) in string.punctuation) or (inf_pos and inf_pos.startswith(stop_tags)):
                        break
                    # Otherwise: add the word to the MWE
                    else:
                        mwe.add_word(self.get_text(inf), inf_lem, self.get_pos(language, inf), inf.get(id_attr), in_construction=False)

                # If we found our recent past construction: break out of the loop
                if is_recent_past:
                    break
            # Stop looking at punctuation or stop tags
            elif (self.get_text(pre) in string.punctuation) or (pre_pos and pre_pos.startswith(stop_tags)):
                break
            # Otherwise: add the word to the MWE
            else:
                mwe.add_word(self.get_text(pre), pre_lem, self.get_pos(language, pre), pre.get(id_attr), in_construction=False)

        return mwe if is_recent_past else None
