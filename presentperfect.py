MARKUP = u'**{}**'


class PresentPerfect:
    """
    A present perfect consists of a list of tuples (words).
    Each tuple consist of a word and a designation if this is a verb.
    """

    def __init__(self, aux_verb):
        """
        A present perfect is initiated by an auxiliary verb.
        """
        self.words = []
        self.add_word(aux_verb, True)

    def add_word(self, word, is_verb):
        """
        Adds a word to the present perfect.
        """
        self.words.append((word, is_verb))

    def extend(self, present_perfect):
        """
        Extends a present perfect with another one (used for present perfect continuous).
        """
        for i, (part, is_verb) in enumerate(present_perfect.words):
            if i == 0:
                continue
            self.add_word(part, is_verb)

    def verbs(self):
        """
        Extracts the verbs from the present perfect.
        """
        return [part for (part, is_verb) in self.words if is_verb]

    def verbs_to_string(self):
        """
        Returns the verbs from the present perfect as a string.
        """
        return ' '.join(self.verbs())

    def mark_sentence(self, sentence):
        """
        Marks the present perfect in a full sentence.
        """
        # TODO: this is a bit iffy, another idea could be to compose the sentence from the remaining siblings
        # To find the pp in the full text, simply join all the parts of the pp
        pp_text = ' '.join([part for (part, _) in self.words])

        # For the replacement, mark the verbs with the MARKUP
        if len(self.words) == len(self.verbs()):
            marked_pp = MARKUP.format(pp_text)
        else:
            marked_pp = ' '.join([MARKUP.format(part) if is_verb else part for (part, is_verb) in self.words])

        return sentence.replace(pp_text, marked_pp)
