import os
import time

from extractor.europarl import EuroparlPerfectExtractor


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
    #en_extractor = EuroparlPerfectExtractor('en', ['de', 'fr', 'nl'], search_in_to=False, lemmata=True)
    nl_extractor = EuroparlPerfectExtractor('nl', ['de', 'en', 'fr'], search_in_to=False, lemmata=True)
    return [nl_extractor]
    # return [de_extractor]

if __name__ == "__main__":
    process_data_folders(create_extractors(), 'data')
