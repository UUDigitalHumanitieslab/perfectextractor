from abc import ABCMeta, abstractmethod
import codecs
import csv
import os

import click

from .utils import TXT

LEMMATA_CONFIG = os.path.join(os.path.dirname(__file__), 'config/{language}_lemmata.txt')


class BaseExtractor(object):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to=None,
                 file_names=None, sentence_ids=None,
                 lemmata=None, tokens=None, outfile=None, position=None, output=TXT,
                 sort_by_certainty=False, file_limit=0, min_file_size=0, max_file_size=0):
        """
        Initializes the extractor for the given source and target language(s).
        :param language_from: the source language
        :param languages_to: the target language(s)
        :param file_names: whether to limit the search to certain file names
        :param sentence_ids: whether to limit the search to certain sentence IDs
        :param lemmata: whether to limit the search to certain lemmata (can be provided as a boolean or a list)
        :param tokens: whether to limit the search to certain tokens (list of tuples (from-to))
        :param outfile: the filename to output the results to
        :param position: whether to limit the search to a certain position (e.g. only sentence-initial)
        :param output: whether to output the results in text or XML format
        :param sort_by_certainty: whether to sort the files by average alignment certainty
        :param file_limit: whether to limit the number of files searched in
        :param min_file_size: whether to only use files larger (or equal) than a certain size
        :param max_file_size: whether to only use files smaller (or equal) than a certain size
        """
        self.l_from = language_from
        self.l_to = languages_to or []
        self.file_names = file_names
        self.sentence_ids = sentence_ids
        self.tokens = dict(tokens) if tokens else None
        self.outfile = outfile
        self.position = position
        self.output = output
        self.sort_by_certainty = sort_by_certainty
        self.file_limit = file_limit
        self.min_file_size = min_file_size
        self.max_file_size = max_file_size

        # Read in the lemmata list (if provided)
        self.lemmata_list = []
        self.read_lemmata(lemmata)

        # Other variables
        self.other_extractors = []
        self.alignment_xmls = dict()

    def process_folder(self, dir_name):
        """
        Creates a result file and processes each file in a folder.
        """
        result_file = self.outfile or '-'.join([dir_name, self.l_from]) + '.csv'
        with open(result_file, 'w') as f:
            f.write('\uFEFF')  # the UTF-8 BOM to hint Excel we are using that...
            csv_writer = csv.writer(f, delimiter=';')
            csv_writer.writerow(self.generate_header())
            csv_writer.writerows(self.generate_results(dir_name))

    def collect_file_names(self, dir_name):
        """
        Collects the file names in a given directory and (potentially) filters these based on file size,
        alignment certainty or a limited number of files.
        :param dir_name: The current directory
        :return: A list of files to consider.
        """
        click.echo('Collecting file names...')

        if self.file_names:
            file_names = [os.path.join(dir_name, f) for f in self.file_names]
        else:
            file_names = self.list_filenames(dir_name)

        if self.min_file_size or self.max_file_size:
            file_names = self.filter_by_file_size(file_names)

        if self.sort_by_certainty:
            file_names = self.sort_by_alignment_certainty(file_names)

        if self.file_limit:
            file_names = file_names[:self.file_limit]

        click.echo('Finished collecting file names, starting processing...')
        return file_names

    def generate_results(self, dir_name):
        results = []

        for file_name in self.collect_file_names(dir_name):
            result = self.process_file(file_name)

            for extractor in self.other_extractors:
                extractor.sentence_ids = [r[1] for r in result]
                result = extractor.process_file(file_name)

            results.extend(result)

        return results

    def generate_header(self):
        header = [
            'document',
            'sentence',
            'type {}'.format(self.l_from),
            'words {}'.format(self.l_from),
            'ids {}'.format(self.l_from),
            self.l_from]
        for language in self.l_to:
            header.append('alignment type')
            header.append(language)
        return header

    def read_lemmata(self, lemmata):
        if lemmata is not None:
            if type(lemmata) in (list, tuple):
                self.lemmata_list = list(lemmata)
            elif type(lemmata) == bool:
                if lemmata:
                    with codecs.open(LEMMATA_CONFIG.format(language=self.l_from), 'r', 'utf-8') as lexicon:
                        self.lemmata_list = lexicon.read().split()
            else:
                raise ValueError('Unknown value for lemmata')

    def add_extractor(self, extractor):
        """
        Adds another Extractor to this Extractor. This allows to combine Extractors.
        The last added Extractor determines the output.
        """
        self.other_extractors.append(extractor)

    def list_directories(self, path):
        directories = [os.path.join(path, directory) for directory in os.listdir(path)]
        return filter(os.path.isdir, directories)

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

    @abstractmethod
    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        """
        Returns the translated segment numbers (could be multiple) for a segment number in the original text.
        """
        raise NotImplementedError

    @abstractmethod
    def get_sentence(self, element):
        """
        Returns the full sentence XML for the given element.
        """
        raise NotImplementedError

    @abstractmethod
    def get_siblings(self, element, sentence_id, check_preceding):
        """
        Returns the siblings of the given element in the given sentence_id.
        The check_preceding parameter allows to look either forwards or backwards.
        """
        raise NotImplementedError

    @abstractmethod
    def sort_by_alignment_certainty(self, file_names):
        raise NotImplementedError

    @abstractmethod
    def filter_by_file_size(self, file_names):
        raise NotImplementedError
