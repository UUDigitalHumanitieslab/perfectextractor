import glob
import os

EUROPARL_CONFIG = os.path.join(os.path.dirname(__file__), 'europarl.cfg')


class BaseEuroparl(object):
    def get_config(self):
        return EUROPARL_CONFIG

    def list_filenames(self, dir_name):
        return sorted(glob.glob(os.path.join(dir_name, '*.xml')))
