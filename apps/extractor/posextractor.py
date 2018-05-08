from abc import ABCMeta, abstractmethod
import codecs
import ConfigParser
import os

from .base import BaseExtractor
from .utils import UnicodeWriter

LEMMATA_CONFIG = os.path.join(os.path.dirname(__file__), '../config/{language}_lemmata.txt')


class PoSExtractor(BaseExtractor):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to=None, pos=None, sentence_ids=None, lemmata=False):
        """
        Initializes the extractor for the given source and target language(s).
        Reads in the config for the source language,
        as well as a list of lemmata.
        :param language_from: the source language
        :param languages_to: the target language(s)
        :param pos: A list of part-of-speech tags
        :param lemmata: whether to limit the search to certain lemmata (can be provided as a boolean or a list)
        """
        super(PoSExtractor, self).__init__(language_from, languages_to, sentence_ids=sentence_ids)

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
        Preprocesses the found word
        """
        raise NotImplementedError

    @abstractmethod
    def get_type(self, word):
        """
        Return the type for the found word. A sensible default is the part-of-speech.
        """
