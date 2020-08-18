import os
import shutil
import unittest

from click.testing import CliRunner

from perfectextractor.extract import extract

EUROPARL_DATA = os.path.join(os.path.dirname(__file__), 'data/europarl')

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.runner = CliRunner()
        self.folder_out = os.path.join(EUROPARL_DATA, 'out')
        self.folder_cmp = os.path.join(EUROPARL_DATA, 'cmp')

    def test_arguments(self):
        runner = CliRunner()
        result = runner.invoke(extract)
        self.assertEqual(result.exit_code, 2)  # need to provide arguments

    def test_perfectextractor(self):
        os.mkdir(self.folder_out)

        filename = 'en-nl-perfect.csv'
        out_file = os.path.join(self.folder_out, filename)
        result = self.runner.invoke(extract, [EUROPARL_DATA, 'en', 'nl',
                                              '--extractor', 'perfect',
                                              '--outfile', out_file])
        self.assertEqual(result.exit_code, 0)

        cmp_file = os.path.join(self.folder_cmp, filename)

        with open(out_file) as tmp:
            with open(cmp_file) as cmp:
                self.assertListEqual(tmp.readlines(), cmp.readlines())

    def test_recentpastextractor(self):
        os.mkdir(self.folder_out)

        filename = 'fr-nl-recentpast.csv'
        out_file = os.path.join(self.folder_out, filename)
        result = self.runner.invoke(extract, [EUROPARL_DATA, 'fr', 'nl',
                                              '--extractor', 'recent_past',
                                              '--outfile', out_file])
        self.assertEqual(result.exit_code, 0)

        cmp_file = os.path.join(self.folder_cmp, filename)

        with open(out_file) as tmp:
            with open(cmp_file) as cmp:
                self.assertListEqual(tmp.readlines(), cmp.readlines())

    def test_sinceextractor(self):
        os.mkdir(self.folder_out)

        filename = 'nl-en-since.csv'
        out_file = os.path.join(self.folder_out, filename)
        result = self.runner.invoke(extract, [EUROPARL_DATA, 'nl', 'en',
                                              '--extractor', 'since_duration',
                                              '--outfile', out_file])
        self.assertEqual(result.exit_code, 0)

        cmp_file = os.path.join(self.folder_cmp, filename)

        with open(out_file) as tmp:
            with open(cmp_file) as cmp:
                self.assertListEqual(tmp.readlines(), cmp.readlines())

    def tearDown(self):
        if os.path.isdir(self.folder_out):
            shutil.rmtree(self.folder_out)
