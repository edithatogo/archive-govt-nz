"""Real-source extended table tests, with explicit overlapping strata controls."""
from __future__ import annotations
import copy
import importlib
import json
import os
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
ORIGINALS=Path(os.environ.get('SOC_ORIGINALS',str(ROOT.parent/'baseline/originals')))

class ExpandedTests(unittest.TestCase):
    def api(self):
        try:return importlib.import_module('normalise_soc_extended')
        except ModuleNotFoundError:self.fail('Expanded real-source normaliser is not implemented')

    def source(self,key):
        return json.loads((ORIGINALS/(key+'.cells.json')).read_text())

    def test_all_selected_families_are_present(self):
        rows,receipt=self.api().build_census(ORIGINALS)
        self.assertEqual(receipt['cohorts'],4)
        self.assertEqual(receipt['table_families'],22)
        self.assertEqual(receipt['tables'],86)
        self.assertGreater(len(rows),25000)
        self.assertTrue(all(r['synthetic'] is False for r in rows))
        families={r['family_id'] for r in rows}
        self.assertTrue({'industry','occupation','household_composition','landlord_sector','dwelling_occupancy'} <= families)

    def test_new_source_anchor_and_exact_footnotes(self):
        rows,_=self.api().build_census(ORIGINALS)
        row=next(r for r in rows if r['source_id']=='census2023_general_2020' and r['geography_name']=='Auckland Central' and r['sheet']=='Industry' and r['category']=='Health Care and Social Assistance')
        indexed={c[0]:c for c in next(s for s in self.source('census2023_general_2020')['sheets'] if s['name']=='Industry')['cells']}
        self.assertEqual(row['value'],indexed[row['cell']][2])
        self.assertIn('high quality',row['footnote_text'])
        self.assertTrue(row['footnote_cell'].startswith('Variable specific footnotes!B'))

    def test_multiple_response_categories_not_treated_as_partition(self):
        rows,_=self.api().build_census(ORIGINALS)
        samples=[r for r in rows if r['family_id'] in {'personal_income_sources','household_income_sources','unpaid_activities'}]
        self.assertTrue(all(r['response_mode']=='multiple_response' and not r['categories_additive'] for r in samples))

    def test_suppression_remains_null_not_zero(self):
        rows,_=self.api().build_census(ORIGINALS)
        self.assertTrue(any(r['status']=='suppressed' for r in rows))
        self.assertTrue(all(r['value'] is None for r in rows if r['status']=='suppressed'))
        self.assertTrue(any(r['value']=='0' and r['status']=='observed' for r in rows))

    def test_maori_residents_are_not_electoral_roll_population(self):
        rows,_=self.api().build_census(ORIGINALS)
        x=next(r for r in rows if r['source_id']=='census2023_maori_2020' and r['family_id']=='industry')
        self.assertIn('Māori descent',x['publisher_population_note'])
        self.assertFalse(x['electoral_roll_population'])

    def test_direct_medians_not_aggregated(self):
        rows,_=self.api().build_census(ORIGINALS)
        medians=[r for r in rows if r['measurement_kind']=='median']
        self.assertTrue(medians)
        self.assertTrue(all(not r['categories_additive'] for r in medians))

    def test_table_change_requires_new_source_pin(self):
        extract=self.source('census2023_general_2020')
        extract['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'source'):
            self.api().census_rows('census2023_general_2020',extract,{})

    def test_dwelling_parent_child_dimensions_retained(self):
        rows,_=self.api().build_census(ORIGINALS)
        dwelling=[r for r in rows if r['family_id']=='dwelling_occupancy']
        self.assertTrue(dwelling)
        self.assertTrue(all(r['category_parent'] and r['category_leaf'] for r in dwelling))
        keys={(r['source_id'],r['geography_name'],r['category']) for r in dwelling}
        self.assertEqual(len(keys),len(dwelling))

    def test_descent_and_age_descent_tables_reconcile(self):
        sheets=self.source('turnout2023_age_descent')['sheets']
        result=self.api().normalise_descent_tables(sheets)
        descent=result['electorate_descent']; detailed=result['electorate_age_descent']
        self.assertEqual(len(descent),137)
        self.assertEqual(len(detailed),1507)
        self.assertEqual(sum(r['voters'] for r in descent),2858896)
        self.assertEqual(sum(r['enrolled'] for r in detailed),3688292)
        self.assertTrue(result['receipt']['margins_exact'])
        self.assertTrue(all(r['area_role']=='electorate' for r in detailed))
        self.assertGreater(len(result['reference_totals']),0)

    def test_duplicate_turnout_stratum_rejected(self):
        sheets=self.source('turnout2023_age_descent')['sheets']
        s=sheets[1]
        # Duplicate a source coordinate rather than silently overwrite it.
        s['cells'].append(s['cells'][5].copy())
        with self.assertRaisesRegex(ValueError,'duplicate'):
            self.api().normalise_descent_tables(sheets)

    def test_altered_descent_total_rejected(self):
        sheets=self.source('turnout2023_age_descent')['sheets']
        for c in sheets[1]['cells']:
            if c[0]=='D9':c[2]=str(int(c[2])+1)
        with self.assertRaises(ValueError):self.api().normalise_descent_tables(sheets)

    def test_electorate_name_drift_across_tables_rejected(self):
        sheets=self.source('turnout2023_age_descent')['sheets']
        for cell in sheets[1]['cells']:
            if cell[0]=='B9':cell[2]='Wrong electorate'
        with self.assertRaisesRegex(ValueError,'identity'):
            self.api().normalise_descent_tables(sheets)

    def test_nonvoter_ratio_is_checked_independently(self):
        sheets=self.source('turnout2023_age_descent')['sheets']
        for cell in sheets[1]['cells']:
            if cell[0]=='G9':cell[2]='0.001'
        with self.assertRaisesRegex(ValueError,'ratio'):
            self.api().normalise_descent_tables(sheets)

    def test_missing_descent_age_stratum_rejected(self):
        sheets=self.source('turnout2023_age_descent')['sheets']
        s=sheets[2]
        s['cells']=[c for c in s['cells'] if ''.join(k for k in c[0] if k.isdigit()) != '29']
        with self.assertRaises(ValueError):self.api().normalise_descent_tables(sheets)

if __name__=='__main__':unittest.main()
