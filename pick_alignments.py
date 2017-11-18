import argparse

from lxml import etree


def remove_alignments(tree, search_string):
    for linkGrp in tree.xpath('//linkGrp[not(contains(@fromDoc, "{}"))]'.format(search_string)):
        linkGrp.getparent().remove(linkGrp)
    return tree


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('file_in', type=str, help='Input file')
    parser.add_argument('file_out', type=str, help='Output file')
    parser.add_argument('search_string', type=str, help='Search string')
    args = parser.parse_args()

    in_tree = etree.parse(args.file_in)
    out_tree = remove_alignments(in_tree, args.search_string)
    out_tree.write(args.file_out, pretty_print=True, xml_declaration=True, encoding='utf-8')
