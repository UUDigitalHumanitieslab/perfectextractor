# -*- encoding: utf-8 -*-

import os
import time

from lxml import etree

from apps.extractor.base import BaseExtractor
from apps.extractor.perfectextractor import PerfectExtractor
from apps.extractor.posextractor import PoSExtractor
from apps.extractor.recentpastextractor import RecentPastExtractor
from apps.extractor.xml_utils import get_sentence_from_element

from .base import BaseEuroparl


class EuroparlExtractor(BaseEuroparl, BaseExtractor):
    def process_file(self, filename):
        """
        Processes a single file.
        """
        t0 = time.time()
        print 'Now processing ' + filename + '...'

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag='s')

        # Parse the alignment and translation trees
        alignment_trees, translation_trees = self.parse_alignment_trees(filename)

        t1 = time.time()
        print 'Finished parsing trees, took {:.3} seconds'.format(t1 - t0)

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
            result.append('<root>' + etree.tostring(s) + '</root>')

            for language_to in self.l_to:
                if language_to in translation_trees:
                    # TODO: deal with source_lines
                    source_lines, translated_lines, alignment_type = self.get_translated_lines(alignment_trees,
                                                                                               self.l_from,
                                                                                               language_to,
                                                                                               s.get('id'))
                    translated_sentences = [self.get_line(translation_trees[language_to], line) for line in translated_lines]
                    result.append(alignment_type)
                    result.append('<root>' + '\n'.join(translated_sentences) + '</root>' if translated_sentences else '')
                else:
                    # If no translation is available, add empty columns
                    result.extend([''] * 2)

            results.append(result)

        print 'Finished, took {:.3} seconds'.format(time.time() - t1)

        return results

    def get_line_by_number(self, tree, segment_number):
        """
        Returns the full line for a segment number.
        TODO: handle more than one here? => bug
        """
        result = None

        line = tree.xpath('//s[@id="' + segment_number + '"]')
        if line:
            result = line[0]

        return result

    def get_sentence(self, element):
        return element.xpath('ancestor::s')[0]

    def get_siblings(self, element, sentence_id, check_preceding):
        path = ('preceding' if check_preceding else 'following') + '::w[ancestor::s[@id="' + sentence_id + '"]]'
        siblings = element.xpath(path)
        if check_preceding:
            siblings = siblings[::-1]
        return siblings

    def get_line_as_xml(self, tree, segment_number):
        line = tree.xpath('//s[@id="' + segment_number + '"]')
        if line:
            return line[0]
        else:
            return None

    def get_line(self, tree, segment_number):
        line = tree.xpath('//s[@id="' + segment_number + '"]')
        if line:
            return etree.tostring(line[0])
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

        sl = sorted([language_from, language_to])
        for xtargets in alignment_trees[language_to]:
            if sl[0] == language_from:
                if segment_number in xtargets[0]:
                    from_lines = xtargets[0]
                    to_lines = xtargets[1]
                    break
            else:
                if segment_number in xtargets[1]:
                    from_lines = xtargets[1]
                    to_lines = xtargets[0]
                    break

        if not any(to_lines):
            to_lines = []

        alignment = '{} => {}'.format(len(from_lines), len(to_lines)) if to_lines else ''

        return from_lines, to_lines, alignment

    def parse_alignment_trees(self, filename):
        base_filename = os.path.basename(filename)
        data_folder = os.path.dirname(os.path.dirname(filename))

        alignment_trees = dict()
        translation_trees = dict()
        for language_to in self.l_to:
            sl = sorted([self.l_from, language_to])
            alignment_file = os.path.join(data_folder, '-'.join(sl) + '.xml')
            if os.path.isfile(alignment_file):
                alignment_tree = etree.parse(alignment_file)
                doc = '{}/{}.gz'.format(self.l_from, base_filename)
                path = '@fromDoc="{}"' if sl[0] == self.l_from else '@toDoc="{}"'
                linkGrps = alignment_tree.xpath('//linkGrp[{}]'.format(path.format(doc)))

                if not linkGrps:
                    print 'No translation found for {} to {}'.format(filename, language_to)
                elif len(linkGrps) == 1:
                    linkGrp = linkGrps[0]

                    translation_link = linkGrp.get('toDoc') if sl[0] == self.l_from else linkGrp.get('fromDoc')
                    translation_file = os.path.join(data_folder, translation_link[:-3])
                    translation_trees[language_to] = etree.parse(translation_file)

                    links = [link.get('xtargets').split(';') for link in linkGrp.xpath('./link')]
                    alignment_trees[language_to] = [[la.split(' '), lb.split(' ')] for la, lb in links]
                else:
                    print 'Multiple translations found for {} to {}'.format(filename, language_to)

        return alignment_trees, translation_trees


class EuroParlPoSExtractor(EuroparlExtractor, PoSExtractor):
    def process_file(self, filename):
        """
        Processes a single file.
        """
        t0 = time.time()
        print 'Now processing ' + filename + '...'

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag='s')

        # Parse the alignment and translation trees
        alignment_trees, translation_trees = self.parse_alignment_trees(filename)

        t1 = time.time()
        print 'Finished parsing trees, took {:.3} seconds'.format(t1 - t0)

        results = []

        # Find potential words matching the part-of-speech
        pos_attr = self.config.get(self.l_from, 'pos')
        lemma_attr = self.config.get('all', 'lemma_attr')
        xp = './/w[contains(" {value} ", concat(" ", @{element}, " "))]'
        if self.pos:
            xpath = xp.format(element=pos_attr, value=' '.join(self.pos))
        else:
            xpath = xp.format(element=lemma_attr, value=' '.join(self.lemmata_list))

        for _, s in s_trees:
            if self.sentence_ids and s.get('id') not in self.sentence_ids:
                continue

            for w in s.xpath(xpath):
                words = self.preprocess_found(w)

                if words is None:
                    continue

                result = list()
                result.append(os.path.basename(filename))
                result.append(s.get('id'))
                result.append(self.get_type(words))
                result.append(' '.join([w.text for w in words]))
                result.append(' '.join([w.get('id') for w in words]))
                result.append('<root>' + etree.tostring(s) + '</root>')

                # Find the translated lines
                for language_to in self.l_to:
                    if language_to in translation_trees:
                        # TODO: deal with source_lines
                        source_lines, translated_lines, alignment_type = self.get_translated_lines(alignment_trees,
                                                                                                   self.l_from,
                                                                                                   language_to,
                                                                                                   s.get('id'))
                        if translated_lines:
                            translated_sentences = [self.get_line(translation_trees[language_to], line) for line in translated_lines]
                            result.append(alignment_type)
                            result.append('<root>' + '\n'.join(translated_sentences) + '</root>' if translated_sentences else '')
                        else:
                            result.append('')
                            result.append('')
                    else:
                        # If no translation is available, add empty columns
                        result.extend([''] * 2)

                results.append(result)

        print 'Finished finding PoS, took {:.3} seconds'.format(time.time() - t1)

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
            result = None

        if self.position and not word.get('id').endswith('.' + str(self.position)):
            result = None

        return result


class EuroparlFrenchArticleExtractor(EuroParlPoSExtractor):
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

        for w in super(EuroparlFrenchArticleExtractor, self).preprocess_found(word):
            prev = w.getprevious()
            if prev is not None and prev.get('lem') in self.particles:
                result.append(prev)

            result.append(word)

        return result

    def get_type(self, words):
        """
        Return the type for a found article: definite, indefinite or partitive.
        For 'des', this is quite hard to decide, so we leave both options open.
        """
        result = ''

        if words[-1].get('lem') == 'le':
            result = 'definite'
        elif words[-1].get('lem') == 'un':
            result = 'indefinite'

        if words[0].get('lem') in self.particles:
            if result:
                result += ' '
            result += 'partitive'

        if words[0].text == 'des':
            result = 'indefinite/partitive'

        return result


class EuroParlRecentPastExtractor(EuroparlExtractor, RecentPastExtractor):
    def process_file(self, filename):
        """
        Processes a single file.
        """
        t0 = time.time()
        print 'Now processing ' + filename + '...'

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag='s')

        # Parse the alignment and translation trees
        alignment_trees, translation_trees = self.parse_alignment_trees(filename)

        t1 = time.time()
        print 'Finished parsing trees, took {:.3} seconds'.format(t1 - t0)

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
                    result.append('<root>' + etree.tostring(rp.xml_sentence) + '</root>')

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
                                                print 'found recent past in French'
                                                found_trans = True

                                result.append(alignment_type)
                                result.append('<root>' + '\n'.join(
                                    translated_sentences) + '</root>' if translated_sentences else '')
                            else:
                                result.append('')
                                result.append('')
                        else:
                            # If no translation is available, add empty columns
                            result.extend([''] * 2)

                    if not found_trans:
                        results.append(result)

        print 'Finished finding recent pasts, took {:.3} seconds'.format(time.time() - t1)

        return results

    def get_sentence_words(self, xml_sentence):
        s = []
        # TODO: this xPath-expression might be specific for a corpus
        for w in xml_sentence.xpath('.//w'):
            s.append(w.text.strip() if w.text else ' ')
        return ' '.join(s)


class EuroparlPerfectExtractor(EuroparlExtractor, PerfectExtractor):
    def get_line_by_number(self, tree, language_to, segment_number):
        """
        Returns the full line for a segment number, as well as the PresentPerfect found (or None if none found).
        TODO: handle more than one here? => bug
        """
        sentence = '-'
        pp = None

        line = tree.xpath('//s[@id="' + segment_number + '"]')
        if line:
            s = line[0]
            first_w = s.xpath('.//w')[0]
            sentence = get_sentence_from_element(first_w)

            if self.search_in_to:
                for e in s.xpath(self.config.get(language_to, 'xpath')):
                    pp = self.check_present_perfect(e, language_to)
                    if pp:
                        sentence = pp.mark_sentence()
                        break

        return etree.tostring(s), sentence, pp

    def process_file(self, filename):
        """
        Processes a single file.
        """
        t0 = time.time()
        print 'Now processing ' + filename + '...'

        # Parse the current tree (create a iterator over 's' elements)
        s_trees = etree.iterparse(filename, tag='s')

        # Parse the alignment and translation trees
        alignment_trees, translation_trees = self.parse_alignment_trees(filename)

        t1 = time.time()
        print 'Finished parsing trees, took {:.3} seconds'.format(t1 - t0)

        results = []
        # Find potential present perfects (per sentence)
        for _, s in s_trees:
            if self.sentence_ids and s.get('id') not in self.sentence_ids:
                continue

            for e in s.xpath(self.config.get(self.l_from, 'xpath')):
                pp = self.check_present_perfect(e, self.l_from)

                # If this is really a present perfect, add it to the result
                if pp:
                    result = list()
                    result.append(os.path.basename(filename))
                    result.append(s.get('id'))
                    result.append(pp.perfect_type())
                    result.append(pp.verbs_to_string())
                    result.append(pp.verb_ids())
                    result.append('<root>' + etree.tostring(pp.xml_sentence) + '</root>')

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
                            result.append('<root>' + '\n'.join(translated_sentences) + '</root>' if translated_sentences else '')
                        else:
                            # If no translation is available, add empty columns
                            result.extend([''] * 2)

                    results.append(result)

        print 'Finished finding present perfects, took {:.3} seconds'.format(time.time() - t1)

        return results
