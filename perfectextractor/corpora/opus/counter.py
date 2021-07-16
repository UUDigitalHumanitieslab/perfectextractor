from collections import Counter
import os

from lxml import etree

from perfectextractor.apps.counter.base import BaseCounter
from .base import BaseOPUS


class OPUSCounter(BaseOPUS, BaseCounter):
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

        c = Counter()
        for w in tree.xpath(self.config.get(self.l_from, 'xpath')):
            c[self.get_lemma(w)] += 1

        for k, v in c.most_common():
            results.append([os.path.basename(filename), 'opus', k, str(v)])

        return results

    def list_directories(self, path):
        return filter(lambda x: x.endswith(self.l_from), super().list_directories(path))
