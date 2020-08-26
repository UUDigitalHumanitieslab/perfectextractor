import os

from .pos import OPUSPoSExtractor


class OPUSSinceDurationExtractor(OPUSPoSExtractor):
    def __init__(self, language_from, languages_to, **kwargs):
        """
        Initializes the OPUSSinceDurationExtractor with a set of lemmata, part-of-speech for numbers,
        and time units, so that it should find [seit] + [number] + [unit of time].
        :param language_from: The language to find the specified part-of-speeches in.
        :param languages_to: The languages to extract the aligned sentences from.
        """
        super().__init__(language_from, languages_to, **kwargs)

        self.lemmata_list = self.config.get(self.l_from, 'since_lem').split('|')
        self.number_pos = self.config.get(self.l_from, 'since_number_pos').split('|')
        self.time_units = self.config.get(self.l_from, 'since_time_units').split('|')

    def get_config(self):
        since_config = os.path.join(os.path.dirname(__file__), 'since.cfg')
        return [super().get_config(), since_config]

    def preprocess_found(self, word):
        result = []

        for w in super().preprocess_found(word):
            result.append(word)

            next_word = w.getnext()
            if next_word is not None and self.get_pos(self.l_from, next_word) in self.number_pos:
                result.append(next_word)
            else:
                result = None
                continue

            next_word2 = next_word.getnext()
            if next_word2 is not None and self.get_lemma(next_word2) in self.time_units:
                result.append(next_word2)
            else:
                result = None
                continue

        return result
