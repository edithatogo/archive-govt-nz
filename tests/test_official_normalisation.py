"""Real-source anchors and adversarial controls for the pinned official cohort."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get('SOC_ORIGINALS', str(ROOT.parent/'official')))

class OfficialNormalisationTests(unittest.TestCase):
    def setUp(self):
        path = ROOT/'tools/normalise_soc_official.py'
        self.assertTrue(path.exists(), 'official normalisation implementation missing')
        spec=importlib.util.spec_from_file_location('normalise_soc_official',path)
        self.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.mod)
        self.profiles=self.mod.load_profiles(ROOT/'data/soc-official-profiles.json')
        self.capture=json.loads((DATA/'manifest.json').read_text())
    def census(self,key='census2023_general_2020'):
        p=self.profiles['cohorts'][key]
        return self.mod.normalise_census(json.loads((DATA/(key+'.cells.json')).read_text()),p)
    def test_real_income_cell_anchor_and_mean_median_distinction(self):
        rows=self.census()
        r=next(r for r in rows if r['geography_name']=='Auckland Central' and r['category']=='Median Personal Income')
        self.assertEqual(r['value'],'44900'); self.assertEqual(r['cell'],'C3')
        self.assertEqual(r['measurement_kind'],'median');self.assertEqual(r['boundary_vintage'],'2020')
        self.assertFalse(r['synthetic']);self.assertEqual(r['source_published_at'],None)
    def test_direct_boundary_cohort_counts(self):
        expected={'census2023_general_2020':65,'census2023_general_2025':64,'census2023_maori_2020':7,'census2023_maori_2025':7}
        for key,n in expected.items():
            with self.subTest(key=key):
                areas={r['geography_name'] for r in self.census(key) if r['area_role']=='electorate'}
                self.assertEqual(len(areas),n)
    def test_preserves_suppression_and_zero(self):
        rows=self.census()
        withheld=[r for r in rows if r['raw_token']=='..C']
        self.assertTrue(withheld);self.assertTrue(all(r['value'] is None and r['status']=='suppressed' for r in withheld))
        zero=[r for r in rows if r['value']=='0'];self.assertTrue(zero)
        self.assertTrue(all(r['status']=='observed' for r in zero))
    def test_maori_descent_is_not_mislabeled_roll_population(self):
        rows=self.census('census2023_maori_2025')
        self.assertTrue(all('Māori descent' in r['publisher_population_note'] for r in rows))
        self.assertTrue(all(r['electoral_roll_population'] is False for r in rows))
    def test_header_order_changes_are_not_silently_accepted(self):
        key='census2023_general_2020';d=json.loads((DATA/(key+'.cells.json')).read_text())
        s=next(s for s in d['sheets'] if s['name']=='Personal income')
        next(c for c in s['cells'] if c[0]=='B2')[2]='Changed statistic'
        with self.assertRaisesRegex(ValueError,'header'):
            self.mod.normalise_census(d,self.profiles['cohorts'][key])
    def test_formula_is_not_accepted_as_empirical_observation(self):
        key='census2023_general_2020';d=json.loads((DATA/(key+'.cells.json')).read_text())
        s=next(s for s in d['sheets'] if s['name']=='Personal income')
        next(c for c in s['cells'] if c[0]=='C3')[3]='SUM(B3)'
        with self.assertRaisesRegex(ValueError,'formula'):
            self.mod.normalise_census(d,self.profiles['cohorts'][key])
    def test_duplicate_cell_and_unknown_numeric_token_rejected(self):
        key='census2023_general_2020';d=json.loads((DATA/(key+'.cells.json')).read_text());s=next(s for s in d['sheets'] if s['name']=='Personal income');s['cells'].append(s['cells'][-1])
        with self.assertRaisesRegex(ValueError,'duplicate'):
            self.mod.normalise_census(d,self.profiles['cohorts'][key])
        d=json.loads((DATA/(key+'.cells.json')).read_text());s=next(s for s in d['sheets'] if s['name']=='Personal income');next(c for c in s['cells'] if c[0]=='C3')[2]='NaN'
        with self.assertRaises(ValueError):self.mod.normalise_census(d,self.profiles['cohorts'][key])
    def test_wrong_original_identity_rejected(self):
        key='census2023_general_2020';d=json.loads((DATA/(key+'.cells.json')).read_text());d['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'identity'):self.mod.normalise_census(d,self.profiles['cohorts'][key])
    def test_real_turnout_counts_reconcile_national_totals(self):
        d=json.loads((DATA/'turnout2023_age_descent.cells.json').read_text());rows,summary=self.mod.normalise_turnout(d)
        self.assertEqual(len(rows),792);self.assertEqual(summary['electorates'],72)
        self.assertEqual(summary['voters'],2858896);self.assertEqual(summary['enrolled'],3688292)
        au=[r for r in rows if r['geography_name']=='Auckland Central']
        self.assertEqual(sum(r['voters'] for r in au),35270)
        self.assertEqual(sum(r['enrolled'] for r in au),45426)
        self.assertAlmostEqual(au[0]['turnout_percent'],83.19235012872379)
    def test_turnout_bad_denominator_fails(self):
        d=json.loads((DATA/'turnout2023_age_descent.cells.json').read_text());s=d['sheets'][0];next(c for c in s['cells'] if c[0]=='H18')[2]='1'
        with self.assertRaisesRegex(ValueError,'count'):self.mod.normalise_turnout(d)
    def test_whole_artifact_hashes_verify(self):
        self.mod.verify_capture(DATA,self.capture)
        bad=copy.deepcopy(self.capture);bad['records'][0]['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'hash'):self.mod.verify_capture(DATA,bad)

if __name__=='__main__':unittest.main()
