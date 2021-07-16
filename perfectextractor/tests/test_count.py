import os
import shutil
import unittest

from click.testing import CliRunner

from perfectextractor.count import count

EUROPARL_DATA = os.path.join(os.path.dirname(__file__), 'data/europarl')


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.folder_out = os.path.join(EUROPARL_DATA, 'out')
        self.folder_cmp = os.path.join(EUROPARL_DATA, 'cmp')

    def test_arguments(self):
        runner = CliRunner()
        result = runner.invoke(count)
        self.assertEqual(result.exit_code, 2)  # need to provide arguments

    def test_counter(self):
        os.mkdir(self.folder_out)

        filename = 'en-counts.csv'
        out_file = os.path.join(self.folder_out, filename)
        result = self.runner.invoke(count, [EUROPARL_DATA, 'en', '--outfile', out_file])
        self.assertEqual(result.exit_code, 0)

        cmp_file = os.path.join(self.folder_cmp, filename)

        with open(out_file) as tmp:
            with open(cmp_file) as cmp:
                self.assertListEqual(tmp.readlines(), cmp.readlines())

    def tearDown(self):
        if os.path.isdir(self.folder_out):
            shutil.rmtree(self.folder_out)
