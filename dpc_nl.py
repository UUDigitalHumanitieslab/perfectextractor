import glob
import os

from lxml import etree

import dpc

TEI = {'ns': 'http://www.tei-c.org/ns/1.0'}


def process_folder(dir_name):
    """
    Creates a result file and processes each English file in a folder.
    """
    result_file = dir_name + '.txt'
    with open(result_file, 'w') as f:
        for filename in glob.glob(dir_name + '/*[0-9]-nl-tei.xml'):
            process_file(f, filename)


def process_file(f, filename):
    """
    Processes a single file.
    """
    document = filename.split('nl-tei.xml')[0]
    f.write('Document: ' + document[:-1] + '\n')
    f.write('Original language: ' + dpc.get_original_language(document) + '\n')

    tree = etree.parse(filename)
    found = False
    for e in tree.xpath('//ns:w[@ana="WW(pv,tgw,met-t)" and @lemma="hebben"]', namespaces=TEI):
        pp = dpc.check_present_perfect(e, 'WW(vd,vrij,zonder)', False)

        if pp:
            found = True
            f.write('Present perfect: ' + ' '.join(pp) + '\n')

            # Write the complete segment with mark-up
            f.write(dpc.get_marked_sentence(e, pp).encode('utf-8') + '\n')

            # Find the translated lines
            seg_n = e.getparent().getparent().get('n')[4:]
            translated_lines = dpc.get_translated_lines(document, seg_n)
            if translated_lines:
                translated_tree = etree.parse(document + 'en-tei.xml')
                for t in translated_lines:
                    #f.write(get_line_by_number(translated_tree, get_adjacent_line_number(t, -1)) + '\n')
                    f.write(dpc.get_line_by_number(translated_tree, t) + '\n')
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
    process_folder('data/gru')
