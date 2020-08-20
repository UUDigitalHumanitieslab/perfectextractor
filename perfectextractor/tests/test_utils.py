import unittest

from perfectextractor.apps.extractor.xml_utils import get_adjacent_line_number
from perfectextractor.corpora.dpc.utils import is_nl


class TestUtils(unittest.TestCase):
    def test_get_adjacent_line_number(self):
        next_line = get_adjacent_line_number('p1.s1', 2)
        self.assertEqual(next_line, 'p1.s3')
        next_line = get_adjacent_line_number('p2.s6', 4)
        self.assertEqual(next_line, 'p2.s10')

    def test_is_nl(self):
        self.assertEqual(is_nl('nl'), 1)
        self.assertEqual(is_nl('en'), 0)
