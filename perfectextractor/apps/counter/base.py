from abc import ABCMeta, abstractmethod

from perfectextractor.apps.extractor.utils import UnicodeWriter


class BaseCounter(object):
    __metaclass__ = ABCMeta

    def __init__(self, language_from):
        """
        Initializes the counter for the given source and target language(s).
        :param language_from: the source language
        """
        self.l_from = language_from

    def process_folder(self, dir_name):
        """
        Creates a result file and processes each file in a folder.
        """
        result_file = '-counts-'.join([dir_name, self.l_from]) + '.csv'
        with open(result_file, 'w') as f:
            f.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
            csv_writer = UnicodeWriter(f, delimiter=';')

            header = ['document', 'lemma', 'count']
            csv_writer.writerow(header)

            for filename in self.list_filenames(dir_name):
                results = self.process_file(filename)
                csv_writer.writerows(results)

    @abstractmethod
    def get_config(self):
        """
        Returns the location of the configuration file.
        """
        raise NotImplementedError

    @abstractmethod
    def process_file(self, filename):
        """
        Process a single file
        """
        raise NotImplementedError

    @abstractmethod
    def list_filenames(self, dir_name):
        """
        List all to be processed files in the given directory.
        """
        raise NotImplementedError
