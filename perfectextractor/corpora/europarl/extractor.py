# -*- encoding: utf-8 -*-

import os
import time

import click
from lxml import etree

from perfectextractor.apps.extractor.base import BaseExtractor
from perfectextractor.apps.extractor.models import Alignment, MARKUP
from perfectextractor.apps.extractor.perfectextractor import PerfectExtractor, PRESENT
from perfectextractor.apps.extractor.posextractor import PoSExtractor
from perfectextractor.apps.extractor.recentpastextractor import RecentPastExtractor
from perfectextractor.apps.extractor.xml_utils import get_sentence_from_element
from perfectextractor.apps.extractor.utils import XML

from .base import BaseEuroparl


class EuroparlExtractor(BaseEuroparl, BaseExtractor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._index = dict()  # save segments indexed by id

    def process_file(self, filename):
        """
        Processes a single file.
        """
        t0 = time.time()
        click.echo('Now processing {}...'.format(filename))

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag='s')

        # Parse the alignment and translation trees
        alignment_trees, translation_trees = self.parse_alignment_trees(filename)

        t1 = time.time()
        click.echo('Finished parsing trees, took {:.3} seconds'.format(t1 - t0))

        # Fetch the results
        results = self.fetch_results(filename, s_trees, alignment_trees, translation_trees)

        click.echo('Finished fetching results, took {:.3} seconds'.format(time.time() - t1))

        self._index = dict()  # free index memory
        return results

    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        """
        Fetches the results for a file
        :param filename: The current filename
        :param s_trees: The XML trees for all 's' elements in the file
        :param alignment_trees: The alignment XML trees, per target language
        :param translation_trees: The translation XML trees, per target language
        :return: All results in a list
        """
        results = list()
        # Loop over all sentences
        for _, s in s_trees:
            if self.sentence_ids and s.get('id') not in self.sentence_ids:
                continue

            result = list()
            result.append(os.path.basename(filename))
            result.append(s.get('id'))
            result.append('')
            result.append('')
            result.append('')
            if self.output == XML:
                result.append('<root>' + etree.tostring(s, encoding=str) + '</root>')
            else:
                result.append(self.get_sentence_words(s))
            self.append_metadata(None, s, result)

            for language_to in self.l_to:
                if language_to in translation_trees:
                    # TODO: deal with source_lines
                    source_lines, translated_lines, alignment_type = self.get_translated_lines(alignment_trees,
                                                                                               self.l_from,
                                                                                               language_to,
                                                                                               s.get('id'))
                    result.append(alignment_type)
                    if self.output == XML:
                        translated_sentences = [self.get_line(translation_trees[language_to], line) for line in translated_lines]
                        result.append('<root>' + '\n'.join(translated_sentences) + '</root>' if translated_sentences else '')
                    else:
                        translated_sentences = [self.get_line_as_xml(translation_trees[language_to], line) for line in translated_lines]
                        result.append('\n'.join([self.get_sentence_words(ts) for ts in translated_sentences]) if translated_sentences else '')
                else:
                    # If no translation is available, add empty columns
                    result.extend([''] * 2)

            results.append(result)
        return results

    def get_sentence_words(self, sentence, match=None):
        # TODO: this is copied from apps/models.py. Consider refactoring!
        s = []
        # TODO: this xPath-expression might be specific for a corpus
        for w in sentence.xpath('.//w'):
            if match is not None and w.get('id') == match.get('id'):
                s.append(MARKUP.format(w.text.strip()))
            else:
                s.append(w.text.strip() if w.text else ' ')
        return ' '.join(s)

    def get_line_by_number(self, tree, segment_number):
        """
        Returns the full line for a segment number.
        TODO: handle more than one here? => bug
        """
        result = None

        line = tree.xpath('//s[@id="' + segment_number + '"]')
        if line is not None:
            result = line[0]

        return result

    def get_sentence(self, element):
        return element.xpath('ancestor::s')[0]

    def get_siblings(self, element, sentence_id, check_preceding):
        siblings = element.xpath('ancestor::s//w')
        if check_preceding:
            siblings = siblings[:siblings.index(element)]
            siblings = siblings[::-1]
        else:
            siblings = siblings[siblings.index(element) + 1:]
        return siblings

    def _segment_by_id(self, tree, id):
        if tree not in self._index:
            self._index[tree] = dict()
            for segment in tree.xpath('//s'):
                self._index[tree][segment.get('id')] = segment
        return self._index[tree].get(id)

    def get_line_as_xml(self, tree, segment_number):
        return self._segment_by_id(tree, segment_number)

    def get_line(self, tree, segment_number):
        line = self._segment_by_id(tree, segment_number)
        if line is not None:
            return etree.tostring(line, encoding=str)
        else:
            return None

    def get_translated_lines(self, alignment_trees, language_from, language_to, segment_number):
        """
        Returns the translated segment numbers (could be multiple) for a segment number in the original text.

        Alignment lines in the Europarl corpus look like this:
            <linkGrp targType="s" fromDoc="en/ep-00-01-17.xml.gz" toDoc="nl/ep-00-01-17.xml.gz">
                <link xtargets="1;1" />
                <link xtargets="2;2 3" />
                <link xtargets="3;4 5" />
            </linkGrp>

        To get from language A to B, we should order the languages

        This function supports n-to-n alignments, as it will return both the source and translated lines as a list.
        """
        from_lines = []
        to_lines = []
        certainty = None

        sl = sorted([language_from, language_to])
        for alignment in alignment_trees[language_to]:
            if sl[0] == language_from:
                if segment_number in alignment.sources:
                    from_lines = alignment.sources
                    to_lines = alignment.targets
                    certainty = alignment.certainty
                    break
            else:
                if segment_number in alignment.targets:
                    from_lines = alignment.targets
                    to_lines = alignment.sources
                    certainty = alignment.certainty
                    break

        if not any(to_lines):
            to_lines = []

        alignment_str = '{} => {}'.format(len(from_lines), len(to_lines)) if to_lines else ''

        return from_lines, to_lines, alignment_str

    def parse_alignment_trees(self, filename, include_translations=True):
        data_folder = os.path.dirname(os.path.dirname(filename))

        # Cache the alignment XMLs on the first run
        if not self.alignment_xmls:
            for language_to in self.l_to:
                sl = sorted([self.l_from, language_to])
                alignment_file = os.path.join(data_folder, '-'.join(sl) + '.xml')
                if os.path.isfile(alignment_file):
                    alignment_tree = etree.parse(alignment_file)
                    self.alignment_xmls[language_to] = alignment_tree
                elif include_translations:
                    click.echo('No alignment file found for {} to {}'.format(filename, language_to))

        alignment_trees = dict()
        translation_trees = dict()
        for language_to in self.alignment_xmls.keys():
            sl = sorted([self.l_from, language_to])
            alignment_tree = self.alignment_xmls[language_to]
            base_filename = os.path.basename(filename)
            doc = '{}/{}'.format(self.l_from, base_filename)
            doc_gz = doc + '.gz'  # Europarl uses .gz natively, deal with both options
            path = '@fromDoc="{}"' if sl[0] == self.l_from else '@toDoc="{}"'
            linkGrps = alignment_tree.xpath('//linkGrp[{} or {}]'.format(path.format(doc), path.format(doc_gz)))

            if not linkGrps:
                if include_translations:
                    click.echo('No translation found for {} to {}'.format(filename, language_to))
            elif len(linkGrps) == 1:
                linkGrp = linkGrps[0]

                if include_translations:
                    translation_link = linkGrp.get('toDoc') if sl[0] == self.l_from else linkGrp.get('fromDoc')
                    if translation_link.endswith('.gz'):   # See comment above: Europarl uses .gz as extension
                        translation_link = translation_link[:-3]
                    translation_file = os.path.join(data_folder, translation_link)
                    translation_trees[language_to] = etree.parse(translation_file)

                alignments = []
                for link in linkGrp.xpath('./link'):
                    xtargets = link.get('xtargets').split(';')
                    sources = xtargets[0].split(' ')
                    targets = xtargets[1].split(' ')
                    certainty = link.get('certainty', None)
                    alignments.append(Alignment(sources, targets, certainty))

                alignment_trees[language_to] = alignments
            else:
                click.echo('Multiple translations found for {} to {}'.format(filename, language_to))

        return alignment_trees, translation_trees

    def average_alignment_certainty(self, alignment_trees):
        certainties_sum = 0
        certainties_len = 0
        for language, alignments in alignment_trees.items():
            certainties = [float(a.certainty) if a.certainty else 0 for a in alignments]
            certainties_sum += sum(certainties)
            certainties_len += len(certainties)

        return certainties_sum / float(certainties_len) if certainties_len > 0 else 0

    def sort_by_alignment_certainty(self, file_names):
        certainties = dict()
        for file_name in file_names:
            alignment_trees, _ = self.parse_alignment_trees(file_name, include_translations=False)
            if len(alignment_trees) == len(self.l_to):  # Only add files that have translations in all languages
                certainties[file_name] = self.average_alignment_certainty(alignment_trees)

        sorted_by_value = sorted(certainties.items(), key=lambda kv: kv[1], reverse=True)
        return [f[0] for f in sorted_by_value]

    def filter_by_file_size(self, file_names):
        results = []
        for file_name in file_names:
            file_size = etree.parse(file_name).xpath('count(//s)')
            if self.min_file_size <= file_size <= self.max_file_size:
                results.append(file_name)

        return results

    def list_directories(self, path):
        return filter(lambda x: x.endswith(self.l_from), super(EuroparlExtractor, self).list_directories(path))


class EuroparlPoSExtractor(EuroparlExtractor, PoSExtractor):
    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        """
        Processes a single file.
        """
        results = []

        # Find potential words matching the part-of-speech
        pos_attr = self.config.get(self.l_from, 'pos')
        lemma_attr = self.config.get('all', 'lemma_attr')
        ns = {}
        predicate = 'contains(" {value} ", concat(" ", @{element}, " "))'
        predicates = []

        if self.lemmata_list:
            predicates.append(predicate.format(element=lemma_attr, value=' '.join(self.lemmata_list)))

        if self.tokens:
            predicates.append(predicate.format(element='id', value=' '.join(self.tokens.keys())))

        if self.pos:
            predicates.append(predicate.format(element=pos_attr, value=' '.join(self.pos)))

        if self.regex:
            # prepare a pattern that combines multiple regexps using OR operators
            # and non-capturing groups
            pattern = '|'.join('(?:{})'.format(r) for r in self.regex)

            # special namespace required for enabling regular expresssion functions
            ns = {"re": "http://exslt.org/regular-expressions"}
            predicates.append('re:test(., "{pattern}", "i")'.format(pattern=pattern))

        xpath = './/w'
        if predicates:
            xpath = './/w[{}]'.format(' and '.join(predicates))

        for _, s in s_trees:
            if self.sentence_ids and s.get('id') not in self.sentence_ids:
                continue

            for w in s.xpath(xpath, namespaces=ns):
                words = self.preprocess_found(w)

                if not words:
                    continue

                result = list()
                result.append(os.path.basename(filename))
                result.append(s.get('id'))
                result.append(self.get_type(words))
                result.append(' '.join([w.text for w in words]))
                result.append(' '.join([w.get('id') for w in words]))
                if self.output == XML:
                    result.append('<root>' + etree.tostring(s, encoding=str) + '</root>')
                else:
                    result.append(self.get_sentence_words(s, w))
                self.append_metadata(w, s, result)

                # Find the translated lines
                for language_to in self.l_to:
                    if language_to in translation_trees:
                        # TODO: deal with source_lines
                        source_lines, translated_lines, alignment_type = self.get_translated_lines(alignment_trees,
                                                                                                   self.l_from,
                                                                                                   language_to,
                                                                                                   s.get('id'))
                        result.append(alignment_type)
                        if self.output == XML:
                            translated_sentences = [self.get_line(translation_trees[language_to], line) for line in translated_lines]
                            result.append('<root>' + '\n'.join(translated_sentences) + '</root>' if translated_sentences else '')
                        else:
                            translated_sentences = [self.get_line_as_xml(translation_trees[language_to], line) for line in translated_lines]
                            result.append('\n'.join([self.get_sentence_words(ts) for ts in translated_sentences]) if translated_sentences else '')
                    else:
                        # If no translation is available, add empty columns
                        result.extend([''] * 2)

                results.append(result)

        return results

    def preprocess_found(self, word):
        """
        Preprocesses the found word:
        - removes a word if it does not occur in the lemmata list
        - removes a word if it is not in the correct position in the sentence
        Returns the found word as a list, as it might be interesting to include words before and after
        (see e.g. EuroparlFrenchArticleExtractor)
        """
        result = [word]

        lemma_attr = self.config.get('all', 'lemma_attr')
        if self.lemmata_list and word.get(lemma_attr) not in self.lemmata_list:
            result = []

        if self.position and not word.get('id').endswith('.' + str(self.position)):
            result = []

        if self.tokens:
            end_token = self.tokens.get(word.get('id'))
            next_word = word.getnext()
            if next_word is None:
                raise ValueError('End token {} not found'.format(end_token))
            else:
                while next_word.get('id') != end_token:
                    result.append(next_word)

                    next_word = next_word.getnext()
                    if next_word is None:
                        raise ValueError('End token {} not found'.format(end_token))
                else:
                    result.append(next_word)

        return result


class EuroparlFrenchArticleExtractor(EuroparlPoSExtractor):
    def __init__(self, language_from, languages_to):
        """
        Initializes the EuroparlFrenchArticleExtractor with a set of part-of-speeches and lemmata that the found
        words should adhere to. Also initializes a list of particles that could appear before a determiner.
        :param language_from: The language to find the specified part-of-speeches in.
        :param languages_to: The languages to extract the aligned sentences from.
        """
        super(EuroparlFrenchArticleExtractor, self).__init__(language_from, languages_to, ['DET:ART', 'PRP:det'])

        self.lemmata_list = ['le', 'un', 'du']
        self.particles = ['de', 'du']

    def preprocess_found(self, word):
        """
        Removes a word if does not occur in the lemmata list, and then checks if it might be preceded by a particle.
        If so, add the particle to the found words.
        """
        result = []

        lemma_attr = self.config.get('all', 'lemma_attr')
        for w in super(EuroparlFrenchArticleExtractor, self).preprocess_found(word):
            prev = w.getprevious()
            if prev is not None and prev.get(lemma_attr) in self.particles:
                result.append(prev)

            result.append(word)

        return result

    def get_type(self, words):
        """
        Return the type for a found article: definite, indefinite or partitive.
        For 'des', this is quite hard to decide, so we leave both options open.
        """
        result = ''
        lemma_attr = self.config.get('all', 'lemma_attr')

        if words[-1].get(lemma_attr) == 'le':
            result = 'definite'
        elif words[-1].get(lemma_attr) == 'un':
            result = 'indefinite'

        if words[0].get(lemma_attr) in self.particles:
            if result:
                result += ' '
            result += 'partitive'

        if words[0].text == 'des':
            result = 'indefinite/partitive'

        return result


class EuroparlSinceDurationExtractor(EuroparlPoSExtractor):
    def __init__(self, language_from, languages_to, **kwargs):
        """
        Initializes the EuroparlSinceDurationExtractor with a set of lemmata, part-of-speech for numbers,
        and time units, so that it should find [seit] + [number] + [unit of time].
        :param language_from: The language to find the specified part-of-speeches in.
        :param languages_to: The languages to extract the aligned sentences from.
        """
        super(EuroparlPoSExtractor, self).__init__(language_from, languages_to, **kwargs)

        self.lemmata_list = self.config.get(self.l_from, 'since_lem').split(',')
        self.number_pos = self.config.get(self.l_from, 'since_number_pos').split(',')
        self.time_units = self.config.get(self.l_from, 'since_time_units').split(',')

    def preprocess_found(self, word):
        """
        Removes a word if does not occur in the lemmata list, and then checks if it might be preceded by a particle.
        If so, add the particle to the found words.
        """
        result = []

        lemma_attr = self.config.get('all', 'lemma_attr')
        pos_attr = self.config.get(self.l_from, 'pos')

        for w in super(EuroparlSinceDurationExtractor, self).preprocess_found(word):
            result.append(word)

            next_word = w.getnext()
            if next_word is not None and next_word.get(pos_attr) in self.number_pos:
                result.append(next_word)
            else:
                result = None
                continue

            next_word2 = next_word.getnext()
            if next_word2 is not None and next_word2.get(lemma_attr) in self.time_units:
                result.append(next_word2)
            else:
                result = None
                continue

        return result


class EuroparlRecentPastExtractor(EuroparlExtractor, RecentPastExtractor):
    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        """
        Processes a single file.
        """
        results = []
        # Find potential recent pasts (per sentence)
        for _, s in s_trees:
            if self.sentence_ids and s.get('id') not in self.sentence_ids:
                continue

            for w in s.xpath(self.config.get(self.l_from, 'rp_xpath')):
                rp = self.check_recent_past(w, self.l_from)

                if rp:
                    result = list()
                    result.append(os.path.basename(filename))
                    result.append(s.get('id'))
                    result.append(u'passé récent')
                    result.append(rp.verbs_to_string())
                    result.append(rp.verb_ids())
                    result.append('<root>' + etree.tostring(rp.xml_sentence, encoding=str) + '</root>')
                    self.append_metadata(w, s, result)

                    found_trans = False
                    for language_to in self.l_to:
                        if language_to in translation_trees:
                            # TODO: deal with source_lines
                            source_lines, translated_lines, alignment_type = self.get_translated_lines(alignment_trees,
                                                                                                       self.l_from,
                                                                                                       language_to,
                                                                                                       s.get('id'))
                            if translated_lines:
                                translated_sentences = [self.get_line(translation_trees[language_to], line) for line in
                                                        translated_lines]
                                translated_sentences_xml = [self.get_line_as_xml(translation_trees[language_to], line) for line in
                                                            translated_lines]

                                if language_to == 'fr':
                                    for ts in translated_sentences_xml:
                                        for e in ts.xpath(self.config.get(language_to, 'rp_xpath')):
                                            rp = self.check_recent_past(e, language_to)
                                            if rp:
                                                found_trans = True

                                result.append(alignment_type)
                                result.append('<root>' + '\n'.join(translated_sentences) + '</root>' if translated_sentences else '')
                            else:
                                result.append('')
                                result.append('')
                        else:
                            # If no translation is available, add empty columns
                            result.extend([''] * 2)

                    if not found_trans:
                        results.append(result)

        return results

    def get_sentence_words(self, xml_sentence):
        s = []
        # TODO: this xPath-expression might be specific for a corpus
        for w in xml_sentence.xpath('.//w'):
            s.append(w.text.strip() if w.text else ' ')
        return ' '.join(s)


class EuroparlPerfectExtractor(EuroparlExtractor, PerfectExtractor):
    def get_line_and_pp(self, tree, language_to, segment_number):
        """
        Returns the full line for a segment number, as well as the PresentPerfect found (or None if none found).
        TODO: handle more than one here? => bug
        """
        sentence = '-'
        pp = None

        line = self.get_line_as_xml(tree, segment_number)
        if line is not None:
            s = line
            first_w = s.xpath('.//w')[0]
            sentence = get_sentence_from_element(first_w)

            if self.search_in_to:
                for e in s.xpath(self.config.get(language_to, 'xpath')):
                    pp = self.check_perfect(e, language_to)
                    if pp:
                        sentence = pp.mark_sentence()
                        break

        return etree.tostring(s, encoding=str), sentence, pp

    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        """
        Processes a single file.
        """
        results = []
        # Find potential present/past perfects (per sentence)
        for _, s in s_trees:
            if self.sentence_ids and s.get('id') not in self.sentence_ids:
                continue

            # Retrieves the xpath expression for the auxiliary in the given tense or a fallback
            xpath_fallback = 'xpath'
            xpath = xpath_fallback + ('_{}'.format(self.tense) if self.tense != PRESENT else '')
            l_config = dict(self.config.items(self.l_from))
            aux_xpath = l_config.get(xpath, l_config.get(xpath_fallback))

            for e in s.xpath(aux_xpath):
                pp = self.check_perfect(e, self.l_from)

                # apply position filter
                if self.position and not e.get('id').endswith('.' + str(self.position)):
                    continue

                # If this is really a present/past perfect, add it to the result
                if pp:
                    result = list()
                    result.append(os.path.basename(filename))
                    result.append(s.get('id'))
                    result.append(pp.perfect_type())
                    result.append(pp.verbs_to_string())
                    result.append(pp.verb_ids())
                    if self.output == XML:
                        result.append('<root>' + etree.tostring(pp.xml_sentence, encoding=str) + '</root>')
                    else:
                        result.append(pp.mark_sentence())
                    self.append_metadata(e, s, result)

                    # Find the translated lines
                    for language_to in self.l_to:
                        if language_to in translation_trees:
                            # TODO: deal with source_lines
                            source_lines, translated_lines, alignment_type = self.get_translated_lines(alignment_trees,
                                                                                                       self.l_from,
                                                                                                       language_to,
                                                                                                       s.get('id'))
                            translated_present_perfects, translated_sentences, translated_marked_sentences = \
                                self.find_translated_present_perfects(translation_trees[language_to], language_to, translated_lines)
                            result.append(alignment_type)
                            if self.output == XML:
                                result.append('<root>' + '\n'.join(translated_sentences) + '</root>' if translated_sentences else '')
                            else:
                                result.append('\n'.join(translated_marked_sentences) if translated_marked_sentences else '')
                        else:
                            # If no translation is available, add empty columns
                            result.extend([''] * 2)

                    results.append(result)

                    # If we want (only) one classification per sentence, break the for loop here.
                    if self.one_per_sentence:
                        break
            else:
                # If we want one classification per sentence, add the sentence with a classification here.
                if self.one_per_sentence:
                    tense, tenses = self.get_tenses(s)

                    result = list()
                    result.append(os.path.basename(filename))
                    result.append(s.get('id'))
                    result.append(tense)
                    result.append(','.join(tenses))
                    result.append('')
                    result.append(self.get_sentence_words(s))
                    self.append_metadata(None, s, result)
                    results.append(result)

        return results
