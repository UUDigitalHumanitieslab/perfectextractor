MARKUP = u'**{}**'


class Word(object):
    """
    Each Word consists of a word, its lemma, and a designation if this is a verb.
    """
    def __init__(self, word, lemma, is_verb, xml_id):
        self.word = word.strip() if word else ' '
        self.lemma = lemma.strip() if lemma else '?'
        self.is_verb = is_verb
        self.xml_id = xml_id


class MultiWordExpression(object):
    def __init__(self, xml_sentence=None):
        self.xml_sentence = xml_sentence
        self.words = []

    def add_word(self, word, lemma, is_verb, xml_id):
        """
        Adds a word to the MultiWordExpression.
        """
        self.words.append(Word(word, lemma, is_verb, xml_id))

    def prepend_word(self, word, lemma, is_verb, xml_id):
        """
        Prepends a word to the MultiWordExpression.
        """
        self.words.insert(0, Word(word, lemma, is_verb, xml_id))

    def verbs(self):
        """
        Extracts the verbs from the MultiWordExpression.
        """
        return [w.word for w in self.words if w.is_verb]

    def verbs_to_string(self):
        """
        Returns the verbs from the MultiWordExpression as a string.
        """
        return ' '.join(self.verbs())

    def verb_ids(self):
        return ' '.join([w.xml_id for w in self.words if w.is_verb])

    def words_between(self):
        """
        Returns the total number of non-verbs in a MultiWordExpression.
        """
        return len([w.word for w in self.words if not w.is_verb])

    def words_between_verbs(self):
        """
        Returns the number of non-verbs in a MultiWordExpression between the verbs.
        """
        result = []
        current_count = 0
        for w in self.words:
            if w.is_verb:
                result.append(current_count)
                current_count = 0
            else:
                current_count += 1

        return result

    def get_sentence_words(self):
        s = []
        # TODO: this xPath-expression might be specific for a corpus
        for w in self.xml_sentence.xpath('.//w'):
            s.append(w.text.strip() if w.text else ' ')
        return ' '.join(s)

    def get_sentence_id(self):
        return self.xml_sentence.get('id')

    def mark_sentence(self):
        """
        Marks the MultiWordExpression in a full sentence.
        """
        # TODO: this doesn't work if no xml_sentence is given
        if self.xml_sentence is None:
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


class Perfect(MultiWordExpression):
    """
    A Perfect is a special kind of MultiWordExpression, consisting of an auxiliary and one or more past participles.
    """

    def __init__(self, aux_verb, aux_lemma, xml_id, xml_sentence=None):
        """
        A (Present/Past) Perfect is initiated by an auxiliary verb.
        """
        super(Perfect, self).__init__(xml_sentence)
        self.is_passive = False
        self.is_continuous = False
        self.is_reflexive = False
        self.add_word(aux_verb, aux_lemma, True, xml_id)

    def extend(self, present_perfect):
        """
        Extends a Perfect with another one (used to create a passive or continuous Perfect).
        """
        for i, w in enumerate(present_perfect.words):
            if i == 0:
                continue
            self.add_word(w.word, w.lemma, w.is_verb, w.xml_id)

        self.is_passive = not present_perfect.is_continuous
        self.is_continuous = present_perfect.is_continuous

    def perfect_lemma(self):
        """
        Returns the lemma of the Perfect: the lemma of the last word of the construction.
        """
        return self.words[-1].lemma

    def perfect_type(self):
        """
        Returns the type of Perfect
        """
        # TODO: This should be language-dependent, as well as dependent upon being a Present or Past Perfect
        result = 'present perfect'
        if self.is_passive:
            result += ' passive'
        if self.is_continuous:
            result += ' continuous'
        return result


class Alignment(object):
    def __init__(self, sources, targets, certainty=None):
        self.sources = sources
        self.targets = targets
        self.certainty = certainty
