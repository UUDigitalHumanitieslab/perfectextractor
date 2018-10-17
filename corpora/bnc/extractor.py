import os

from lxml import etree

from apps.extractor.base import BaseExtractor
from apps.extractor.perfectextractor import PerfectExtractor
from apps.extractor.utils import XML

from .base import BaseBNC


class BNCExtractor(BaseBNC, BaseExtractor):
    def process_file(self, filename):
        results = []

        # Retrieve the genre
        tree = etree.parse(filename)
        genre = self.get_genre(tree)

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag='s')

        # Find potential present perfects
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
        # TODO: this is copied from apps/models.py. Consider refactoring!
        s = []
        # TODO: this xPath-expression might be specific for a corpus
        for w in sentence.xpath('.//w'):
            s.append(w.text.strip() if w.text else ' ')
        return ' '.join(s)

    def sort_by_alignment_certainty(self, file_names):
        raise NotImplementedError

    def filter_by_file_size(self, file_names):
        raise NotImplementedError

    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        raise NotImplementedError


class BNCPerfectExtractor(BNCExtractor, PerfectExtractor):
    def get_line_by_number(self, tree, language_to, segment_number):
        raise NotImplementedError

    def process_file(self, filename):
        """
        Processes a single file.
        """
        results = []

        # Retrieve the genre
        tree = etree.parse(filename)
        genre = self.get_genre(tree)

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag='s')

        # Find potential present perfects
        for _, s in s_trees:
            for e in s.xpath(self.config.get(self.l_from, 'xpath')):
                pp = self.check_present_perfect(e, self.l_from)

                # If this is really a present perfect, add it to the result
                if pp:
                    result = list()
                    result.append(os.path.basename(filename))
                    result.append(genre)
                    result.append(pp.perfect_type())
                    result.append(pp.verbs_to_string())
                    result.append(pp.perfect_lemma())
                    result.append(pp.mark_sentence())

                    results.append(result)

        return results
