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

            # special namespace required for enabling regular expresssion functions
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

                result = self.generate_result_line(filename, s, words=words)
                result.extend(self.generate_translations(alignment_trees, translation_trees, s))
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

    def get_type(self, sentence, words=None, mwe=None):
        """
        Return the type for the found word(s). A sensible default is the part-of-speech of the first found word.
        """
        return self.get_pos(self.l_from, words[0])
