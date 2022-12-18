import os

from perfectextractor.apps.extractor.continuousextractor import ContinuousExtractor
from .extractor import OPUSExtractor


class OPUSContinuousExtractor(OPUSExtractor, ContinuousExtractor):
    def get_config(self):
        continuous_config = os.path.join(os.path.dirname(__file__), 'continuous.cfg')
        return [super().get_config(), continuous_config]

    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        """
        Processes a single file.
        """
        results = []
        # Find potential (present/past) continuous (per sentence)
        for _, s in s_trees:
            for w in s.xpath(self.config.get(self.l_from, 'cont_xpath')):
                continuous = self.check_continuous(w, self.l_from)

                if continuous:
                    result = self.generate_result_line(filename, s, mwe=continuous)
                    result.extend(self.generate_translations(alignment_trees, translation_trees, s))
                    results.append(result)

        return results

    def get_type(self, sentence, mwe=None):
        return 'present continuous'
