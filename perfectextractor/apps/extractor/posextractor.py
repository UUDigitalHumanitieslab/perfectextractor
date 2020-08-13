from abc import ABCMeta, abstractmethod
import os

from .base import BaseExtractor

LEMMATA_CONFIG = os.path.join(os.path.dirname(__file__), '../config/{language}_lemmata.txt')


class PoSExtractor(BaseExtractor):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to=None, pos=None, regex=None, **kwargs):
        """
        Initializes the extractor for the given source and target language(s).
        Reads in the config for the source language.
        :param language_from: the source language
        :param languages_to: the target language(s)
        :param pos: A list of part-of-speech tags
        :param regex: A list of regular expressions
        """
        super(PoSExtractor, self).__init__(language_from, languages_to, **kwargs)

        self.pos = pos
        self.regex = regex

    @abstractmethod
    def preprocess_found(self, word):
        """
        Preprocesses the found word: potentially add more words to the found words, or filter based on lemmata.
        """
        raise NotImplementedError

    def get_type(self, words):
        """
        Return the type for the found word(s). A sensible default is the part-of-speech of the first found word.
        """
        return self.get_pos(self.l_from, words[0])
