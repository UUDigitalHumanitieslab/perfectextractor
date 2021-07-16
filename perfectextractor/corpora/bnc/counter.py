from collections import Counter
import os

from lxml import etree

from perfectextractor.apps.counter.base import BaseCounter
from .base import BaseBNC


class BNCCounter(BaseBNC, BaseCounter):
    def get_config(self):
        counter_config = os.path.join(os.path.dirname(__file__), 'counter.cfg')
        return [super().get_config(), counter_config]

    def process_file(self, filename):
        """
        Processes a single file.
        """
        results = []

        # Parse the current tree
        tree = etree.parse(filename)
        genre = self.get_genre(tree)

        c = Counter()
        for w in tree.xpath(self.config.get(self.l_from, 'xpath')):
            c[self.get_lemma(w)] += 1

        for k, v in c.most_common():
            results.append([os.path.basename(filename), genre, k, str(v)])

        return results
