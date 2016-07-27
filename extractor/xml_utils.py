def get_original_language(element):
    """
    Returns the original language for a document.
    """
    speaker_language = element.getparent().getparent().getparent().get('LANGUAGE')
    return speaker_language or '?'


def get_sentence_from_element(element):
    s = []
    for w in element.xpath('ancestor::s')[0].xpath('.//w'):
        s.append(w.text)
    return ' '.join(s)
