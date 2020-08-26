from .pos import OPUSPoSExtractor


class OPUSFrenchArticleExtractor(OPUSPoSExtractor):
    def __init__(self, language_from, languages_to):
        """
        Initializes the OPUSFrenchArticleExtractor with a set of part-of-speeches and lemmata that the found
        words should adhere to. Also initializes a list of particles that could appear before a determiner.
        :param language_from: The language to find the specified part-of-speeches in.
        :param languages_to: The languages to extract the aligned sentences from.
        """
        super().__init__(language_from, languages_to, pos=['DET:ART', 'PRP:det'])

        self.lemmata_list = ['le', 'un', 'du']
        self.particles = ['de', 'du']

    def preprocess_found(self, word):
        """
        Removes a word if does not occur in the lemmata list, and then checks if it might be preceded by a particle.
        If so, add the particle to the found words.
        """
        result = []

        for w in super().preprocess_found(word):
            prev = w.getprevious()
            if prev is not None and self.get_lemma(prev) in self.particles:
                result.append(prev)

            result.append(word)

        return result

    def get_type(self, sentence, mwe=None):
        """
        Return the type for a found article: definite, indefinite or partitive.
        For 'des', this is quite hard to decide, so we leave both options open.
        """
        result = ''

        if mwe.words[-1].lemma == 'le':
            result = 'definite'
        elif mwe.words[-1].lemma == 'un':
            result = 'indefinite'

        if mwe.words[0].lemma in self.particles:
            if result:
                result += ' '
            result += 'partitive'

        if mwe.words[0].word == 'des':
            result = 'indefinite/partitive'

        return result
