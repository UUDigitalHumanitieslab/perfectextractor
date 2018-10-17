import os
import time

import click

from corpora.bnc.extractor import BNCExtractor, BNCPerfectExtractor
from corpora.dpc.extractor import DPCExtractor, DPCPerfectExtractor
from corpora.europarl.extractor import EuroparlExtractor, EuroparlPerfectExtractor, EuroparlRecentPastExtractor
from apps.extractor.utils import TXT, XML

# Corpora
BNC = 'bnc'
DPC = 'dpc'
EUROPARL = 'europarl'

# Extractor types
BASE = 'base'
PERFECT = 'perfect'
RECENT_PAST = 'recent_past'


def process_data_folders(extractor, path):
    for directory in extractor.list_directories(path):
        t0 = time.time()
        click.echo('Now processing {} for {}'.format(directory, extractor.l_from))
        extractor.process_folder(directory)
        click.echo('Processing finished, took {:.3} seconds'.format(time.time() - t0))


@click.command()
@click.argument('folder')
@click.argument('language_from')
@click.argument('languages_to', nargs=-1)  # nargs=-1 eats up all remaining arguments
@click.option('--corpus', default=EUROPARL, type=click.Choice([EUROPARL, DPC, BNC]), help='Which type of corpus to use')
@click.option('--extractor', default=BASE, type=click.Choice([BASE, PERFECT, RECENT_PAST]), help='Which kind of extractor to use')
@click.option('--file_names', '-f', multiple=True, help='Limits the file names searched into')
@click.option('--sentence_ids', '-s', multiple=True, help='Limits the sentence IDs searched into')
@click.option('--search_in_to', is_flag=True, help='Search in to?')
@click.option('--output', default=TXT, type=click.Choice([TXT, XML]), help='Output in text or XML format')
@click.option('--sort_by_certainty', is_flag=True, help='Sort by certainty?')
@click.option('--file_limit', default=0, help='Limit number of files searched')
@click.option('--min_file_size', default=0, help='Limits the minimal size of the files searched')
@click.option('--max_file_size', default=0, help='Limits the maximal size of the files searched')
def extract(folder, language_from, languages_to, corpus='europarl', extractor='base', file_names=None, sentence_ids=None,
            search_in_to=False, output=TXT, sort_by_certainty=False, file_limit=0, min_file_size=0, max_file_size=0):
    # Set the default arguments
    kwargs = dict(output=output, file_names=file_names, sentence_ids=sentence_ids,
                  sort_by_certainty=sort_by_certainty, file_limit=file_limit,
                  min_file_size=min_file_size, max_file_size=max_file_size)

    # Determine the extractor to be used
    # TODO: add more varieties
    resulting_extractor = None
    if corpus == EUROPARL:
        if extractor == PERFECT:
            resulting_extractor = EuroparlPerfectExtractor
        elif extractor == RECENT_PAST:
            resulting_extractor = EuroparlRecentPastExtractor
        else:
            resulting_extractor = EuroparlExtractor
    elif corpus == DPC:
        if extractor == PERFECT:
            resulting_extractor = DPCPerfectExtractor
        elif extractor == RECENT_PAST:
            raise click.ClickException('Corpus or extractor type not implemented!')
        else:
            raise click.ClickException('Corpus or extractor type not implemented!')
    elif corpus == BNC:
        if extractor == PERFECT:
            resulting_extractor = BNCPerfectExtractor
        elif extractor == RECENT_PAST:
            raise click.ClickException('Corpus or extractor type not implemented!')
        else:
            resulting_extractor = BNCExtractor

    if extractor == PERFECT:
        kwargs['search_in_to'] = search_in_to

    if not resulting_extractor:
        raise click.ClickException('Unknown value for either corpus or extractor type')

    # Start the extraction!
    process_data_folders(resulting_extractor(language_from, languages_to, **kwargs), folder)


if __name__ == "__main__":
    extract()


# TODO:
# switch between perfect, recentpast, pos, word
# dependent on this choice, add other questions
# allow output to .xlsx
