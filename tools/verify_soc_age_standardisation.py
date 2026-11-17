"""Independent exact-rational controls for real electorate age standardisation."""
from __future__ import annotations
import os
import importlib
import json
import sys
import unittest
from collections import defaultdict
from fractions import Fraction
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
DATA=Path(os.environ.get('SOC_NORMALISED',str(ROOT.parent/'baseline/normalised')))/'turnout-age.json'

class StandardisationTests(unittest.TestCase):
    def api(self):
        try:return importlib.import_module('standardise_soc_turnout')
        except ModuleNotFoundError:self.fail('SOC age standardisation not implemented')
    def rows(self):return json.loads(DATA.read_text())
    def test_real_72_areas_two_explicit_standards(self):
        rows,receipt=self.api().standardise(self.rows())
        self.assertEqual(len(rows),144)
        self.assertEqual(receipt['electorates'],72)
        self.assertEqual({r['standard'] for r in rows},{'national_enrolled_2023','same_roll_system_enrolled_2023'})
        self.assertTrue(all(r['causal_claim'] is False for r in rows))
    def test_independent_exact_fraction_reference_for_all_areas(self):
        result,_=self.api().standardise(self.rows())
        by_area=defaultdict(list)
        for r in self.rows():by_area[r['electorate_number']].append(r)
        for out in result:
            code=out['electorate_number'];target=by_area[code]
            ref=self.rows() if out['standard']=='national_enrolled_2023' else [r for r in self.rows() if (r['electorate_number']>=66)==(code>=66)]
            totals=defaultdict(int)
            for r in ref:totals[r['age_band']]+=r['enrolled']
            total=sum(totals.values())
            expected=sum((Fraction(totals[r['age_band']],total)*Fraction(r['voters'],r['enrolled']) for r in target),Fraction())*100
            self.assertAlmostEqual(float(out['standardised_turnout_percent']),float(expected),places=10)
    def test_raw_rate_uses_summed_counts_not_mean_of_age_rates(self):
        results,_=self.api().standardise(self.rows())
        au=next(r for r in results if r['geography_name']=='Auckland Central')
        self.assertEqual(au['voters'],35270);self.assertEqual(au['enrolled'],45426)
        self.assertAlmostEqual(float(au['raw_turnout_percent']),100*35270/45426,places=10)
    def test_missing_age_stratum_is_rejected(self):
        rows=self.rows();rows.pop()
        with self.assertRaisesRegex(ValueError,'strat'):
            self.api().standardise(rows)
    def test_duplicate_stratum_is_rejected(self):
        rows=self.rows()
        with self.assertRaisesRegex(ValueError,'duplicate'):
            self.api().standardise(rows+rows[:1])
    def test_wrong_boundary_rejected(self):
        rows=self.rows();rows[0]['boundary_vintage']='2025'
        with self.assertRaisesRegex(ValueError,'vintage'):
            self.api().standardise(rows)
    def test_zero_denominator_rejected(self):
        rows=self.rows();rows[0].update(enrolled=0,voters=0,nonvoters=0)
        with self.assertRaisesRegex(ValueError,'denominator'):
            self.api().standardise(rows)
    def test_source_change_rejected(self):
        rows=self.rows();rows[0]['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'source'):
            self.api().standardise(rows)
    def test_area_name_drift_rejected(self):
        rows=self.rows();rows[0]['geography_name']='Unknown'
        with self.assertRaisesRegex(ValueError,'identity'):
            self.api().standardise(rows)
    def test_count_change_requires_national_reconciliation(self):
        rows=self.rows();rows[0]['voters']+=1;rows[0]['nonvoters']-=1
        with self.assertRaisesRegex(ValueError,'national'):
            self.api().standardise(rows)
    def test_source_tuple_is_independently_pinned_at_file_boundary(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            file=Path(d)/'input.json';file.write_bytes(DATA.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'digest'):
                self.api().load_rows(file)
    def test_population_counts_not_census_resident_weights(self):
        rows,receipt=self.api().standardise(self.rows())
        self.assertEqual(receipt['standard_population'],'registered electors in the 2023 turnout workbook')
        self.assertTrue(all(r['age_strata']==11 and r['source_sha256']==receipt['original_sha256'] for r in rows))

if __name__=='__main__':unittest.main()
