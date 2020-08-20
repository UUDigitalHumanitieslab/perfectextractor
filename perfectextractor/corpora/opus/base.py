import glob
import os

BASE_CONFIG = os.path.join(os.path.dirname(__file__), 'base.cfg')


class BaseOPUS(object):
    def get_config(self):
        return BASE_CONFIG

    def list_filenames(self, dir_name):
        return sorted(glob.glob(os.path.join(dir_name, '*.xml')))
