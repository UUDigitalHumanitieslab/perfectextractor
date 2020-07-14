# -*- encoding: utf-8 -*-

from abc import ABCMeta, abstractmethod
import codecs
import string
import os

from .base import BaseExtractor
from .models import Perfect
from .wiktionary import get_translations

# List of verbs that have BE instead of HAVE as their auxiliary
AUX_BE_CONFIG = os.path.join(os.path.dirname(__file__), 'config/{language}_aux_be.txt')

# Tenses
PRESENT = 'present'
PAST = 'past'
# FUTURE = 'future'  # TODO: implement this somewhere in the near future


class PerfectExtractor(BaseExtractor):
    __metaclass__ = ABCMeta

    def __init__(self, language_from, languages_to=None, search_in_to=False, tense=PRESENT, **kwargs):
        """
        Initializes the PerfectExtractor for the given source and target language(s).
        Reads in the config for the source language,
        as well as the list of verbs that use 'to be' as auxiliary verb for both source and target language(s).
        :param language_from: the source language
        :param languages_to: the target language(s)
        :param search_in_to: whether to look for perfects in the target language
        :param tense: whether to search for present, past or future perfects
        """
        super(PerfectExtractor, self).__init__(language_from, languages_to, **kwargs)

        self.search_in_to = search_in_to
        self.tense = tense

        # Read the list of verbs that use 'to be' as auxiliary verb per language
        self.aux_be_list = {}
        languages = [self.l_from]
        if search_in_to:
            languages.extend(self.l_to)
        for language in languages:
            aux_be_list = []
            if self.config.get(language, 'lexical_bound'):
                with codecs.open(AUX_BE_CONFIG.format(language=language), 'r', 'utf-8') as lexicon:
                    aux_be_list = lexicon.read().split()
            self.aux_be_list[language] = aux_be_list

    @abstractmethod
    def get_line_and_pp(self, tree, language_to, segment_number):
        """
        Returns the full line for a segment number, as well as the PresentPerfect found (or None if none found)
        """
        raise NotImplementedError

    def is_lexically_bound(self, language, pp, aux_verb, past_participle, w_before=None):
        """
        Checks if the perfect is lexically bound to the auxiliary verb.
        If not, we are not dealing with a Perfect here.
        """
        lemma_attr = self.config.get('all', 'lemma_attr')
        aux_be = self.config.get(language, 'lexical_bound')

        # If lexical bounds do not exist or we're dealing with an auxiliary verb that is unbound, return True
        # Note: we check with "not in", because in French the lemma can be e.g. 'suivre|être'
        if not aux_be or aux_be not in aux_verb.get(lemma_attr):
            return True

        # Else, check if we are dealing with a reflexive Perfect (in that case, there is no lexical bound)
        if self.is_reflexive(language, w_before):
            pp.prepend_word(w_before[0].text, w_before[0].get(lemma_attr), True, w_before[0].get('id'))
            pp.is_reflexive = True
            return True

        # Finally, check whether the past participle is in the list of bound verbs
        return past_participle.get(lemma_attr) in self.aux_be_list[language]

    def is_reflexive(self, language, w_before):
        """
        Check whether we are dealing with a reflexive Perfect
        """
        lemma_attr = self.config.get('all', 'lemma_attr')
        reflexive_lemmata = self.config.get(language, 'reflexive_lemmata').split(',')

        precondition = reflexive_lemmata and w_before is not None and len(w_before) >= 2
        if precondition:
            prev_reflexive = w_before[0].get(lemma_attr) in reflexive_lemmata
            # TODO: below condition is language-specific, and does not yet work for e.g. negation
            prevprev_pronoun = w_before[0].get(lemma_attr) not in ['nous', 'vous'] or self.get_pos(language, w_before[1]) == 'PRO:PER'
            return prev_reflexive and prevprev_pronoun
        else:
            return False

    def check_perfect(self, auxiliary, language, check_ppp=True, check_ppc=False, check_preceding=False):
        """
        Checks whether this element (i.e. the auxiliary) is the start of a Perfect (pp),
        a Perfect continuous (ppc) or passive Perfect (ppp).
        If it is, the complete construction is returned as a Perfect object.
        If not, None is returned.
        """
        lemma_attr = self.config.get('all', 'lemma_attr')
        perfect_tags = self.config.get(language, 'perfect_tags').split(',')
        check_ppp = check_ppp and self.config.getboolean(language, 'ppp')
        ppp_lemma = self.config.get(language, 'ppp_lemma')
        check_ppc = check_ppc and self.config.getboolean(language, 'ppc')
        ppc_tags = self.config.get(language, 'ppc_tags').split(',')
        stop_tags = tuple(self.config.get(language, 'stop_tags').split(','))
        allow_reversed = self.config.getboolean(language, 'allow_reversed')

        # Retrieves the auxiliaries, or a fallback if there are none provided
        aux_fallback = 'aux_words'
        aux = aux_fallback + ('_{}'.format(self.tense) if self.tense != PRESENT else '')
        l_config = dict(self.config.items(language))  # In Python 3, we could consider self.config[language] instead.
        aux_words = l_config.get(aux, l_config.get(aux_fallback)).split(',')

        # Start a potential Perfect
        s = self.get_sentence(auxiliary)
        pp = Perfect(auxiliary.text, auxiliary.get(lemma_attr), auxiliary.get('id'), s)
        is_pp = False

        # Check if the starting auxiliary is actually allowed
        if any(aux_words) and auxiliary.text.lower() not in aux_words:
            return None

        # Loop over the siblings of the current element.
        siblings = self.get_siblings(auxiliary, s.get('id'), check_preceding)
        for n, sibling in enumerate(siblings):
            # If the tag of the sibling is the perfect tag, we found a Perfect!
            sibling_pos = self.get_pos(language, sibling)
            sibling_lemma = sibling.get(lemma_attr)
            if sibling_pos in perfect_tags:
                # Check if the sibling is lexically bound to the auxiliary verb
                # (only if we're not checking for passive Perfect)
                before = self.get_siblings(auxiliary, s.get('id'), not check_preceding)
                if check_ppp and not self.is_lexically_bound(language, pp, auxiliary, sibling, before):
                    break

                # Check if the lemma is not in the lemmata list, if so break, unless we found a potential ppp
                if not self.in_lemmata_list(sibling_lemma):
                    if not(check_ppp and sibling_lemma == ppp_lemma):
                        break

                pp.add_word(sibling.text, sibling_lemma, True, sibling.get('id'))
                is_pp = True

                # ... now check whether this is a passive Perfect or Perfect continuous (by recursion)
                if check_ppp and sibling_lemma == ppp_lemma:
                    ppp = self.check_perfect(sibling,
                                             language,
                                             check_ppp=False,
                                             check_ppc=True,
                                             check_preceding=check_preceding)
                    if ppp:
                        pp.extend(ppp)
                    elif not self.in_lemmata_list(sibling_lemma):
                        is_pp = False
                break
            # Check if this is a Perfect continuous (in the recursion step)
            elif check_ppc and sibling_pos in ppc_tags and self.in_lemmata_list(sibling_lemma):
                pp.add_word(sibling.text, sibling_lemma, True, sibling.get('id'))
                pp.is_continuous = True
                is_pp = True
                break
            # Stop looking at punctuation or stop tags
            elif (sibling.text and sibling.text in string.punctuation) or (sibling_pos and sibling_pos.startswith(stop_tags)):
                break
            # We didn't break yet? Then add this sibling as a potential non-verb part of the Perfect.
            else:
                pp.add_word(sibling.text, sibling_lemma, False, sibling.get('id'))

        # If we haven't yet found a past participle, and we are allowed to look in the other direction,
        # try to find a past participle by looking backwards in the sentence.
        if not is_pp and allow_reversed and not check_preceding:
            pp = self.check_perfect(auxiliary, language, check_ppp=check_ppp, check_preceding=True)
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
        Finds Perfects in translated sentences.
        """
        translated_pps = []
        translated_sentences = []
        translated_marked_sentences = []

        if translated_lines and any(translated_lines):
            for t in translated_lines:
                sentence, translation, translated_pp = self.get_line_and_pp(translated_tree, language_to, t)
                translated_pps.append(translated_pp)
                translated_sentences.append(sentence)
                translated_marked_sentences.append(translation)

        return translated_pps, translated_sentences, translated_marked_sentences

    def check_translated_pps(self, pp, translated_present_perfects, language_to):
        """
        Checks whether the translated Perfects found form an actual translation of the Perfect.
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
