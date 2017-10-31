from collections import Counter
import glob
import os

from .base import BaseCounter
from lxml import etree


EUROPARL_CONFIG = os.path.join(os.path.dirname(__file__), '../config/europarl.cfg')


class EuroparlCounter(BaseCounter):
    def get_config(self):
        return EUROPARL_CONFIG

    def list_filenames(self, dir_name):
        return sorted(glob.glob(os.path.join(dir_name, '*.xml')))

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
            results.append([filename, k, str(v)])

        return results
