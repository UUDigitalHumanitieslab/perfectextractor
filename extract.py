import os
import time

import click

from corpora.europarl.extractor import EuroparlPerfectExtractor, EuroparlExtractor
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
@click.option('--extractor', default='base', type=click.Choice(['base', 'perfect']), help='Which kind of extractor to use')
@click.option('--file_names', '-f', multiple=True, help='Limits the file names searched into')
@click.option('--sentence_ids', '-s', multiple=True, help='Limits the sentence IDs searched into')
@click.option('--search_in_to', is_flag=True, help='Search in to?')
@click.option('--output', default=TXT, type=click.Choice([TXT, XML]), help='Output in text or XML format')
@click.option('--sort_by_certainty', is_flag=True, help='Sort by certainty?')
@click.option('--file_limit', default=0, help='Limit number of files searched')
@click.option('--min_file_size', default=0, help='Limits the minimal size of the files searched')
@click.option('--max_file_size', default=0, help='Limits the maximal size of the files searched')
def extract(folder, language_from, languages_to, extractor='base', file_names=None, sentence_ids=None,
            search_in_to=False, output=TXT, sort_by_certainty=False, file_limit=0, min_file_size=0, max_file_size=0):
    # Set the default arguments
    kwargs = dict(output=output, file_names=file_names, sentence_ids=sentence_ids,
                  sort_by_certainty=sort_by_certainty, file_limit=file_limit,
                  min_file_size=min_file_size, max_file_size=max_file_size)

    # Determine the extractor to be used
    # TODO: add more varieties
    e = EuroparlPerfectExtractor if extractor == 'perfect' else EuroparlExtractor
    if extractor == 'perfect':
        kwargs['search_in_to'] = search_in_to

    # Start the extraction!
    extractor = e(language_from, languages_to, **kwargs)
    process_data_folders(extractor, folder)


if __name__ == "__main__":
    extract()


# TODO:
# switch between europarl, dpc, bnc
# switch between perfect, recentpast, pos, word
# dependent on this choice, add other questions
# allow output to .xlsx
