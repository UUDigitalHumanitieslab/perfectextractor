import os

from perfectextractor.apps.extractor.recentpastextractor import RecentPastExtractor
from .extractor import OPUSExtractor


class OPUSRecentPastExtractor(OPUSExtractor, RecentPastExtractor):
    def get_config(self):
        perfect_config = os.path.join(os.path.dirname(__file__), 'perfect.cfg')
        rp_config = os.path.join(os.path.dirname(__file__), 'recentpast.cfg')
        return [super().get_config(), perfect_config, rp_config]

    def fetch_results(self, filename, s_trees, alignment_trees, translation_trees):
        """
        Processes a single file.
        """
        results = []
        # Find potential recent pasts (per sentence)
        for _, s in s_trees:
            for w in s.xpath(self.config.get(self.l_from, 'rp_xpath')):
                rp = self.check_recent_past(w, self.l_from)

                if rp:
                    result = self.generate_result_line(filename, s, mwe=rp)
                    result.extend(self.generate_translations(alignment_trees, translation_trees, s))
                    results.append(result)

        return results

    def get_type(self, sentence, mwe=None):
        return 'passé récent'
