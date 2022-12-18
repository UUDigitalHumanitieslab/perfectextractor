from abc import ABC
import string
from typing import List, Optional

from lxml import etree

from .base import BaseExtractor
from .models import MultiWordExpression


class ContinuousExtractor(BaseExtractor, ABC):
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

    def check_continuous(self, w: etree._Element, language: str) -> Optional[MultiWordExpression]:
        """
        Checks if the element w is the start of a (present/past) continuous construction
        :param w: the starting element
        :param language: the language
        :return: if found, the recent past construction as a MultiWordExpression, otherwise None
        """
        is_continuous = False

        # Retrieve the configuration variables
        cont_gerund_pos = self.config.get(language, 'cont_gerund_pos').split('|')
        stop_tags = tuple(self.config.get(language, 'stop_tags').split('|'))

        sentence = self.get_sentence(w)

        # Start a new MWE at the first word
        mwe = MultiWordExpression(sentence)
        mwe.add_word(self.get_text(w), self.get_lemma(w), self.get_pos(language, w), self.get_id(w))

        # Check the siblings for the gerund of the continuous construction
        for gerund in self.get_siblings(w, self.get_id(sentence), False):
            gerund_text = self.get_text(gerund)
            gerund_lem = self.get_lemma(gerund)
            gerund_pos = self.get_pos(language, gerund)
            gerund_id = self.get_id(gerund)
            if gerund_pos in cont_gerund_pos:
                # We found our construction: add the word and break out of the loop
                mwe.add_word(gerund_text, gerund_lem, gerund_pos, gerund_id)
                is_continuous = True
                break
            # Stop looking when matching punctuation or stop tags
            elif gerund_text in string.punctuation or (gerund_pos and gerund_pos.startswith(stop_tags)):
                break
            # Otherwise: add the word to the MWE and continue searching for a gerund
            else:
                mwe.add_word(gerund_text, gerund_lem, gerund_pos, gerund_id, in_construction=False)

        return mwe if is_continuous else None
