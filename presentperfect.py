MARKUP = u'**{}**'


class PresentPerfect:
    """
    A present perfect consists of a list of tuples (words).
    Each tuple consist of a word, its lemma, and a designation if this is a verb.
    """

    def __init__(self, aux_verb, aux_lemma):
        """
        A present perfect is initiated by an auxiliary verb.
        """
        self.words = []
        self.add_word(aux_verb, aux_lemma, True)

    def add_word(self, word, lemma, is_verb):
        """
        Adds a word to the present perfect.
        """
        self.words.append((word, lemma, is_verb))

    def extend(self, present_perfect):
        """
        Extends a present perfect with another one (used for present perfect continuous).

        >>> pp_extend = PresentPerfect('been', 'be')
        >>> pp_extend.add_word('created', 'create', True)
        >>> ppc.extend(pp_extend)
        >>> ppc.verbs()
        ['has', 'been', 'created']
        """
        for i, (word, lemma, is_verb) in enumerate(present_perfect.words):
            if i == 0:
                continue
            self.add_word(word, lemma, is_verb)

    def perfect_lemma(self):
        """
        Returns the lemma of the perfect: the last word of the construction.

        >>> pp.perfect_lemma()
        'love'
        """
        return self.words[-1][1]

    def verbs(self):
        """
        Extracts the verbs from the present perfect.

        >>> pp.verbs()
        ['has', 'loved']
        """
        return [part for (part, _, is_verb) in self.words if is_verb]

    def verbs_to_string(self):
        """
        Returns the verbs from the present perfect as a string.

        >>> pp.verbs_to_string()
        'has loved'
        """
        return ' '.join(self.verbs())

    def words_between(self):
        """
        Returns the number of non-verbs in a present perfect construction.

        >>> pp.words_between()
        1
        """
        return len([part for (part, _, is_verb) in self.words if not is_verb])

    def mark_sentence(self, sentence):
        """
        Marks the present perfect in a full sentence.

        >>> pp.mark_sentence('She has always loved him.')
        u'She **has** always **loved** him.'
        """
        # TODO: this is a bit iffy, another idea could be to compose the sentence from the remaining siblings
        # To find the pp in the full text, simply join all the parts of the pp
        pp_text = ' '.join([part for (part, _, _) in self.words])

        # For the replacement, mark the verbs with the MARKUP
        if len(self.words) == len(self.verbs()):
            marked_pp = MARKUP.format(pp_text)
        else:
            marked_pp = ' '.join([MARKUP.format(part) if is_verb else part for (part, _, is_verb) in self.words])

        return sentence.replace(pp_text, marked_pp)


if __name__ == "__main__":
    import doctest
    pp = PresentPerfect('has', 'have')
    pp.add_word('always', 'always', False)
    pp.add_word('loved', 'love', True)
    ppc = PresentPerfect('has', 'have')
    ppc.add_word('been', 'be', True)
    doctest.testmod(extraglobs={'pp': pp, 'ppc': ppc})
