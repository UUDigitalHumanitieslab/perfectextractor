MARKUP = u'**{}**'


class Word:
    """
    Each Word consists of a word, its lemma, and a designation if this is a verb.
    """
    def __init__(self, word, lemma, is_verb, xml_id):
        self.word = word
        self.lemma = lemma
        self.is_verb = is_verb
        self.xml_id = xml_id


class PresentPerfect:
    """
    A present perfect consists of a list of Words.
    """

    def __init__(self, aux_verb, aux_lemma, xml_id, xml_sentence=None):
        """
        A present perfect is initiated by an auxiliary verb.
        """
        self.xml_sentence = xml_sentence
        self.words = []
        self.add_word(aux_verb, aux_lemma, True, xml_id)

    def add_word(self, word, lemma, is_verb, xml_id):
        """
        Adds a word to the present perfect.
        """
        self.words.append(Word(word, lemma, is_verb, xml_id))

    def extend(self, present_perfect):
        """
        Extends a present perfect with another one (used to create a present perfect continuous).
        """
        for i, w in enumerate(present_perfect.words):
            if i == 0:
                continue
            self.add_word(w.word, w.lemma, w.is_verb, w.xml_id)

    def perfect_lemma(self):
        """
        Returns the lemma of the perfect: the lemma of the last word of the construction.
        """
        return self.words[-1].lemma

    def verbs(self):
        """
        Extracts the verbs from the present perfect.
        """
        return [w.word for w in self.words if w.is_verb]

    def verbs_to_string(self):
        """
        Returns the verbs from the present perfect as a string.
        """
        return ' '.join(self.verbs())

    def verb_ids(self):
        return ' '.join([w.xml_id for w in self.words if w.is_verb])

    def words_between(self):
        """
        Returns the number of non-verbs in a present perfect construction.
        """
        return len([w.word for w in self.words if not w.is_verb])

    def get_sentence_words(self):
        s = []
        # TODO: this xPath-expression might be specific for a corpus
        for w in self.xml_sentence.xpath('.//w'):
            s.append(w.text)
        return ' '.join(s)

    def get_sentence_id(self):
        return self.xml_sentence.get('id')

    def mark_sentence(self):
        """
        Marks the present perfect in a full sentence.
        """
        # TODO: this doesn't work if no xml_sentence is given
        if not self.xml_sentence:
            return ''

        # TODO: this is a bit iffy, another idea could be to compose the sentence from the remaining siblings
        # To find the pp in the full text, simply join all the parts of the pp
        pp_text = ' '.join([w.word for w in self.words])

        # For the replacement, mark the verbs with the MARKUP
        if len(self.words) == len(self.verbs()):
            marked_pp = MARKUP.format(pp_text)
        else:
            marked_pp = ' '.join([MARKUP.format(w.word) if w.is_verb else w.word for w in self.words])

        return self.get_sentence_words().replace(pp_text, marked_pp)
