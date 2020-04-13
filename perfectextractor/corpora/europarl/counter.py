from collections import Counter

from lxml import etree

from perfectextractor.apps.counter.base import BaseCounter
from .base import BaseEuroparl


class EuroparlCounter(BaseEuroparl, BaseCounter):
    def process_file(self, filename):
        """
        Processes a single file.
        """
        results = []

        # Parse the current tree
        tree = etree.parse(filename)

        c = Counter()
        for w in tree.xpath('.//w[starts-with(@tree, "V")]'):
            c[w.get('lem', '-')] += 1

        for k, v in c.most_common():
            results.append([filename, 'europarl', k, str(v)])

        return results
