from abc import ABCMeta, abstractmethod
import ConfigParser
import codecs
import string
import os

from .utils import UnicodeWriter
from .models import PresentPerfect
from .wiktionary import get_translations

AUX_BE_CONFIG = os.path.join(os.path.dirname(__file__), '../config/{language}_aux_be.txt')
TEI = {'ns': 'http://www.tei-c.org/ns/1.0'}
NL = 'nl'


class PerfectExtractor(object):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to):
        """
        Initializes the extractor for the given source and target language(s).
        Reads in the config for the source language,
        as well as the list of verbs that use 'to be' as auxiliary verb for both source and target language(s).
        """
        self.l_from = language_from
        self.l_to = languages_to

        # Read the config
        config = ConfigParser.RawConfigParser()
        config.readfp(codecs.open(self.get_config(), 'r', 'utf8'))
        self.config = config

        # Read the list of verbs that use 'to be' as auxiliary verb per language
        self.aux_be_list = {}
        for language in [language_from] + languages_to:
            aux_be_list = []
            if self.config.get(language, 'lexical_bound'):
                with codecs.open(AUX_BE_CONFIG.format(language=language), 'rb', 'utf-8') as lexicon:
                    aux_be_list = lexicon.read().split()
            self.aux_be_list[language] = aux_be_list

    @abstractmethod
    def get_config(self):
        """
        Returns the location of the configuration file.
        """
        raise NotImplementedError

    @abstractmethod
    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        """
        Returns the translated segment numbers (could be multiple) for a segment number in the original text.
        """
        raise NotImplementedError

    @abstractmethod
    def get_line_by_number(self, tree, language_to, segment_number):
        """
        Returns the full line for a segment number, as well as the PresentPerfect found (or None if none found).
        TODO: handle more than one here? => bug
        """
        raise NotImplementedError

    def is_lexically_bound(self, language, aux_verb, perfect):
        """
        Checks if the perfect is lexically bound to the auxiliary verb.
        If not, we are not dealing with a present perfect here.
        """
        lemma_attr = self.config.get('all', 'lemma_attr')
        aux_be = self.config.get(language, 'lexical_bound')

        # If lexical bounds do not exist or we're dealing with an auxiliary verb that is unbound, return True
        if not aux_be or aux_verb.get(lemma_attr) != aux_be:
            return True
        # Else, check whether the perfect is in the list of bound verbs
        else:
            return perfect.get(lemma_attr) in self.aux_be_list[language]

    def check_present_perfect(self, element, language, check_ppc=True, check_preceding=False):
        """
        Checks whether this element is the start of a present perfect (or pp continuous).
        If it is, the present perfect is returned as a list.
        If not, None is returned.
        """
        lemma_attr = self.config.get('all', 'lemma_attr')
        perfect_tag = self.config.get(language, 'perfect_tag')
        check_ppc = check_ppc and self.config.getboolean(language, 'ppc')
        ppc_lemma = self.config.get(language, 'ppc_lemma')
        stop_tags = tuple(self.config.get(language, 'stop_tags').split(','))
        allow_reversed = self.config.getboolean(language, 'allow_reversed')
        pos_tag = self.config.get(language, 'pos')

        # Start a potential present perfect
        s = self.get_sentence(element)
        pp = PresentPerfect(element.text, element.get(lemma_attr), element.get('id'), s)
        is_pp = False

        # Loop over the siblings of the current element.
        for sibling in self.get_siblings(element, s.get('id'), check_preceding):
            # If the tag of the sibling is the perfect tag, we found a present perfect!
            sibling_pos = sibling.get(pos_tag)
            if sibling_pos == perfect_tag:
                # Check if the sibling is lexically bound to the auxiliary verb
                # (only if we're not checking for present perfect continuous)
                if check_ppc and not self.is_lexically_bound(language, element, sibling):
                    break
                pp.add_word(sibling.text, sibling.get(lemma_attr), True, sibling.get('id'))
                is_pp = True
                # ... now check whether this is a present perfect continuous (by recursion)
                if check_ppc and sibling.get(lemma_attr) == ppc_lemma:
                    ppc = self.check_present_perfect(sibling, language, False)
                    if ppc:
                        pp.extend(ppc)
                break
            # Stop looking at punctuation or stop tags
            elif sibling.text in string.punctuation or (sibling_pos and sibling_pos.startswith(stop_tags)):
                break
            # We didn't break yet? Then add this sibling as a potential non-verb part of the present perfect.
            else:
                pp.add_word(sibling.text, sibling.get(lemma_attr), False, sibling.get('id'))

        # If we haven't yet found a perfect, and we are allowed to look in the other direction,
        # try to find a perfect by looking backwards in the sentence.
        if not is_pp and allow_reversed and not check_preceding:
            pp = self.check_present_perfect(element, language, check_ppc, True)
            if pp:
                is_pp = True

        return pp if is_pp else None

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

    def find_translated_present_perfects(self, translated_tree, language_to, translated_lines):
        """
        Finds present perfects in translated sentences.
        """
        translated_pps = []
        translated_sentences = []
        translated_marked_sentences = []

        if translated_lines and any(translated_lines):
            for t in translated_lines:
                sentence, translation, translated_pp = self.get_line_by_number(translated_tree, language_to, t)
                translated_pps.append(translated_pp)
                translated_sentences.append(sentence)
                translated_marked_sentences.append(translation)

        return translated_pps, translated_sentences, translated_marked_sentences

    def process_folder(self, dir_name):
        """
        Creates a result file and processes each file in a folder.
        """
        result_file = '-'.join([dir_name, self.l_from]) + '.csv'
        with open(result_file, 'wb') as f:
            f.write(u'\uFEFF'.encode('utf-8'))  # the UTF-8 BOM to hint Excel we are using that...
            csv_writer = UnicodeWriter(f, delimiter=';')

            header = [
                'document',
                'original_language',
                'present perfect ' + self.l_from,
                'present perfect ids',
                'xml',
                self.l_from]
            for language in self.l_to:
                header.append('present perfect ' + language)
                header.append('is translation?')
                header.append('alignment type')
                header.append('xml')
                header.append(language)
            csv_writer.writerow(header)

            for filename in self.list_filenames(dir_name):
                results = self.process_file(filename)
                csv_writer.writerows(results)

    @abstractmethod
    def list_filenames(self, dir_name):
        """
        List all to be processed files in the given directory.
        """
        raise NotImplementedError

    def check_translated_pps(self, pp, translated_present_perfects, language_to):
        """
        Checks whether the translated present perfects found form an actual translation of the present perfect.
        """
        results = []
        for tpp in translated_present_perfects:
            if tpp:
                translations = get_translations(pp.perfect_lemma(), self.l_from, language_to)
                if tpp.perfect_lemma() in translations:
                    results.append('yes')
                else:
                    results.append('unknown')
        return results

    @abstractmethod
    def process_file(self, filename):
        """
        Processes a single file, given by the filename.
        """
        raise NotImplementedError