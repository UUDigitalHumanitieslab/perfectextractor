from abc import ABC

from .base import BaseExtractor
from .models import MultiWordExpression


class PoSExtractor(BaseExtractor, ABC):
    def __init__(self, language_from, languages_to=None, pos=None, regex=None, **kwargs):
        """
        Initializes the extractor for the given source and target language(s).
        Reads in the config for the source language.
        :param language_from: the source language
        :param languages_to: the target language(s)
        :param pos: A list of part-of-speech tags
        :param regex: A list of regular expressions
        """
        super().__init__(language_from, languages_to, **kwargs)

        self.pos = pos
        self.regex = regex

    def prepare_xpath(self):
        id_attr = self.config.get('all', 'id')
        lemma_attr = self.config.get('all', 'lemma_attr')
        pos_attr = self.config.get(self.l_from, 'pos', fallback=self.config.get('all', 'pos'))

        ns = {}
        predicate = 'contains(" {value} ", concat(" ", @{element}, " "))'
        predicates = []

        if self.tokens:
            predicates.append(predicate.format(element=id_attr, value=' '.join(self.tokens.keys())))
        if self.lemmata_list:
            predicates.append(predicate.format(element=lemma_attr, value=' '.join(self.lemmata_list)))
        if self.pos:
            predicates.append(predicate.format(element=pos_attr, value=' '.join(self.pos)))
        if self.regex:
            # prepare a pattern that combines multiple regexps using OR operators
            # and non-capturing groups
            pattern = '|'.join('(?:{})'.format(r) for r in self.regex)

            # special namespace required for enabling regular expression functions
            ns = {"re": "http://exslt.org/regular-expressions"}
            predicates.append('re:test(., "{pattern}", "i")'.format(pattern=pattern))

        xpath = './/' + self.word_tag
        if predicates:
            xpath = './/{}[{}]'.format(self.word_tag, ' and '.join(predicates))

        return xpath, ns

    def preprocess_found(self, word):
        """
        Preprocesses the found word:
        - removes a word if it does not occur in the lemmata list
        - removes a word if it is not in the correct position in the sentence
        Returns the found word as a list, as it might be interesting to include words before and after
        (see e.g. EuroparlFrenchArticleExtractor)
        """
        result = [word]

        id_attr = self.config.get('all', 'id')

        # TODO: check if this is generic
        if self.position and not word.get(id_attr).endswith('.' + str(self.position)):
            result = []

        if self.tokens:
            end_token = self.tokens.get(word.get(id_attr))
            next_word = word.getnext()
            if next_word is None:
                raise ValueError('End token {} not found'.format(end_token))
            else:
                while next_word.get(id_attr) != end_token:
                    result.append(next_word)

                    next_word = next_word.getnext()
                    if next_word is None:
                        raise ValueError('End token {} not found'.format(end_token))
                else:
                    result.append(next_word)

        return result

    def words2mwe(self, words, sentence):
        id_attr = self.config.get('all', 'id')
        lemma_attr = self.config.get('all', 'lemma_attr')

        result = MultiWordExpression(sentence)
        for word in words:
            result.add_word(word.text, word.get(lemma_attr), self.get_pos(self.l_from, word), word.get(id_attr))
        return result
