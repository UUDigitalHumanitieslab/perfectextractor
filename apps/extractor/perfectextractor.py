from abc import ABCMeta, abstractmethod
import ConfigParser
import codecs
import string
import os

from .base import BaseExtractor
from .models import PresentPerfect
from .utils import TXT
from .wiktionary import get_translations

AUX_BE_CONFIG = os.path.join(os.path.dirname(__file__), 'config/{language}_aux_be.txt')

TEI = {'ns': 'http://www.tei-c.org/ns/1.0'}


class PerfectExtractor(BaseExtractor):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to=None, search_in_to=False, sentence_ids=None, output=TXT, lemmata=None):
        """
        Initializes the extractor for the given source and target language(s).
        Reads in the config for the source language,
        as well as the list of verbs that use 'to be' as auxiliary verb for both source and target language(s).
        :param language_from: the source language
        :param languages_to: the target language(s)
        :param search_in_to: whether to look for perfects in the target language
        :param lemmata: whether to limit the search to certain lemmata (can be provided as a boolean or a list)
        """
        super(PerfectExtractor, self).__init__(language_from, languages_to, sentence_ids=sentence_ids, output=output)

        self.search_in_to = search_in_to

        # Read the config
        config = ConfigParser.RawConfigParser()
        config.readfp(codecs.open(self.get_config(), 'r', 'utf8'))
        self.config = config

        # Read the list of verbs that use 'to be' as auxiliary verb per language
        self.aux_be_list = {}
        languages = [self.l_from]
        if search_in_to:
            languages.extend(self.l_to)
        for language in languages:
            aux_be_list = []
            if self.config.get(language, 'lexical_bound'):
                with codecs.open(AUX_BE_CONFIG.format(language=language), 'rb', 'utf-8') as lexicon:
                    aux_be_list = lexicon.read().split()
            self.aux_be_list[language] = aux_be_list

        # Read in the lemmata list (if provided)
        self.read_lemmata(lemmata)

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

    def check_present_perfect(self, element, language, check_ppp=True, check_ppc=False, check_preceding=False):
        """
        Checks whether this element is the start of a present perfect (pp),
        a present perfect continuous (ppc) or passive present perfect (ppp).
        If it is, the complete construction is returned as a PresentPerfect object.
        If not, None is returned.
        """
        lemma_attr = self.config.get('all', 'lemma_attr')
        aux_words = self.config.get(language, 'aux_words').split(',')
        perfect_tags = self.config.get(language, 'perfect_tags').split(',')
        check_ppp = check_ppp and self.config.getboolean(language, 'ppp')
        ppp_lemma = self.config.get(language, 'ppp_lemma')
        check_ppc = check_ppc and self.config.getboolean(language, 'ppc')
        ppc_tags = self.config.get(language, 'ppc_tags').split(',')
        stop_tags = tuple(self.config.get(language, 'stop_tags').split(','))
        allow_reversed = self.config.getboolean(language, 'allow_reversed')
        pos_tag = self.config.get(language, 'pos')

        # Start a potential present perfect
        s = self.get_sentence(element)
        pp = PresentPerfect(element.text, element.get(lemma_attr), element.get('id'), s)
        is_pp = False

        # Check if the starting auxiliary is actually allowed
        if any(aux_words) and element.text not in aux_words:
            return None

        # Loop over the siblings of the current element.
        for sibling in self.get_siblings(element, s.get('id'), check_preceding):
            # If the tag of the sibling is the perfect tag, we found a present perfect!
            sibling_pos = sibling.get(pos_tag)
            sibling_lemma = sibling.get(lemma_attr)
            if sibling_pos in perfect_tags:
                # Check if the sibling is lexically bound to the auxiliary verb
                # (only if we're not checking for passive present perfect)
                if check_ppp and not self.is_lexically_bound(language, element, sibling):
                    break

                # Check if the lemma is not in the lemmata list, if so break, unless we found a potential ppp
                if not self.in_lemmata_list(sibling_lemma):
                    if not(check_ppp and sibling_lemma == ppp_lemma):
                        break

                pp.add_word(sibling.text, sibling_lemma, True, sibling.get('id'))
                is_pp = True

                # ... now check whether this is a passive present perfect or present perfect continuous (by recursion)
                if check_ppp and sibling_lemma == ppp_lemma:
                    ppp = self.check_present_perfect(sibling,
                                                     language,
                                                     check_ppp=False,
                                                     check_ppc=True,
                                                     check_preceding=check_preceding)
                    if ppp:
                        pp.extend(ppp)
                    elif not self.in_lemmata_list(sibling_lemma):
                        is_pp = False
                break
            # Check if this is a present perfect continuous (in the recursion step)
            elif check_ppc and sibling_pos in ppc_tags and self.in_lemmata_list(sibling_lemma):
                pp.add_word(sibling.text, sibling_lemma, True, sibling.get('id'))
                pp.is_continuous = True
                is_pp = True
                break
            # Stop looking at punctuation or stop tags
            elif (sibling.text and sibling.text in string.punctuation) or (sibling_pos and sibling_pos.startswith(stop_tags)):
                break
            # We didn't break yet? Then add this sibling as a potential non-verb part of the present perfect.
            else:
                pp.add_word(sibling.text, sibling_lemma, False, sibling.get('id'))

        # If we haven't yet found a perfect, and we are allowed to look in the other direction,
        # try to find a perfect by looking backwards in the sentence.
        if not is_pp and allow_reversed and not check_preceding:
            pp = self.check_present_perfect(element, language, check_ppp=check_ppp, check_preceding=True)
            if pp:
                is_pp = True

        return pp if is_pp else None

    def in_lemmata_list(self, element):
        """
        Returns whether the given element is in the lemmata list.
        Returns True when there is no lemmata list given.
        """
        return not self.lemmata_list or element in self.lemmata_list

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
