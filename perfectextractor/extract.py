import time

import click

from perfectextractor.corpora.bnc.extractor import BNCExtractor
from perfectextractor.corpora.bnc.perfect import BNCPerfectExtractor
from perfectextractor.corpora.bnc.pos import BNCPoSExtractor
from perfectextractor.corpora.dpc.extractor import DPCExtractor
from perfectextractor.corpora.dpc.perfect import DPCPerfectExtractor
from perfectextractor.corpora.dpc.pos import DPCPoSExtractor
from perfectextractor.corpora.opus.extractor import OPUSExtractor
from perfectextractor.corpora.opus.perfect import OPUSPerfectExtractor
from perfectextractor.corpora.opus.pos import OPUSPoSExtractor
from perfectextractor.corpora.opus.recentpast import OPUSRecentPastExtractor
from perfectextractor.corpora.opus.since import OPUSSinceDurationExtractor
from perfectextractor.apps.extractor.utils import TXT, XML, CSV, XLSX
from perfectextractor.apps.extractor.perfectextractor import PRESENT, PAST

# Corpora
BNC = 'bnc'
DPC = 'dpc'
OPUS = 'opus'

# Extractor types
BASE = 'base'
POS = 'pos'
PERFECT = 'perfect'
RECENT_PAST = 'recent_past'
SINCE_DURATION = 'since_duration'


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
@click.option('--corpus', default=OPUS, type=click.Choice([OPUS, DPC, BNC]),
              help='Which type of corpus to use')
@click.option('--extractor', default=BASE, type=click.Choice([BASE, POS, PERFECT, RECENT_PAST, SINCE_DURATION]),
              help='Which kind of extractor to use')
@click.option('--file_names', '-f', multiple=True,
              help='Limits the file names searched into')
@click.option('--sentence_ids', '-s', multiple=True,
              help='Limits the sentence IDs searched into')
@click.option('--lemmata', '-l', multiple=True,
              help='Limits the lemmata searched for')
@click.option('--regex', '-r', multiple=True,
              help='Use regular expression to match words')
@click.option('--pos', '-p', multiple=True,
              help='Limits the POS-tags searched for')
@click.option('--tokens', '-t', multiple=True, type=click.Tuple([str, str]),
              help='Limits the tokens searched for. Format: -t [start_token] [end_token]')
@click.option('--metadata', '-m', multiple=True, type=click.Tuple([str, str]),
              help='Adds additional metadata. Format: -m [tag] [level]')
@click.option('--outfile', '-o',
              help='Output file')
@click.option('--position', default=0,
              help='The position of the searched item')
@click.option('--search_in_to', is_flag=True,
              help='Also search for perfects in the to language(s)?')
@click.option('--tense', default=PRESENT, type=click.Choice([PRESENT, PAST]),
              help='The tense of perfect (present, past, future)')
@click.option('--output', default=TXT, type=click.Choice([TXT, XML]),
              help='Output results in text or XML format')
@click.option('--format', 'format_', default=CSV, type=click.Choice([CSV, XLSX]),
              help='Output file in .csv or .xlsx format')
@click.option('--one_per_sentence', is_flag=True,
              help='Output all sentences, and only one classification per sentence')
@click.option('--sort_by_certainty', is_flag=True,
              help='Sort by certainty?')
@click.option('--file_limit', default=0,
              help='Limit number of files searched')
@click.option('--min_file_size', default=0,
              help='Limits the minimal size of the files searched')
@click.option('--max_file_size', default=0,
              help='Limits the maximal size of the files searched')
def extract(folder, language_from, languages_to, corpus='opus', extractor='base',
            pos=None, search_in_to=False, tense=PRESENT,
            output=TXT, format_=CSV, file_names=None, sentence_ids=None,
            lemmata=None, regex=None, position=None, tokens=None, metadata=None,
            outfile=None, one_per_sentence=False, sort_by_certainty=False, file_limit=0,
            min_file_size=0, max_file_size=0):
    # Set the default arguments
    kwargs = dict(output=output, file_names=file_names, sentence_ids=sentence_ids,
                  lemmata=lemmata, regex=regex, position=position, tokens=tokens, metadata=metadata,
                  outfile=outfile, format_=format_, one_per_sentence=one_per_sentence,
                  sort_by_certainty=sort_by_certainty, file_limit=file_limit,
                  min_file_size=min_file_size, max_file_size=max_file_size)

    # Determine the extractor to be used
    # TODO: add more varieties
    resulting_extractor = None
    if corpus == OPUS:
        if extractor == POS:
            resulting_extractor = OPUSPoSExtractor
        elif extractor == PERFECT:
            resulting_extractor = OPUSPerfectExtractor
        elif extractor == RECENT_PAST:
            resulting_extractor = OPUSRecentPastExtractor
        elif extractor == SINCE_DURATION:
            resulting_extractor = OPUSSinceDurationExtractor
        else:
            resulting_extractor = OPUSExtractor
    elif corpus == DPC:
        if extractor == POS:
            resulting_extractor = DPCPoSExtractor
        elif extractor == PERFECT:
            resulting_extractor = DPCPerfectExtractor
        elif extractor == RECENT_PAST:
            raise click.ClickException('Corpus or extractor type not implemented!')
        elif extractor == SINCE_DURATION:
            raise click.ClickException('Corpus or extractor type not implemented!')
        else:
            resulting_extractor = DPCExtractor
    elif corpus == BNC:
        if extractor == POS:
            resulting_extractor = BNCPoSExtractor
        elif extractor == PERFECT:
            resulting_extractor = BNCPerfectExtractor
        elif extractor == RECENT_PAST:
            raise click.ClickException('Corpus or extractor type not implemented!')
        elif extractor == SINCE_DURATION:
            raise click.ClickException('Corpus or extractor type not implemented!')
        else:
            resulting_extractor = BNCExtractor

    if extractor == PERFECT:
        kwargs['search_in_to'] = search_in_to
        kwargs['tense'] = tense

    if extractor == POS:
        kwargs['pos'] = pos

    if not resulting_extractor:
        raise click.ClickException('Unknown value for either corpus or extractor type')

    # Start the extraction!
    process_data_folders(resulting_extractor(language_from, languages_to, **kwargs), folder)


if __name__ == "__main__":
    extract()
