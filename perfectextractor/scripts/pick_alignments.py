import argparse

from lxml import etree


def remove_alignments(tree, search_string):
    """
    Removes all linkGrp-tags that do not contain the provided search string.
    :param tree: the current XML tree
    :param search_string: the search string
    :return: The tree with linkGrp-tags removed that do not contain the search string
    """
    for linkGrp in tree.xpath('//linkGrp[not(contains(@fromDoc, "{}"))]'.format(search_string)):
        linkGrp.getparent().remove(linkGrp)
    return tree


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('file_in', help='Input file')
    parser.add_argument('file_out', help='Output file')
    parser.add_argument('search_string', help='Search string')
    args = parser.parse_args()

    in_tree = etree.parse(args.file_in)
    out_tree = remove_alignments(in_tree, args.search_string)
    doctype = in_tree.docinfo.doctype.replace('>', ' "">')  # Re-add the space that lxml deletes during parsing.
    out_tree.write(args.file_out, pretty_print=True, xml_declaration=True,
                   encoding=in_tree.docinfo.encoding,
                   doctype=doctype)
