import time

import click

from perfectextractor.apps.extractor.utils import CSV, XLSX
from perfectextractor.corpora.bnc.counter import BNCCounter
from perfectextractor.corpora.opus.counter import OPUSCounter

# Corpora
BNC = 'bnc'
DPC = 'dpc'
OPUS = 'opus'


def process_data_folders(counter, path):
    for directory in counter.list_directories(path):
        t0 = time.time()
        click.echo('Now processing {} for {}'.format(directory, counter.l_from))
        counter.process_folder(directory)
        click.echo('Processing finished, took {:.3} seconds'.format(time.time() - t0))


@click.command()
@click.argument('folder')
@click.argument('language')
@click.option('--corpus', default=OPUS, type=click.Choice([OPUS, DPC, BNC]),
              help='Which type of corpus to use')
@click.option('--outfile', '-o',
              help='Output file')
@click.option('--format', 'format_', default=CSV, type=click.Choice([CSV, XLSX]),
              help='Output file in .csv or .xlsx format')
def count(folder, language, corpus=OPUS, outfile=None, format_=CSV):
    # Set the default arguments
    kwargs = dict(outfile=outfile, format_=format_)

    # Determine the counter to be used
    resulting_counter = None
    if corpus == OPUS:
        resulting_counter = OPUSCounter
    elif corpus == BNC:
        resulting_counter = BNCCounter

    if not resulting_counter:
        raise click.ClickException('Unknown value for either corpus or counter type')

    # Start the count!
    process_data_folders(resulting_counter(language, **kwargs), folder)


if __name__ == "__main__":
    count()
