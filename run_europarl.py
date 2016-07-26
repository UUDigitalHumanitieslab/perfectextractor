import os
import time

from extractor.europarl import PerfectExtractor


def process_data_folders(extractors, path):
    for extractor in extractors:
        for directory in os.listdir(path):
            d = os.path.join(path, directory)
            if os.path.isdir(d) and d.endswith(extractor.l_from):
                t0 = time.time()
                print 'Now processing {} for {}'.format(d, extractor.l_from)
                extractor.process_folder(d)
                print 'Processing finished, took {:.3} seconds'.format(time.time() - t0)


def create_extractors():
    de_extractor = PerfectExtractor('de', ['en', 'es', 'fr', 'nl'])
    en_extractor = PerfectExtractor('en', ['de', 'es', 'fr', 'nl'])
    es_extractor = PerfectExtractor('es', ['de', 'en', 'fr', 'nl'])
    fr_extractor = PerfectExtractor('fr', ['de', 'en', 'es', 'nl'])
    nl_extractor = PerfectExtractor('nl', ['de', 'en', 'es', 'fr'])
    return [de_extractor, en_extractor, es_extractor, nl_extractor, fr_extractor]
    # return [fr_extractor]

if __name__ == "__main__":
    process_data_folders(create_extractors(), 'data')
