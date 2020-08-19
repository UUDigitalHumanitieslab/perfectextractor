import os

BASE_CONFIG = os.path.join(os.path.dirname(__file__), 'base.cfg')

TEI_URL = 'http://www.tei-c.org/ns/1.0'
TEI_NS = {'ns': TEI_URL}


class BaseDPC(object):
    def get_config(self):
        return BASE_CONFIG

    @property
    def sentence_tag(self):
        return '{{{}}}s'.format(TEI_URL)

    @property
    def word_tag(self):
        return 'ns:w'
