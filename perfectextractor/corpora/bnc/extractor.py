# -*- encoding: utf-8 -*-

import os

from lxml import etree

from perfectextractor.apps.extractor.base import BaseExtractor
from perfectextractor.apps.extractor.perfectextractor import PerfectExtractor
from perfectextractor.apps.extractor.utils import XML

from .base import BaseBNC


class BNCExtractor(BaseBNC, BaseExtractor):
    def process_file(self, filename):
        results = []

        # Retrieve the genre
        tree = etree.parse(filename)
        genre = self.get_genre(tree)

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag='s')

        # Find potential Perfects
        for _, s in s_trees:
            if self.sentence_ids and s.get('n') not in self.sentence_ids:
                continue

            result = list()
            result.append(os.path.basename(filename))
            result.append(s.get('n'))
            result.append(genre)
            result.append('')
            result.append('')
            if self.output == XML:
                result.append('<root>' + etree.tostring(s) + '</root>')
            else:
                result.append(self.get_sentence_words(s))

            results.append(result)
        return results

    def get_sentence(self, element):
        return element.xpath('ancestor::s')[0]

    def get_siblings(self, element, sentence_id, check_preceding):
        return element.itersiblings(tag='w', preceding=check_preceding)

    def get_sentence_words(self, sentence):
        """
        Returns all words in the sentence.
        Note that in the BNC, these can be either in w or c tags (the latter are for punctuation)
        :param sentence: the s element
        :return: all w and c texts, joined with a space.
        """
        s = []
        for w in sentence.xpath('.//w | .//c'):
            s.append(w.text.strip() if w.text else ' ')
        return ' '.join(s)

    def sort_by_alignment_certainty(self, file_names):
        raise NotImplementedError

    def filter_by_file_size(self, file_names):
        raise NotImplementedError

    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        raise NotImplementedError


class BNCPerfectExtractor(BNCExtractor, PerfectExtractor):
    def get_line_and_pp(self, tree, language_to, segment_number):
        raise NotImplementedError

    def generate_header(self):
        header = [
            'document',
            'genre',
            'is-perfect',
            'tense',
            'words',
            'lemma',
            'is-question',
            'text']
        return header

    def process_file(self, filename):
        """
        Processes a single file.
        """
        results = []

        # Retrieve the genre
        tree = etree.parse(filename)
        genre = self.get_genre(tree)

        # if not genre.startswith('S'):  # Only spoken genre for the moment
        #    return results

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag='s')

        # Find potential Perfects
        for _, s in s_trees:
            sentence = self.get_sentence_words(s)
            is_question = self.is_question(sentence)

            for e in s.xpath(self.config.get(self.l_from, 'xpath')):
                pp = self.check_perfect(e, self.l_from)

                # If this is really a Perfect, add it to the result
                if pp:
                    result = list()
                    result.append(os.path.basename(filename))
                    result.append(genre)
                    result.append('1')
                    result.append(pp.perfect_type())
                    result.append(pp.verbs_to_string())
                    result.append(pp.perfect_lemma())
                    result.append('1' if is_question else '0')
                    result.append(sentence)
                    results.append(result)

                    # If we want (only) one classification per sentence, break the for loop here.
                    if self.one_per_sentence:
                        break
            else:
                # If we want one classification per sentence, add the sentence with a classification here.
                if self.one_per_sentence:
                    tense, tenses = self.get_tenses(s)

                    result = list()
                    result.append(os.path.basename(filename))
                    result.append(genre)
                    result.append('0')
                    result.append(tense)
                    result.append(','.join(tenses))
                    result.append('')
                    result.append('1' if is_question else '0')
                    result.append(sentence)
                    results.append(result)

        return results

    def is_question(self, sentence):
        """
        Naively checks if a sentence is a question.
        :param sentence: a string of words separated by spaces
        :return: whether this sentence contains a question mark
        """
        return '?' in sentence

    def get_pos(self, language, element):
        """
        POS-tags in the BNC can potentially consist of two part-of-speech tags,
        but the first tag is the most likely choice.
        See http://www.natcorp.ox.ac.uk/docs/URG/posguide.html#ambiguity
        :param language: the current language
        :param element: the current w element
        :return: the (most likely) part-of-speech tag
        """
        pos = element.get(self.config.get(language, 'pos'))
        return pos.split('-')[0]
