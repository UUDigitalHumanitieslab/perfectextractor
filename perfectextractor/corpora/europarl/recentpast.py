import os

from perfectextractor.apps.extractor.recentpastextractor import RecentPastExtractor
from .extractor import EuroparlExtractor


class EuroparlRecentPastExtractor(EuroparlExtractor, RecentPastExtractor):
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

    def mark_sentence(self, sentence, match=None):
        s = []
        # TODO: this xPath-expression might be specific for a corpus
        for w in sentence.xpath('.//w'):
            s.append(w.text.strip() if w.text else ' ')
        return ' '.join(s)

    def get_type(self, sentence, words=None, mwe=None):
        return 'passé récent'
