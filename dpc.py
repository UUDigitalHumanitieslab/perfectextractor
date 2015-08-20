import ConfigParser
import codecs
import glob
import string

from lxml import etree

TEI = {'ns': 'http://www.tei-c.org/ns/1.0'}
NL = 'nl'


def get_line_by_number(tree, segment_number):
    """
    Returns the line for a segment number.
    TODO: handle not found here.
    TODO: handle more than one here? => bug
    """
    result = '-'
    line = tree.xpath('//ns:s[@n="' + segment_number + '"]', namespaces=TEI)
    if line:
        result = line[0].getprevious().text
    return result


def get_adjacent_line_number(segment_number, i):
    """
    Returns the next segment number + i.
    """
    split = segment_number.split('s')
    adj = int(split[1]) + i
    return split[0] + 's' + str(adj)


def get_marked_sentence(e, pp):
    """
    Retrieve the full sentence for an element and mark the pp in there.
    TODO: this is a bit iffy, another idea could be to compose the sentence from the remaining siblings
    """
    full_sentence = e.getparent().getprevious().text
    return full_sentence.replace(' '.join(pp), '**' + ' '.join(pp) + '**')


class PerfectExtractor:
    def __init__(self, language_from, language_to):
        self.l_from = language_from
        self.l_to = language_to
        config = ConfigParser.RawConfigParser()
        config.read('dpc.cfg')
        self.config = config

    def is_nl(self):
        return int(self.l_from == NL)

    def get_translated_lines(self, document, segment_number):
        """
        Returns the translated segment numbers (could be multiple) for a segment number in the original text.

        The translation document file format either ends with nl-en-tei.xml or nl-fr-tei.xml.

        An alignment line looks like this:
            <link type="A: 1-1" targets="p1.s1; p1.s1"/>
        To get from NL to EN/FR, we have to find the segment number in the targets attribute BEFORE the semicolon.
        For the reverse pattern, we have to find the segment number in the targets attribute AFTER the semicolon.

        This function supports 1-to-2 alignments, as it will return the translated lines as a list.

        TODO: deal with 2-to-1 alignments as well here.
        """
        not_nl = self.l_to if self.l_from == NL else self.l_from

        alignment_tree = etree.parse(document + NL + '-' + not_nl + '-tei.xml')
        for link in alignment_tree.xpath('//ns:link', namespaces=TEI):
            targets = link.get('targets').split('; ')
            if segment_number in targets[1 - self.is_nl()].split(' '):
                return targets[self.is_nl()].split(' ')

    def get_original_language(self, document):
        """
        Returns the original language for a document.
        """
        metadata_tree = etree.parse(document + self.l_from + '-mtd.xml')
        return metadata_tree.getroot().find('metaTrans').find('Original').get('lang')

    def check_present_perfect(self, element, check_ppc=True):
        """
        Checks whether this element is the start of a present perfect (or pp continuous).
        If it is, the present perfect is returned as a list.
        If not, None is returned.
        """
        perfect_tag = self.config.get(self.l_from, 'stop_tag')
        check_ppc = check_ppc and self.config.getboolean(self.l_from, 'ppc')
        ppc_lemma = self.config.get(self.l_from, 'ppc_lemma')

        pp = [element.text]
        is_pp = False

        for sibling in element.itersiblings():
            pp.append(sibling.text)
            # We found a perfect...
            if sibling.get('ana') == perfect_tag:
                is_pp = True
                # ... now check whether this is a present perfect continuous (by recursion)
                if check_ppc and sibling.get('lemma') == ppc_lemma:
                    ppc = self.check_present_perfect(sibling, False)
                    if ppc:
                        pp.extend(ppc[1:])
                break
            # Stop looking at punctuation
            if sibling.text in string.punctuation:
                break

        return pp if is_pp else None

    def process_folder(self, dir_name):
        """
        Creates a result file and processes each English file in a folder.
        """
        result_file = dir_name + '.txt'
        with codecs.open(result_file, 'w', 'utf-8') as f:
            for filename in glob.glob(dir_name + '/*[0-9]-' + self.l_from + '-tei.xml'):
                self.process_file(f, filename)

    def process_file(self, f, filename):
        """
        Processes a single file.
        """
        document = filename.split(self.l_from + '-tei.xml')[0]
        f.write('Document: ' + document[:-1] + '\n')
        f.write('Original language: ' + self.get_original_language(document) + '\n')

        tree = etree.parse(filename)
        found = False
        for e in tree.xpath(self.config.get(self.l_from, 'xpath'), namespaces=TEI):
            pp = self.check_present_perfect(e)

            if pp:
                found = True
                f.write('Present perfect: ' + ' '.join(pp) + '\n')

                # Write the complete segment with mark-up
                f.write(get_marked_sentence(e, pp) + '\n')

                # Find the translated lines
                seg_n = e.getparent().getparent().get('n')[4:]
                translated_lines = self.get_translated_lines(document, seg_n)
                if translated_lines:
                    translated_tree = etree.parse(document + self.l_to + '-tei.xml')
                    for t in translated_lines:
                        #f.write(get_line_by_number(translated_tree, get_adjacent_line_number(t, -1)) + '\n')
                        f.write(get_line_by_number(translated_tree, t) + '\n')
                        #f.write(get_line_by_number(translated_tree, get_adjacent_line_number(t, 1)) + '\n')
                    f.write('\n')
                else:
                    f.write('Not translated\n\n')

        if not found:
            f.write('No present perfects found in this document\n\n')

#for root, dirs, files in os.walk(os.getcwd()):
#    for d in dirs:
#        process_folder(d)
        #break
#process_folder('bal')

if __name__ == "__main__":
    en_extractor = PerfectExtractor('en', 'nl')
    en_extractor.process_folder('data/bal')
    nl_extractor = PerfectExtractor('nl', 'en')
    nl_extractor.process_folder('data/gru')
    nl_extractor = PerfectExtractor('nl', 'fr')
    nl_extractor.process_folder('data/mok')
