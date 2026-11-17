"""Real retained-source tamper controls; no download, credentials or publication."""
from __future__ import annotations
import copy
import hashlib
import importlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
ORIGINALS = Path(os.environ.get('SOC_ORIGINALS', str(ROOT.parent / 'baseline/originals')))

class SourceBindingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((ORIGINALS / 'manifest.json').read_text())

    def api(self):
        try:
            return importlib.import_module('soc_source_binding')
        except ModuleNotFoundError:
            self.fail('SOC original-to-extract binding is not implemented')

    def test_real_six_record_cohort(self):
        receipt = self.api().verify_bound_capture(ORIGINALS, self.manifest)
        self.assertEqual(receipt['sources'], 6)
        self.assertEqual(receipt['publication_authorised'], False)

    def test_missing_record_rejected(self):
        changed = copy.deepcopy(self.manifest); changed['records'].pop()
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.api().verify_bound_capture(ORIGINALS, changed)

    def test_duplicate_record_rejected(self):
        changed = copy.deepcopy(self.manifest); changed['records'].append(changed['records'][0])
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.api().verify_bound_capture(ORIGINALS, changed)

    def test_extra_record_rejected(self):
        changed = copy.deepcopy(self.manifest)
        extra = dict(changed['records'][0]); extra['id'] = 'unapproved'
        changed['records'].append(extra)
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.api().verify_bound_capture(ORIGINALS, changed)

    def test_resealed_turnout_extract_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'source'; shutil.copytree(ORIGINALS, dest)
            file = dest / 'turnout2023_age_descent.cells.json'
            altered = json.loads(file.read_text())
            altered['sheets'][0]['cells'][0][2] = 'tampered label'
            file.write_text(json.dumps(altered, ensure_ascii=False))
            changed = copy.deepcopy(self.manifest)
            next(r for r in changed['records'] if r['id']=='turnout2023_age_descent')['cells_sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            # The previous implementation accepts a manifest resealed alongside an extract.
            for record in changed['records']:
                for suffix, field in [('.xlsx','sha256'),('.cells.json','cells_sha256')]:
                    self.assertEqual(hashlib.sha256((dest/(record['id']+suffix)).read_bytes()).hexdigest(), record[field])
            with self.assertRaisesRegex(ValueError, 'independent.*pin'):
                self.api().verify_bound_capture(dest, changed)

    def test_existing_normaliser_entrypoint_rejects_resealed_extract(self):
        legacy = importlib.import_module('normalise_soc_official')
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'source'
            shutil.copytree(ORIGINALS, dest)
            file = dest / 'turnout2023_age_descent.cells.json'
            data = json.loads(file.read_text())
            data['sheets'][0]['cells'][0][2] = 'altered after capture'
            file.write_text(json.dumps(data, ensure_ascii=False))
            changed = copy.deepcopy(self.manifest)
            row = next(r for r in changed['records'] if r['id'] == 'turnout2023_age_descent')
            row['cells_sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, 'independent.*pin'):
                legacy.verify_capture(dest, changed)

    def test_existing_normaliser_entrypoint_requires_complete_inventory(self):
        legacy = importlib.import_module('normalise_soc_official')
        changed = copy.deepcopy(self.manifest)
        changed['records'].pop()
        with self.assertRaisesRegex(ValueError, 'inventory'):
            legacy.verify_capture(ORIGINALS, changed)

    def test_wrong_byte_count_rejected(self):
        changed = copy.deepcopy(self.manifest); changed['records'][0]['bytes'] += 1
        with self.assertRaisesRegex(ValueError, 'size'):
            self.api().verify_bound_capture(ORIGINALS, changed)

    def test_wrong_boundary_rejected(self):
        changed = copy.deepcopy(self.manifest); changed['records'][0]['boundary'] = '2025'
        with self.assertRaisesRegex(ValueError, 'metadata'):
            self.api().verify_bound_capture(ORIGINALS, changed)

    def test_missing_extract_cannot_be_ignored(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'source'; shutil.copytree(ORIGINALS,dest)
            (dest/'turnout2023_age_descent.cells.json').unlink()
            with self.assertRaisesRegex(ValueError, 'retained file'):
                self.api().verify_bound_capture(dest,self.manifest)

    def test_symlinked_original_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/'source'; shutil.copytree(ORIGINALS,dest)
            f=dest/'turnout2023_age_descent.xlsx'; f.unlink(); f.symlink_to(ORIGINALS/f.name)
            with self.assertRaisesRegex(ValueError, 'retained file'):
                self.api().verify_bound_capture(dest,self.manifest)

    def test_source_extraction_matches_all_original_cells(self):
        result = self.api().audit_original_cells(ORIGINALS,self.manifest)
        self.assertEqual(result['matched_cells'],266201)
        self.assertEqual(result['worksheets'],135)
        self.assertEqual(result['mismatches'],0)

if __name__ == '__main__':
    unittest.main()
