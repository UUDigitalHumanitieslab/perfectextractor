from abc import ABCMeta, abstractmethod


class BaseExtractor(object):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to):
        """
        Initializes the extractor for the given source and target language(s).
        :param language_from: the source language
        :param languages_to: the target language(s)
        """
        self.l_from = language_from
        self.l_to = languages_to

    @abstractmethod
    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        """
        Returns the translated segment numbers (could be multiple) for a segment number in the original text.
        """
        raise NotImplementedError

