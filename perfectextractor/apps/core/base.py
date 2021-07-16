from abc import ABC, abstractmethod
import configparser
import os
from typing import Iterator, Optional

from lxml import etree

from perfectextractor.apps.extractor.utils import CachedConfig, TXT, CSV


class BaseWorker(ABC):
    def __init__(self,
                 language_from: str,
                 outfile: Optional[str] = None,
                 format_: str = CSV):
        self.l_from = language_from
        self.outfile = outfile
        self.format_ = format_

        # Read the config
        config = configparser.ConfigParser()
        config.read(self.get_config())
        self.config = CachedConfig(config)

    def list_directories(self, path: str) -> Iterator[str]:
        directories = [os.path.join(path, directory) for directory in os.listdir(path)]
        return filter(os.path.isdir, directories)

    @abstractmethod
    def get_config(self):
        """
        Returns the location of the configuration file.
        """
        pass

    @staticmethod
    def get_text(element: etree._Element) -> str:
        return str(element.text) if element.text else ''

    def get_id(self, element: etree._Element) -> str:
        # TODO: for corpora without XML id, we should base this on the position in the sentence
        id_attr = self.config.get('all', 'id')
        return element.get(id_attr, '?')

    def get_lemma(self, element: etree._Element) -> str:
        lemma_attr = self.config.get('all', 'lemma_attr')
        return element.get(lemma_attr, '?')

    def get_pos(self, language: str, element: etree._Element) -> str:
        """
        Retrieves the part-of-speech tag for the current language and given element,
        with a fallback to the default part-of-speech tag in the corpus as a whole.
        :param language: the current language
        :param element: the current element
        :return: the part-of-speech tag
        """
        return element.get(self.config.get(language, 'pos', fallback=self.config.get('all', 'pos')), '?')
