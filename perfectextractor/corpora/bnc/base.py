import glob
import os

BNC_CONFIG = os.path.join(os.path.dirname(__file__), 'bnc.cfg')


class BaseBNC(object):
    def get_config(self):
        return BNC_CONFIG

    def list_filenames(self, dir_name):
        return sorted(glob.glob(os.path.join(dir_name, '*.xml')))

    def get_genre(self, tree):
        return tree.xpath('.//classCode')[0].text
