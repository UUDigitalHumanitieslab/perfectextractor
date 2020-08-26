from abc import ABC, abstractmethod
import codecs
import configparser
import os
import time
from typing import Dict, Generator, Iterator, List, Optional, Tuple, Union

import click
from lxml import etree

from .models import Alignment, MultiWordExpression
from .utils import TXT, XML, CSV, open_csv, open_xlsx, CachedConfig

LEMMATA_CONFIG = os.path.join(os.path.dirname(__file__), 'config/{language}_lemmata.txt')


class BaseExtractor(ABC):
    def __init__(self,
                 language_from: str,
                 languages_to: Optional[List[str]] = None,
                 file_names: Optional[List[str]] = None,
                 sentence_ids: Optional[List[str]] = None,
                 lemmata: Optional[Union[Tuple[str], List[str], bool]] = None,
                 tokens: Optional[List[Tuple[str, str]]] = None,
                 metadata: Optional[List[Tuple[str, str]]] = None,
                 regex: Optional[List[str]] = None,
                 outfile: Optional[str] = None,
                 position: Optional[int] = None,
                 output: str = TXT,
                 format_: str = CSV,
                 one_per_sentence: bool = False,
                 sort_by_certainty: bool = False,
                 file_limit: int = 0,
                 min_file_size: int = 0,
                 max_file_size: int = 0) -> None:
        """
        Initializes the extractor for the given source and target language(s).
        :param language_from: the source language
        :param languages_to: the target language(s)
        :param file_names: whether to limit the search to certain file names
        :param sentence_ids: whether to limit the search to certain sentence IDs
        :param lemmata: whether to limit the search to certain lemmata (can be provided as a boolean or a list)
        :param tokens: whether to limit the search to certain tokens (list of tuples (from-to))
        :param metadata: whether to add metadata to the output (list of tuples (metadata-level))
        :param regex: whether to limit the search to certain regular expressions (list of regexes)
        :param outfile: the filename to output the results to
        :param position: whether to limit the search to a certain position (e.g. only sentence-initial)
        :param output: whether to output the results in text or XML format
        :param format_: whether to output the file as .csv or .xlsx
        :param one_per_sentence: whether to output all lines, and allow one classification per sentence
        :param sort_by_certainty: whether to sort the files by average alignment certainty
        :param file_limit: whether to limit the number of files searched in
        :param min_file_size: whether to only use files larger (or equal) than a certain size
        :param max_file_size: whether to only use files smaller (or equal) than a certain size
        """
        self.l_from = language_from
        self.l_to = languages_to or []
        self.file_names = file_names
        self.sentence_ids = sentence_ids
        self.tokens: Optional[Dict[str, str]] = dict(tokens) if tokens else None
        self.metadata: Dict[str, str] = dict(metadata) if metadata else {}
        self.regex = regex
        self.outfile = outfile
        self.position = position
        self.output = output
        self.format_ = format_
        self.one_per_sentence = one_per_sentence
        self.sort_by_certainty = sort_by_certainty
        self.file_limit = file_limit
        self.min_file_size = min_file_size
        self.max_file_size = max_file_size

        # Read in the lemmata list (if provided)
        self.lemmata_list: List[str] = []
        self.read_lemmata(lemmata)

        # Read the config
        config = configparser.ConfigParser()
        config.read(self.get_config())
        self.config = CachedConfig(config)

        # Other variables
        self.other_extractors: List[BaseExtractor] = []
        self.alignment_xmls: Dict[str, str] = dict()
        self._index: Dict[str, etree._Element] = dict()  # save segments indexed by id

    def read_lemmata(self, lemmata: Optional[Union[Tuple[str], List[str], bool]]) -> None:
        """
        Gathers the lemmata to be filtered upon.
        """
        if lemmata is not None:
            if type(lemmata) in (list, tuple):
                self.lemmata_list = list(lemmata)
            elif type(lemmata) == bool:
                if lemmata:
                    with codecs.open(LEMMATA_CONFIG.format(language=self.l_from), 'r', 'utf-8') as lexicon:
                        self.lemmata_list = lexicon.read().split()
            else:
                raise ValueError('Unknown value for lemmata')

    def check_language_in_config(self, language: str) -> None:
        """
        Checks whether there is an implementation available for the given language.
        """
        if language not in self.config.sections():
            msg = 'No implementation for {} for language {}'.format(self.__class__.__name__, language)
            raise click.ClickException(msg)

    def process_folder(self, dir_name: str, progress_cb=None, done_cb=None) -> None:
        """
        Creates a result file and processes each file in a folder.
        """
        file_names = self.collect_file_names(dir_name)
        progress_total = len(file_names)

        result_file = self.outfile or '-'.join([dir_name, self.l_from]) + '.' + self.format_
        opener = open_csv if self.format_ == CSV else open_xlsx

        with opener(result_file) as writer:
            header = self.generate_header()
            writer.writerow(header) if self.format_ == CSV else writer.writerow(header, is_header=True)
            for i, part in enumerate(self.generate_results(dir_name, file_names)):
                writer.writerows(part)
                if progress_cb:
                    progress_cb(i + 1, progress_total)

            if done_cb:
                done_cb(result_file)

    def collect_file_names(self, dir_name: str) -> List[str]:
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

    def generate_results(self, dir_name: str, file_names: List[str] = None) -> Generator[List[str], List[str], None]:
        """
        Generates the results for a directory or a set of files.
        """
        if file_names is None:
            file_names = self.collect_file_names(dir_name)

        for f in file_names:
            yield self.process_file(f)

    def process_file(self, filename: str) -> List[str]:
        """
        Processes a single file.
        """
        t0 = time.time()
        click.echo('Now processing {}...'.format(filename))

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag=self.sentence_tag)

        # Filter the sentence trees
        s_trees = self.filter_sentences(s_trees)

        # Parse the alignment and translation trees
        alignment_trees, translation_trees = self.parse_alignment_trees(filename)

        t1 = time.time()
        click.echo('Finished parsing trees, took {:.3} seconds'.format(t1 - t0))

        # Fetch the results
        results = self.fetch_results(filename, s_trees, alignment_trees, translation_trees)

        click.echo('Finished fetching results, took {:.3} seconds'.format(time.time() - t1))

        # Free index memory
        self._index = dict()

        return results

    def filter_sentences(self, s_trees):
        """
        Filters the sentences based on the provided sentence_ids.
        """
        if self.sentence_ids:
            # TODO: preferably, this should also return an iterparse instead of a list
            result = []
            for event, s in s_trees:
                if s.get(self.config.get('all', 'id')) in self.sentence_ids:
                    result.append((event, s))
            return result
        else:
            return s_trees

    @property
    def sentence_tag(self) -> str:
        """
        The XML tag used for sentences.
        """
        return 's'

    @property
    def word_tag(self) -> str:
        """
        The XML tag used for words.
        """
        return 'w'

    def generate_header(self) -> List[str]:
        """
        Returns the header for the output file.
        """
        header = [
            'document',
            'sentence',
            'type {}'.format(self.l_from),
            'words {}'.format(self.l_from),
            'ids {}'.format(self.l_from),
            self.l_from]
        for metadata in self.metadata.keys():
            header.append(metadata)
        for language in self.l_to:
            header.append('alignment type')
            header.append(language)
        return header

    def generate_result_line(self,
                             filename: str,
                             sentence: etree._Element,
                             mwe: MultiWordExpression = None) -> List[Optional[str]]:
        """
        Returns a single result line
        :param filename: The current filename
        :param sentence: The current sentence (in XML format)
        :param mwe: The found MultiWordExpression
        :return: A list of output properties.
        """
        result: List[Optional[str]] = list()
        result.append(os.path.basename(filename))
        result.append(self.get_id(sentence))

        if mwe:
            result.append(self.get_type(sentence, mwe=mwe))
            result.append(mwe.construction_to_string())
            result.append(mwe.construction_ids())
            if self.output == XML:
                result.append('<root>' + str(etree.tostring(sentence, encoding=str)) + '</root>')
            else:
                result.append(mwe.mark_sentence())
            self.append_metadata(sentence, result)
        else:
            result.append('')
            result.append('')
            result.append('')
            if self.output == XML:
                result.append('<root>' + str(etree.tostring(sentence, encoding=str)) + '</root>')
            else:
                result.append(self.mark_sentence(sentence))
            self.append_metadata(sentence, result)

        return result

    def append_metadata(self,
                        s: Optional[etree._Element],
                        result: List[Optional[str]]) -> None:
        """
        Appends metadata for to a result line.
        """
        for metadata, level in self.metadata.items():
            if s is not None and level == 's':
                result.append(s.get(metadata))
            elif s is not None and level == 'p':
                result.append(s.getparent().get(metadata))
            elif s is not None and level == 'text':
                result.append(s.getparent().getparent().get(metadata))
            else:
                raise ValueError('Invalid level {}'.format(level))

    def add_extractor(self, extractor: 'BaseExtractor') -> None:
        """
        Adds another Extractor to this Extractor. This allows to combine Extractors.
        The last added Extractor determines the output.
        """
        self.other_extractors.append(extractor)

    def list_directories(self, path: str) -> Iterator[str]:
        directories = [os.path.join(path, directory) for directory in os.listdir(path)]
        return filter(os.path.isdir, directories)

    @staticmethod
    def get_text(element: etree._Element) -> str:
        return str(element.text) if element.text else ''

    def get_id(self, element: etree._Element) -> str:
        # TODO: for corpora without XML id, we should base this on the position in the sentence
        id_attr = self.config.get('all', 'id')
        return element.get(id_attr, '?')

    def get_lemma(self, element: etree._Element) -> str:
        lemma_attr = self.config.get('all', 'lemma_attr')
        return element.get(lemma_attr, '?')

    def get_pos(self, language: str, element: etree._Element) -> str:
        """
        Retrieves the part-of-speech tag for the current language and given element,
        with a fallback to the default part-of-speech tag in the corpus as a whole.
        :param language: the current language
        :param element: the current element
        :return: the part-of-speech tag
        """
        return element.get(self.config.get(language, 'pos', fallback=self.config.get('all', 'pos')), '?')

    def get_tenses(self, sentence):
        """
        This method allows to retrieve the English "tense" for a complete sentence. It is very naive,
        based upon the part-of-speech tags of verbs that appear in the sentence.
        It should work for the tagsets of both the Penn Treebank Project and the BNC.
        See https://www.cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/Penn-Treebank-Tagset.pdf for the
        Penn Treebank Project tagset and see http://www.natcorp.ox.ac.uk/docs/URG/posguide.html#section1
        for the BNC tagset
        :param sentence: the s element
        :return: a tuple of the assigned tense and all tenses for the verbs in the sentences
        """
        tense = 'none'
        tenses = []
        for w in sentence.xpath('.//w'):
            pos = self.get_pos(self.l_from, w)

            if pos.startswith('V') and len(pos) == 3:
                if pos.endswith('B') or pos.endswith('P') or pos.endswith('Z'):
                    tenses.append('present')
                elif pos.endswith('D'):
                    tenses.append('past')
                elif pos.endswith('N'):
                    tenses.append('participle')
                elif pos.endswith('G'):
                    tenses.append('gerund')
                elif pos.endswith('I'):
                    tenses.append('infinitive')
                elif pos == 'VM0':
                    tenses.append('modal')
            elif pos == 'MD':
                tenses.append('modal')
            elif pos == 'BES':
                tenses.append('present')
            elif pos == 'VB':
                tenses.append('infinitive')

        if tenses:
            tenses_set = set(tenses)
            if len(tenses_set) == 1:
                tense = tenses[0]
            else:
                if tenses_set in [{'present', 'infinitive'}, {'present', 'gerund'}, {'present', 'gerund', 'infinitive'}]:
                    tense = 'present'
                elif tenses_set in [{'past', 'infinitive'}, {'past', 'gerund'}, {'past', 'gerund', 'infinitive'}]:
                    tense = 'past'
                elif tenses_set == {'modal', 'infinitive'}:
                    tense = 'modal'
                else:
                    tense = 'other'

        return tense, tenses

    @abstractmethod
    def get_config(self) -> Union[str, List[str]]:
        """
        Returns the location of the configuration file, potentially multiple
        """
        pass

    @abstractmethod
    def fetch_results(self,
                      filename: str,
                      s_trees: etree.iterparse,
                      alignment_trees: Dict[str, List[Alignment]],
                      translation_trees: Dict[str, etree._ElementTree]) -> List[str]:
        """
        Fetches the results for a single file.
        """
        pass

    @abstractmethod
    def parse_alignment_trees(self, filename: str) -> Tuple[Dict[str, List[Alignment]],
                                                            Dict[str, etree._ElementTree]]:
        """
        Parses the alignment trees for a single file.
        """
        pass

    @abstractmethod
    def list_filenames(self, dir_name: str) -> List[str]:
        """
        List all to be processed files in the given directory.
        """
        pass

    @abstractmethod
    def get_translated_lines(self,
                             alignment_trees: Dict[str, List[Alignment]],
                             language_from: str,
                             language_to: str,
                             segment_number: str) -> List[str]:
        """
        Returns the translated segment numbers (could be multiple) for a segment number in the original text.
        """
        pass

    @abstractmethod
    def get_sentence(self, element: etree._Element) -> etree._Element:
        """
        Returns the full sentence XML for the given element.
        """
        pass

    @abstractmethod
    def get_siblings(self,
                     element: etree._Element,
                     sentence_id: Optional[str],
                     check_preceding: bool) -> List[etree._Element]:
        """
        Returns the siblings of the given element in the given sentence_id.
        The check_preceding parameter allows to look either forwards or backwards.
        """
        pass

    @abstractmethod
    def sort_by_alignment_certainty(self, file_names: List[str]) -> List[str]:
        """
        Sort files by their probability of having a correct sentence alignment.
        """
        pass

    @abstractmethod
    def filter_by_file_size(self, file_names: List[str]) -> List[str]:
        """
        Filter files based on file size, a minimum and maximum file size can be supplied.
        """
        pass

    @abstractmethod
    def get_type(self, sentence: etree._Element, mwe: Optional[MultiWordExpression] = None) -> str:
        """
        Return a classification for the sentence or the found MultiWordExpression.
        """
        pass

    @abstractmethod
    def mark_sentence(self, sentence: etree._Element, match: Optional[str] = None) -> str:
        """
        Mark the found match (if any) in the sentence.
        """
        pass
