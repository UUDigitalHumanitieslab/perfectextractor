from typing import List, Optional

from lxml import etree

MARKUP = u'**{}**'


class Word:
    """
    Each Word consists of a word, its lemma, and a designation if this is part of a construction.
    """
    def __init__(self, word: str, lemma: str, pos: str, xml_id: str,
                 in_construction: bool = True) -> None:
        self.word = word.strip()
        self.lemma = lemma.strip()
        self.pos = pos.strip()
        self.xml_id = xml_id.strip()
        self.in_construction = in_construction


class MultiWordExpression:
    def __init__(self, xml_sentence: etree._Element) -> None:
        self.xml_sentence = xml_sentence
        self.words: List[Word] = []

    def add_word(self, word: str, lemma: str, pos: str, xml_id: str,
                 in_construction: bool = True) -> None:
        """
        Adds a word to the MultiWordExpression.
        """
        self.words.append(Word(word, lemma, pos, xml_id, in_construction))

    def prepend_word(self, word: str, lemma: str, pos: str, xml_id: str,
                     in_construction: bool = True) -> None:
        """
        Prepends a word to the MultiWordExpression.
        """
        self.words.insert(0, Word(word, lemma, pos, xml_id, in_construction))

    def construction(self) -> List[str]:
        """
        Extracts the words in the construction from the MultiWordExpression.
        """
        return [w.word for w in self.words if w.in_construction]

    def construction_to_string(self) -> str:
        """
        Returns the construction from the MultiWordExpression as a string.
        """
        return ' '.join(self.construction())

    def construction_ids(self) -> str:
        return ' '.join([w.xml_id for w in self.words if w.in_construction])

    def words_between(self) -> int:
        """
        Returns the total number of words in a MultiWordExpression not of part of the construction.
        """
        return len([w.word for w in self.words if not w.in_construction])

    def words_between_construction(self) -> List[int]:
        """
        Returns the number of words in a MultiWordExpression between the construction.
        """
        result = []
        current_count = 0
        for w in self.words:
            if w.in_construction:
                result.append(current_count)
                current_count = 0
            else:
                current_count += 1

        return result

    def get_sentence_words(self) -> str:
        s = []
        # TODO: this xPath-expression might be specific for a corpus
        if self.xml_sentence is not None:
            words: List[etree._Element] = self.xml_sentence.xpath('.//w')
            for w in words:
                s.append(str(w.text.strip() if w.text else ' '))
        return ' '.join(s)

    def mark_sentence(self) -> str:
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
        if len(self.words) == len(self.construction()):
            marked_pp = MARKUP.format(pp_text)
        else:
            marked_pp = ' '.join([MARKUP.format(w.word) if w.in_construction else w.word for w in self.words])

        return self.get_sentence_words().replace(pp_text, marked_pp)


class Perfect(MultiWordExpression):
    """
    A Perfect is a special kind of MultiWordExpression, consisting of an auxiliary and one or more past participles.
    """

    def __init__(self, xml_sentence: etree._Element) -> None:
        super().__init__(xml_sentence)
        self.is_passive = False
        self.is_continuous = False
        self.is_reflexive = False

    def extend(self, perfect: 'Perfect') -> None:
        """
        Extends a Perfect with another one (used to create a passive or continuous Perfect).
        """
        for i, w in enumerate(perfect.words):
            if i == 0:
                continue
            self.add_word(w.word, w.lemma, w.pos, w.xml_id, w.in_construction)

        self.is_passive = not perfect.is_continuous
        self.is_continuous = perfect.is_continuous

    def perfect_lemma(self) -> str:
        """
        Returns the lemma of the Perfect: the lemma of the last word of the construction.
        """
        return self.words[-1].lemma

    def perfect_type(self) -> str:
        """
        Returns the type of Perfect.
        """
        # TODO: This should be language-dependent, as well as dependent upon being a Present or Past Perfect
        result = 'present perfect'
        if self.is_passive:
            result += ' passive'
        if self.is_continuous:
            result += ' continuous'
        return result


class Alignment:
    def __init__(self, sources: List[str], targets: List[str], certainty: Optional[float] = None) -> None:
        self.sources = sources
        self.targets = targets
        self.certainty = certainty
