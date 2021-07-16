from abc import abstractmethod

from perfectextractor.apps.core.base import BaseWorker
from perfectextractor.apps.extractor.utils import CSV, open_csv, open_xlsx


class BaseCounter(BaseWorker):
    def __init__(self, language_from, outfile, format_=CSV):
        """
        Initializes the counter for the given source and target language(s).
        :param language_from: the source language
        :param format_: whether to output the file as .csv or .xlsx
        """
        super().__init__(language_from, outfile, format_)

    def process_folder(self, dir_name):
        """
        Creates a result file and processes each file in a folder.
        """
        result_file = self.outfile or '-counts-'.join([dir_name, self.l_from]) + '.' + self.format_
        opener = open_csv if self.format_ == CSV else open_xlsx

        with opener(result_file) as writer:
            header = ['document', 'extra', 'lemma', 'count']
            writer.writerow(header) if self.format_ == CSV else writer.writerow(header, is_header=True)

            for filename in self.list_filenames(dir_name):
                results = self.process_file(filename)
                writer.writerows(results)

    @abstractmethod
    def process_file(self, filename):
        """
        Process a single file
        """
        pass

    @abstractmethod
    def list_filenames(self, dir_name):
        """
        List all to be processed files in the given directory.
        """
        pass
