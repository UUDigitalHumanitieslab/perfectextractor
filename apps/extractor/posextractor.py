from abc import ABCMeta, abstractmethod
import codecs
import ConfigParser
import os

from .base import BaseExtractor
from .utils import UnicodeWriter

LEMMATA_CONFIG = os.path.join(os.path.dirname(__file__), '../config/{language}_lemmata.txt')


class PoSExtractor(BaseExtractor):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to=None, sentence_ids=None, lemmata=False, position=None, pos=None):
        """
        Initializes the extractor for the given source and target language(s).
        Reads in the config for the source language,
        as well as a list of lemmata.
        :param language_from: the source language
        :param languages_to: the target language(s)
        :param sentence_ids: whether to limit the search to certain sentence IDs
        :param lemmata: whether to limit the search to certain lemmata (can be provided as a boolean or a list)
        :param position: whether to limit the search to a certain position (e.g. only sentence-initial)
        :param pos: A list of part-of-speech tags
        """
        super(PoSExtractor, self).__init__(language_from, languages_to, sentence_ids=sentence_ids, position=position)

        self.pos = pos

        # Read the config
        config = ConfigParser.RawConfigParser()
        config.readfp(codecs.open(self.get_config(), 'r', 'utf8'))
        self.config = config

        # Read in the lemmata list (if provided)
        self.read_lemmata(lemmata)

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
        return words[0].get(self.config.get(self.l_from, 'pos'))
