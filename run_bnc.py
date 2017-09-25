import os
import time

from extractor.bnc import BNCPerfectExtractor


def process_data_folders(extractors, path):
    for extractor in extractors:
        for directory in os.listdir(path):
            d = os.path.join(path, directory)
            if os.path.isdir(d):
                t0 = time.time()
                print 'Now processing {} for {}'.format(d, extractor.l_from)
                extractor.process_folder(d)
                print 'Processing finished, took {:.3} seconds'.format(time.time() - t0)


def create_extractors():
    en_extractor = BNCPerfectExtractor('en', lemmata=['see', 'hear', 'touch', 'feel', 'taste'])
    return [en_extractor]


if __name__ == "__main__":
    process_data_folders(create_extractors(), 'data')
