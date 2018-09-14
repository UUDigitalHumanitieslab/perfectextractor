import os
import time

import click

from corpora.europarl.extractor import EuroparlPerfectExtractor
from apps.extractor.utils import TXT, XML


def process_data_folders(extractor, path):
    for directory in os.listdir(path):
        d = os.path.join(path, directory)
        if os.path.isdir(d) and d.endswith(extractor.l_from):
            t0 = time.time()
            click.echo('Now processing {} for {}'.format(d, extractor.l_from))
            extractor.process_folder(d)
            click.echo('Processing finished, took {:.3} seconds'.format(time.time() - t0))


@click.command()
@click.argument('folder')
@click.argument('language_from')
@click.argument('languages_to', nargs=-1)  # nargs=-1 eats up all remaining arguments
@click.option('--search_in_to', default=False, help='Search in to?')
@click.option('--output', default=TXT, type=click.Choice([TXT, XML]), help='Output in text or XML format')
def extract(folder, language_from, languages_to, search_in_to=False, output=TXT):
    extractor = EuroparlPerfectExtractor(language_from, languages_to, search_in_to=search_in_to, output=output)
    process_data_folders(extractor, folder)


if __name__ == "__main__":
    extract()


# TODO:
# switch between europarl, dpc, bnc
# switch between perfect, recentpast, pos, word
# dependent on this choice, add other questions
# allow output to .xlsx
