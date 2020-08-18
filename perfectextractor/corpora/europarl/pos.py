from perfectextractor.apps.extractor.posextractor import PoSExtractor

from .extractor import EuroparlExtractor


class EuroparlPoSExtractor(EuroparlExtractor, PoSExtractor):
    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        """
        Processes a single file.
        """
        results = []

        # Find potential words matching the part-of-speech
        pos_attr = self.config.get(self.l_from, 'pos', fallback=self.config.get('all', 'pos'))
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

            # special namespace required for enabling regular expression functions
            ns = {"re": "http://exslt.org/regular-expressions"}
            predicates.append('re:test(., "{pattern}", "i")'.format(pattern=pattern))

        xpath = './/w'
        if predicates:
            xpath = './/w[{}]'.format(' and '.join(predicates))

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
