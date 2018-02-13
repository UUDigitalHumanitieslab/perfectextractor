from abc import ABCMeta, abstractmethod
import codecs
import ConfigParser
import os

from .base import BaseExtractor
from .utils import UnicodeWriter

LEMMATA_CONFIG = os.path.join(os.path.dirname(__file__), '../config/{language}_lemmata.txt')


class PoSExtractor(BaseExtractor):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to, pos, lemmata=False):
        """
        Initializes the extractor for the given source and target language(s).
        Reads in the config for the source language,
        as well as a list of lemmata.
        :param language_from: the source language
        :param languages_to: the target language(s)
        :param pos: A list of part-of-speech tags
        :param lemmata: whether to limit the search to certain lemmata (can be provided as a boolean or a list)
        """
        self.l_from = language_from
        self.l_to = languages_to
        self.pos = pos

        # Read the config
        config = ConfigParser.RawConfigParser()
        config.readfp(codecs.open(self.get_config(), 'r', 'utf8'))
        self.config = config

        # Read in the lemmata list (if provided)
        self.read_lemmata(lemmata)

    def process_folder(self, dir_name):
        """
        Creates a result file and processes each file in a folder.
        """
        result_file = '-'.join([dir_name, self.l_from]) + '.csv'
        with open(result_file, 'wb') as f:
            f.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
            csv_writer = UnicodeWriter(f, delimiter=';')

            header = [
                'document',
                self.l_from,
                'type' + ' ' + self.l_from,
                'id' + ' ' + self.l_from,
                self.l_from]
            for language in self.l_to:
                header.append('alignment type')
                header.append(language)
            csv_writer.writerow(header)

            for filename in self.list_filenames(dir_name):
                results = self.process_file(filename)
                csv_writer.writerows(results)

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
