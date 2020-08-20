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


def get_adjacent_line_number(segment_number, i):
    """
    Returns the next segment number + i.
    Segment numbers have the form "pN.sM", where N/M are positive integers.
    """
    split = segment_number.split('s')
    adj = int(split[1]) + i
    return split[0] + 's' + str(adj)
