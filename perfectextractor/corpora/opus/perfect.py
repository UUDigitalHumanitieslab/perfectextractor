import os

from lxml import etree

from perfectextractor.apps.extractor.perfectextractor import PerfectExtractor, PRESENT
from perfectextractor.apps.extractor.xml_utils import get_sentence_from_element

from .extractor import OPUSExtractor


class OPUSPerfectExtractor(OPUSExtractor, PerfectExtractor):
    def get_config(self):
        perfect_config = os.path.join(os.path.dirname(__file__), 'perfect.cfg')
        return [super().get_config(), perfect_config]

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
            # Retrieves the xpath expression for the auxiliary in the given tense or a fallback
            xpath_fallback = 'xpath'
            xpath = xpath_fallback + ('_{}'.format(self.tense) if self.tense != PRESENT else '')
            l_config = self.config[self.l_from]
            aux_xpath = l_config.get(xpath, l_config.get(xpath_fallback))

            for e in s.xpath(aux_xpath):
                pp = self.check_perfect(e, self.l_from)

                # apply position filter
                if self.position and not e.get('id').endswith('.' + str(self.position)):
                    continue

                # If this is really a present/past perfect, add it to the result
                if pp:
                    result = self.generate_result_line(filename, s, mwe=pp)
                    result.extend(self.generate_translations(alignment_trees, translation_trees, s))
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
                    result.append(self.mark_sentence(s))
                    self.append_metadata(s, result)
                    results.append(result)

        return results

    def get_type(self, sentence, mwe=None):
        return mwe.perfect_type()
