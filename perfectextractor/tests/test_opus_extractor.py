# -*- coding: utf-8 -*-

import os
import unittest

from lxml import etree

from perfectextractor.apps.extractor.perfectextractor import PAST
from perfectextractor.corpora.opus.article import OPUSFrenchArticleExtractor
from perfectextractor.corpora.opus.extractor import OPUSExtractor
from perfectextractor.corpora.opus.perfect import OPUSPerfectExtractor
from perfectextractor.corpora.opus.pos import OPUSPoSExtractor
from perfectextractor.corpora.opus.recentpast import OPUSRecentPastExtractor
from perfectextractor.corpora.opus.since import OPUSSinceDurationExtractor

EUROPARL_DATA = os.path.join(os.path.dirname(__file__), 'data/europarl')
DCEP_DATA = os.path.join(os.path.dirname(__file__), 'data/dcep')
SWITCHBOARD_DATA = os.path.join(os.path.dirname(__file__), 'data/switchboard')


class TestEuroparlPerfectExtractor(unittest.TestCase):
    def setUp(self):
        self.nl_filename = os.path.join(EUROPARL_DATA, 'nl/ep-00-12-15.xml')
        self.en_filename = os.path.join(EUROPARL_DATA, 'en/ep-00-12-15.xml')
        self.fr_filename = os.path.join(EUROPARL_DATA, 'fr/ep-00-12-15.xml')

        self.nl_extractor = OPUSPerfectExtractor('nl', ['en'], search_in_to=True)
        self.nl_tree = etree.parse(self.nl_filename)
        self.nl_alignmenttrees, self.nl_translationtrees = self.nl_extractor.parse_alignment_trees(self.nl_filename)

        self.en_extractor = OPUSPerfectExtractor('en', ['nl'], search_in_to=True)
        self.en_tree = etree.parse(self.en_filename)
        self.en_alignmenttrees, self.en_translationtrees = self.en_extractor.parse_alignment_trees(self.en_filename)

    def merge_results(self, generator):
        return sum(list(generator), [])

    def test_init(self):
        self.assertEqual(self.nl_extractor.config.get('nl', 'perfect_tags'), 'verbpapa')
        self.assertIn('dunken', self.nl_extractor.aux_be_list['nl'])

    def test_get_translated_lines(self):
        from_lines, to_lines, align = self.nl_extractor.get_translated_lines(self.nl_alignmenttrees, 'nl', 'en', '17')
        self.assertEqual(from_lines, ['17'])
        self.assertEqual(to_lines, ['11'])
        self.assertEqual(align, '1 => 1')

        from_lines, to_lines, align = self.nl_extractor.get_translated_lines(self.nl_alignmenttrees, 'nl', 'en', '18')
        self.assertEqual(from_lines, ['18', '19'])
        self.assertEqual(to_lines, ['12'])
        self.assertEqual(align, '2 => 1')

        from_lines, to_lines, align = self.nl_extractor.get_translated_lines(self.nl_alignmenttrees, 'nl', 'en', '57')
        self.assertEqual(from_lines, ['57'])
        self.assertEqual(to_lines, ['46', '47'])
        self.assertEqual(align, '1 => 2')

        from_lines, to_lines, align = self.nl_extractor.get_translated_lines(self.nl_alignmenttrees, 'nl', 'en', '9')
        self.assertEqual(from_lines, ['9'])
        self.assertEqual(to_lines, [])
        self.assertEqual(align, '')

        from_lines, to_lines, align = self.en_extractor.get_translated_lines(self.en_alignmenttrees, 'en', 'nl', '19')
        self.assertEqual(from_lines, ['19'])
        self.assertEqual(to_lines, ['27'])
        self.assertEqual(align, '1 => 1')

        from_lines, to_lines, align = self.en_extractor.get_translated_lines(self.en_alignmenttrees, 'en', 'nl', '8')
        self.assertEqual(from_lines, ['8'])
        self.assertEqual(to_lines, ['13', '14'])
        self.assertEqual(align, '1 => 2')

        from_lines, to_lines, align = self.en_extractor.get_translated_lines(self.en_alignmenttrees, 'en', 'nl', '234')
        self.assertEqual(from_lines, ['234', '235'])
        self.assertEqual(to_lines, ['290'])
        self.assertEqual(align, '2 => 1')

    def test_get_line_by_number(self):
        xml_sentence, _, pp = self.nl_extractor.get_line_and_pp(self.nl_tree, 'nl', '4')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '4')
        self.assertEqual(pp.construction(), ['is', 'aangebroken'])
        self.assertEqual(pp.construction_ids(), 'w4.9 w4.19')
        self.assertEqual(pp.words_between(), 9)
        self.assertFalse(pp.is_passive)
        self.assertFalse(pp.is_continuous)

        xml_sentence, _, pp = self.nl_extractor.get_line_and_pp(self.nl_tree, 'nl', '15')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '15')
        self.assertEqual(pp.construction(), ['heeft', 'bemoeid'])
        self.assertEqual(pp.words_between(), 0)
        self.assertFalse(pp.is_passive)
        self.assertFalse(pp.is_continuous)

        xml_sentence, _, pp = self.nl_extractor.get_line_and_pp(self.nl_translationtrees['en'], 'en', '6')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '6')
        self.assertEqual(pp.construction(), ['has', 'said'])
        self.assertEqual(pp.words_between(), 1)
        self.assertFalse(pp.is_passive)
        self.assertFalse(pp.is_continuous)

        xml_sentence, _, pp = self.en_extractor.get_line_and_pp(self.en_tree, 'en', '89')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '89')
        self.assertEqual(pp.construction(), ['has', 'been', 'mentioned'])
        self.assertEqual(pp.words_between(), 1)
        self.assertEqual(pp.words_between_construction(), [0, 1, 0])
        self.assertTrue(pp.is_passive)
        self.assertFalse(pp.is_continuous)

        xml_sentence, _, pp = self.en_extractor.get_line_and_pp(self.en_tree, 'en', '121')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '121')
        self.assertEqual(pp.construction(), ['has', 'been', 'carrying'])
        self.assertEqual(pp.words_between(), 0)
        self.assertEqual(pp.words_between_construction(), [0, 0, 0])
        self.assertFalse(pp.is_passive)
        self.assertTrue(pp.is_continuous)

        xml_sentence, _, pp = self.en_extractor.get_line_and_pp(self.en_tree, 'en', '180')
        self.assertEqual(etree.fromstring(xml_sentence).get('id'), '180')
        self.assertEqual(pp.construction(), ['has', 'brought'])
        self.assertEqual(pp.words_between(), 1)
        self.assertFalse(pp.is_passive)
        self.assertFalse(pp.is_continuous)

    def test_list_filenames(self):
        files = self.nl_extractor.list_filenames(os.path.join(EUROPARL_DATA, 'nl'))
        self.assertEqual([os.path.basename(f) for f in files], ['ep-00-12-15.xml'])

    def test_recent_past_extraction(self):
        fr_extractor = OPUSRecentPastExtractor('fr', ['en', 'nl'])

        results = list(fr_extractor.process_file(self.fr_filename))
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0][2], u'passé récent')
        self.assertEqual(results[0][3], u'vient de dire')
        self.assertEqual(results[1][3], u'viens d\' aborder')
        self.assertEqual(results[2][3], u'viens d\' évoquer')
        self.assertEqual(results[3][3], u'vient d\' être dit')

    def test_position(self):
        when_extractor = OPUSPoSExtractor('en', ['nl'], lemmata=['when'], position=1)
        results = self.merge_results(when_extractor.generate_results(os.path.join(EUROPARL_DATA, 'en')))
        self.assertEqual(len(results), 3)

    def test_average_alignment_certainty(self):
        extractor = OPUSExtractor('en', ['nl', 'de'])

        file_names = extractor.sort_by_alignment_certainty(extractor.list_filenames(os.path.join(DCEP_DATA, 'en')))
        file_names = [os.path.basename(f) for f in file_names]
        self.assertEqual(file_names[0], '20764633__IM-PRESS__20081211-STO-44307__EN.xml')
        self.assertEqual(file_names[1], '16609396__IM-PRESS__20060905-STO-10339__EN.xml')
        self.assertEqual(file_names[2], '16451293__IM-PRESS__20060131-IPR-04891__EN.xml')

    def test_file_limit(self):
        extractor = OPUSExtractor('en', ['nl', 'de'], file_limit=2)
        results = self.merge_results(extractor.generate_results(os.path.join(DCEP_DATA, 'en')))
        self.assertEqual(len(results), 55)

        extractor = OPUSExtractor('en', ['nl', 'de'], file_limit=1)
        results = self.merge_results(extractor.generate_results(os.path.join(DCEP_DATA, 'en')))
        self.assertEqual(len(results), 37)
        self.assertEqual(results[0][0], u'16451293__IM-PRESS__20060131-IPR-04891__EN.xml')
        self.assertEqual(results[0][1], u's1.1')
        self.assertEqual(results[0][2], u'')
        self.assertEqual(results[0][3], u'')
        self.assertEqual(results[0][4], u'')
        self.assertEqual(results[0][5][:14], u'In reaction to')

    def test_lemmata(self):
        extractor = OPUSPerfectExtractor('fr', ['nl'], lemmata=['être'])
        results = self.merge_results(extractor.generate_results(os.path.join(EUROPARL_DATA, 'fr')))
        self.assertEqual(len(results), 25)
        self.assertEqual(results[0][2], u'present perfect')
        self.assertEqual(results[0][3], u'a été')
        self.assertEqual(results[1][3], u'ont été')
        self.assertEqual(results[2][3], u'a été')
        self.assertEqual(results[3][3], u'a été')

    def test_sentence_filtering(self):
        extractor = OPUSPerfectExtractor('fr', ['nl'], lemmata=['être'], sentence_ids=['69', '65'])
        results = self.merge_results(extractor.generate_results(os.path.join(EUROPARL_DATA, 'fr')))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][1], u'65')
        self.assertEqual(results[1][1], u'69')

    def test_regex(self):
        # Primitive search for wh-questions
        regex_extractor = OPUSPoSExtractor('en', ['nl'], regex=['^wh.*', '^how$'], position=1)
        results = self.merge_results(regex_extractor.generate_results(os.path.join(EUROPARL_DATA, 'en')))
        self.assertEqual(len(results), 12)
        self.assertEqual(results[0][3], u'How')
        self.assertEqual(results[1][3], u'How')
        self.assertEqual(results[2][3], u'What')
        self.assertEqual(results[3][3], u'When')

    def test_regex_and_pos(self):
        # Primitive search for wh-questions
        regex_extractor = OPUSPoSExtractor('en', ['nl'], regex=['^wh.*'], pos=['WP'], position=1)
        results = self.merge_results(regex_extractor.generate_results(os.path.join(EUROPARL_DATA, 'en')))
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0][2], u'WP')
        self.assertEqual(results[0][3], u'What')
        self.assertEqual(results[1][3], u'What')
        self.assertEqual(results[2][3], u'What')
        self.assertEqual(results[3][3], u'What')

    def test_tokens(self):
        tokens_extractor = OPUSPoSExtractor('en', ['nl'], tokens=[('w1.13', 'w1.15'), ('w2.5', 'w2.8')])
        results = self.merge_results(tokens_extractor.generate_results(os.path.join(EUROPARL_DATA, 'en')))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][3], u'a historic sitting')
        self.assertEqual(results[1][3], u'my very great pleasure')

        tokens_extractor = OPUSPoSExtractor('en', ['nl'], tokens=[('w1.19', 'w1.17')])
        generator = tokens_extractor.generate_results(os.path.join(EUROPARL_DATA, 'en'))
        self.assertRaises(ValueError, next, generator)

    def test_metadata(self):
        metadata_extractor = OPUSPoSExtractor('en', [], lemmata=['when'],
                                              metadata=[('topic', 'text'), ('damsl_act_tag', 's')])
        results = self.merge_results(metadata_extractor.generate_results(os.path.join(SWITCHBOARD_DATA, 'en')))
        self.assertEqual(len(results), 5)
        self.assertEqual(results[0][6], u'CHILD CARE')
        self.assertEqual(results[0][7], u'sd')
        self.assertEqual(results[4][7], u'qy')

    def test_since(self):
        metadata_extractor = OPUSSinceDurationExtractor('nl', [])
        results = self.merge_results(metadata_extractor.generate_results(os.path.join(EUROPARL_DATA, 'nl')))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][2], u'prep')
        self.assertEqual(results[0][3], u'sinds tien jaar')

    def test_articles(self):
        article_extractor = OPUSFrenchArticleExtractor('fr', [])
        results = self.merge_results(article_extractor.generate_results(os.path.join(EUROPARL_DATA, 'fr')))
        self.assertEqual(len(results), 2041)
        self.assertEqual(results[0][2], u'indefinite partitive')

    def test_past_perfect(self):
        past_perfect_extractor = OPUSPerfectExtractor('en', [], tense=PAST)
        results = self.merge_results(past_perfect_extractor.generate_results(os.path.join(EUROPARL_DATA, 'en')))
        self.assertEqual(len(results), 5)
        self.assertEqual(results[0][3], u'had preordained')

        past_perfect_extractor = OPUSPerfectExtractor('nl', [], tense=PAST)
        results = self.merge_results(past_perfect_extractor.generate_results(os.path.join(EUROPARL_DATA, 'nl')))
        self.assertEqual(len(results), 5)
        self.assertEqual(results[0][3], u'had gelegd')

        past_perfect_extractor = OPUSPerfectExtractor('fr', [], tense=PAST)
        results = self.merge_results(past_perfect_extractor.generate_results(os.path.join(EUROPARL_DATA, 'fr')))
        self.assertEqual(len(results), 9)
        self.assertEqual(results[0][3], u'avait rétabli')

        past_perfect_extractor = OPUSPerfectExtractor('de', [], tense=PAST)
        results = self.merge_results(past_perfect_extractor.generate_results(os.path.join(DCEP_DATA, 'de')))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][3], u'hatte beschlossen')

        past_perfect_extractor = OPUSPerfectExtractor('sv', [], tense=PAST)
        results = self.merge_results(past_perfect_extractor.generate_results(os.path.join(EUROPARL_DATA, 'sv')))
        self.assertEqual(len(results), 7)
        self.assertEqual(results[0][3], u'hade kunnat')

    def test_languages(self):
        sv_extractor = OPUSPerfectExtractor('sv', [])
        results = self.merge_results(sv_extractor.generate_results(os.path.join(EUROPARL_DATA, 'sv')))
        self.assertEqual(len(results), 38)
        self.assertEqual(results[0][3], u'har gjort')

    def test_language_without_config(self):
        self.assertRaises(Exception, OPUSPerfectExtractor, 'it', [])
        OPUSPerfectExtractor('en', ['it'])  # should not raise a ValueError
        self.assertRaises(Exception, OPUSPerfectExtractor, 'en', ['it'], {'search_in_to': True})
