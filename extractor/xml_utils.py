def get_original_language(element):
    """
    Returns the original language for a document.
    """
    speaker_language = element.getparent().getparent().getparent().get('LANGUAGE')
    return speaker_language or '?'


def get_siblings(element, s_id, check_preceding):
    path = ('preceding' if check_preceding else 'following') + '::w[ancestor::s[@id="' + s_id + '"]]'
    siblings = element.xpath(path)
    if check_preceding:
        siblings = siblings[::-1]
    return siblings


def get_sentence_from_element(element):
    s = []
    for w in get_sentence(element).xpath('.//w'):
        s.append(w.text)
    return ' '.join(s)


def get_sentence(element):
    return element.xpath('ancestor::s')[0]
