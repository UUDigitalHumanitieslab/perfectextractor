from collections import Counter

from lxml import etree

from perfectextractor.apps.counter.base import BaseCounter
from .base import BaseBNC


class BNCCounter(BaseBNC, BaseCounter):
    def process_file(self, filename):
        """
        Processes a single file.
        """
        results = []

        # Parse the current tree
        tree = etree.parse(filename)
        genre = self.get_genre(tree)

        c = Counter()
        for w in tree.xpath('.//w[@pos="VERB"]'):
            c[w.get('hw', '-')] += 1

        for k, v in c.most_common():
            results.append([filename, genre, k, str(v)])

        return results
