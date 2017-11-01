from lxml import etree

from apps.extractor.base import BaseExtractor
from apps.extractor.perfectextractor import PerfectExtractor

from .base import BaseBNC


class BNCExtractor(BaseBNC, BaseExtractor):
    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        raise NotImplementedError

    def process_file(self, filename):
        raise NotImplementedError

    def get_sentence(self, element):
        return element.xpath('ancestor::s')[0]

    def get_siblings(self, element, sentence_id, check_preceding):
        return element.itersiblings(tag='w', preceding=check_preceding)


class BNCPerfectExtractor(BNCExtractor, PerfectExtractor):
    def get_line_by_number(self, tree, language_to, segment_number):
        raise NotImplementedError

    def process_file(self, filename):
        """
        Processes a single file.
        """
        results = []

        # Parse the current tree
        tree = etree.parse(filename)
        genre = self.get_genre(tree)

        # Find potential present perfects
        for e in tree.xpath(self.config.get(self.l_from, 'xpath')):
            pp = self.check_present_perfect(e, self.l_from)

            # If this is really a present perfect, add it to the result
            if pp:
                result = list()
                result.append(filename)
                result.append(genre)
                result.append(pp.perfect_type())
                result.append(pp.verbs_to_string())
                result.append(pp.perfect_lemma())
                result.append(pp.mark_sentence())

                results.append(result)

        return results
