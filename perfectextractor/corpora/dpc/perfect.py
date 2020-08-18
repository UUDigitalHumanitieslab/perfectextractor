import os

from lxml import etree

from perfectextractor.apps.extractor.perfectextractor import PerfectExtractor

from .base import TEI_NS
from .extractor import DPCExtractor


class DPCPerfectExtractor(DPCExtractor, PerfectExtractor):
    def get_config(self):
        perfect_config = os.path.join(os.path.dirname(__file__), 'perfect.cfg')
        return [super().get_config(), perfect_config]

    def get_line_and_pp(self, tree, language_to, segment_number):
        """
        Returns the full line for a segment number, as well as the Perfect found (or None if none found).
        TODO: handle more than one here? => bug
        """
        sentence = '-'
        pp = None

        line = tree.xpath('//ns:s[@n="' + segment_number + '"]', namespaces=TEI_NS)
        if line:
            s = line[0]
            sentence = s.getprevious().text

            if self.search_in_to:
                for e in s.xpath(self.config.get(language_to, 'xpath'), namespaces=TEI_NS):
                    pp = self.check_perfect(e, language_to)
                    if pp:
                        sentence = pp.mark_sentence()
                        break

        return etree.tostring(s, encoding=str), sentence, pp

    def get_original_language(self, document):
        """
        Returns the original language for a document.
        """
        metadata_tree = etree.parse(document + self.l_from + '-mtd.xml')
        return metadata_tree.getroot().find('metaTrans').find('Original').get('lang')

    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        """
        Processes a single file.
        """
        results = []

        document = filename.split(self.l_from + '-tei.xml')[0]

        # Find potential Perfects
        for _, s in s_trees:
            for e in s.xpath(self.config.get(self.l_from, 'xpath'), namespaces=TEI_NS):
                pp = self.check_perfect(e, self.l_from)

                # If this is really a Perfect, add it to the result
                if pp:
                    result = list()
                    result.append(document[:-1])
                    result.append(self.get_original_language(document))
                    result.append(pp.perfect_type())
                    result.append(pp.construction_to_string())

                    # Write the complete segment with mark-up
                    result.append(pp.mark_sentence())

                    # Find the translated lines
                    segment_number = e.getparent().getparent().get('n')[4:]
                    for language_to in self.l_to:
                        if language_to in translation_trees:
                            translated_lines, alignment_type = self.get_translated_lines(alignment_trees, self.l_from,
                                                                                         language_to, segment_number)
                            translated_present_perfects, translated_sentences, translated_marked_sentences = \
                                self.find_translated_present_perfects(translation_trees[language_to], language_to, translated_lines)
                            result.append('\n'.join([tpp.construction_to_string() if tpp else '' for tpp in translated_present_perfects]))
                            result.append('\n'.join(self.check_translated_pps(pp, translated_present_perfects, language_to)))
                            result.append(alignment_type)
                            result.append('\n'.join(translated_sentences))
                        else:
                            # If no translation is available, add empty columns
                            result.extend([''] * 4)

                    results.append(result)

        return results
