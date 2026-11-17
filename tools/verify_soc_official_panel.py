"""Explicit real-data verification; set SOC_NORMALISED to the retained SOC02 output."""
import importlib.util
import json
import os
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=Path(os.environ.get('SOC_NORMALISED',str(ROOT/'build/soc-normalised')))

class PanelTests(unittest.TestCase):
    def setUp(self):
        path=ROOT/'tools/build_soc_official_panel.py'
        spec=importlib.util.spec_from_file_location('panel',path)
        self.mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.mod)
        self.census=json.loads((DATA/'census-long.json').read_text())
        self.turnout=json.loads((DATA/'turnout-age.json').read_text())
    def test_real_72_area_panel(self):
        rows,receipt=self.mod.build_panel(self.census,self.turnout)
        self.assertEqual(len(rows),72);self.assertEqual(receipt['matched'],72)
        self.assertEqual(receipt['unmatched'],[])
        row=next(r for r in rows if r['geography_name']=='Auckland Central')
        self.assertEqual(row['median_personal_income_nzd'],'44900')
        self.assertEqual(row['voters'],35270);self.assertEqual(row['enrolled'],45426)
        self.assertEqual(sum(r['voters'] for r in rows),2858896)
        self.assertEqual(receipt['analysis_mode'],'retrospective_area_context')
    def test_future_boundaries_cannot_fill_historical_panel(self):
        with self.assertRaisesRegex(ValueError,'2020'):
            self.mod.build_panel([r for r in self.census if r['boundary_vintage']=='2025'],self.turnout)
    def test_missing_indicator_retains_target(self):
        rows,receipt=self.mod.build_panel([r for r in self.census if r['geography_name']!='Auckland Central'],self.turnout)
        self.assertEqual(len(rows),72);self.assertIn('Auckland Central',receipt['unmatched'])
        self.assertIsNone(next(r for r in rows if r['geography_name']=='Auckland Central')['median_personal_income_nzd'])
    def test_duplicate_covariate_fails(self):
        row=next(r for r in self.census if r['boundary_vintage']=='2020' and r['category']=='Median Personal Income' and r['area_role']=='electorate')
        with self.assertRaisesRegex(ValueError,'duplicate'):
            self.mod.build_panel(self.census+[row],self.turnout)
    def test_duplicate_age_cannot_inflate_totals(self):
        with self.assertRaisesRegex(ValueError,'duplicate'):
            self.mod.build_panel(self.census,self.turnout+self.turnout[:1])
    def test_no_same_population_claim(self):
        rows,_=self.mod.build_panel(self.census,self.turnout)
        row=next(r for r in rows if r['geography_name']=='Waiariki')
        self.assertEqual(row['population_relationship'],'different_populations_same_area_context')
        self.assertFalse(row['causal_claim']);self.assertIsNone(row['source_published_at'])

if __name__=='__main__':unittest.main()
