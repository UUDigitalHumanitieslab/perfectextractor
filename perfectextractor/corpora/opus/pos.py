from perfectextractor.apps.extractor.posextractor import PoSExtractor

from .extractor import OPUSExtractor


class OPUSPoSExtractor(OPUSExtractor, PoSExtractor):
    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        """
        Processes a single file.
        """
        results = []

        # Prepare the search predicates
        xpath, ns = self.prepare_xpath()

        for _, s in s_trees:
            for w in s.xpath(xpath, namespaces=ns):
                words = self.preprocess_found(w)

                if not words:
                    continue

                result = self.generate_result_line(filename, s, self.words2mwe(words, s))
                result.extend(self.generate_translations(alignment_trees, translation_trees, s))
                results.append(result)

        return results

    def get_type(self, sentence, mwe=None):
        """
        Return the type for the found word(s). A sensible default is the part-of-speech of the first found word.
        """
        return mwe.words[0].pos
