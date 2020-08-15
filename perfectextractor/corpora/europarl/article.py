from .pos import EuroparlPoSExtractor


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

    def get_type(self, sentence, words=None, mwe=None):
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
