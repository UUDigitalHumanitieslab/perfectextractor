import os
import time

from corpora.bnc.extractor import BNCPerfectExtractor
from corpora.bnc.counter import BNCCounter


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
    en_counter = BNCCounter('en')
    en_extractor = BNCPerfectExtractor('en')
    return [en_counter, en_extractor]


if __name__ == "__main__":
    process_data_folders(create_extractors(), '/home/martijn/Documents/Corpora/BNC/2554/download/Texts/A')
    process_data_folders(create_extractors(), '/home/martijn/Documents/Corpora/BNC/2554/download/Texts/B')
    process_data_folders(create_extractors(), '/home/martijn/Documents/Corpora/BNC/2554/download/Texts/C')
    process_data_folders(create_extractors(), '/home/martijn/Documents/Corpora/BNC/2554/download/Texts/D')
    process_data_folders(create_extractors(), '/home/martijn/Documents/Corpora/BNC/2554/download/Texts/E')
    process_data_folders(create_extractors(), '/home/martijn/Documents/Corpora/BNC/2554/download/Texts/F')
    process_data_folders(create_extractors(), '/home/martijn/Documents/Corpora/BNC/2554/download/Texts/G')
    process_data_folders(create_extractors(), '/home/martijn/Documents/Corpora/BNC/2554/download/Texts/H')
    process_data_folders(create_extractors(), '/home/martijn/Documents/Corpora/BNC/2554/download/Texts/J')
    process_data_folders(create_extractors(), '/home/martijn/Documents/Corpora/BNC/2554/download/Texts/K')
