"""Normalise a pinned official Census/turnout cohort without changing originals.

The source-native profile fixes every selected table header and input digest.
Outputs remain candidate datasets, not an empirical model or dashboard release.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

TURNOUT_SHA = 'ecf32160d7aa7a024861bd402877f2eacd11a1a5308eac385f2948447c1a78be'


def require(condition, message):
    """Fail with a bounded diagnostic rather than silently reinterpret a source."""
    if not condition:
        raise ValueError(message)


def cells(sheet):
    """Index unique original cell coordinates without loss of cached formula data."""
    indexed = {c[0]: c for c in sheet['cells']}
    require(len(indexed) == len(sheet['cells']), 'duplicate cell coordinate')
    return indexed


def number(cell):
    """Preserve the source's confidentiality marker and exact decimal token."""
    if cell is None or cell[2] in (None, ''):
        return None, 'missing', None
    require(cell[3] is None, 'formula requires separate source review')
    token = str(cell[2])
    if token == '..C':
        return None, 'suppressed', token
    require(cell[1] == 'n' and len(token) <= 80, 'unexpected source value type')
    value = Decimal(token)
    require(value.is_finite(), 'nonfinite source number')
    return str(value), 'observed', token


def normalise_census(extract, profile):
    """Produce long-form observations with exact cell, header and population lineage."""
    require(extract['source_sha256'] == profile['source_sha256'], 'original identity mismatch')
    sheets = {s['name']: s for s in extract['sheets']}
    require(len(sheets) == len(extract['sheets']), 'duplicate worksheet')
    rows = []
    for layout in profile['tables']:
        indexed = cells(sheets[layout['sheet']])
        header_row = layout['header_row']
        actual_headers = {re.sub(r'[0-9]', '', key): value[2] for key, value in indexed.items()
                          if re.fullmatch(r'[A-Z]+' + str(header_row), key) and not key.startswith('A')}
        require(actual_headers == layout['headers'], 'source header drift')
        names = set()
        for key, value in indexed.items():
            if not re.fullmatch(r'A[0-9]+', key) or int(key[1:]) <= header_row:
                continue
            row, name = int(key[1:]), value[2]
            source_name = name
            name = layout.get('geography_aliases', {}).get(name, name)
            require(isinstance(name, str) and name and name not in names, 'duplicate/invalid geographic label')
            names.add(name)
            role = 'reference_total' if name == 'Total' else 'outside_electorates' if name.casefold().startswith('area outside') else 'electorate'
            for col, category in layout['headers'].items():
                coordinate = col + str(row)
                numeric, status, token = number(indexed.get(coordinate))
                kind = 'median' if category.startswith('Median ') else 'mean' if category.startswith('Mean ') else 'count'
                if numeric is not None and kind == 'count':
                    v = Decimal(numeric)
                    require(v >= 0 and v == v.to_integral_value(), 'invalid count')
                rows.append({'source_id': profile['source_id'], 'source_sha256': profile['source_sha256'],
                             'source_url': profile['source_url'], 'source_published_at': None,
                             'source_compiled_date': profile['compiled_date'], 'captured_at': profile['captured_at'],
                             'geography_system': profile['geography_system'], 'boundary_vintage': profile['boundary_vintage'],
                             'reference_period': '2023 Census', 'geography_name': name, 'source_geography_name': source_name, 'area_role': role,
                             'sheet': layout['sheet'], 'cell': coordinate, 'category': category,
                             'measurement_kind': kind, 'unit': layout['unit'], 'population': layout['population'],
                             'publisher_population_note': profile['population_note'], 'electoral_roll_population': False,
                             'value': numeric, 'raw_token': token, 'status': status,
                             'quality_note': 'Published Census confidentiality perturbation retained; counts need not add exactly.',
                             'synthetic': False})
    keys = [(r['sheet'], r['geography_name'], r['category']) for r in rows]
    require(len(keys) == len(set(keys)), 'duplicate observation')
    return rows


def normalise_turnout(extract):
    """Parse the actual 2023 age table and reconcile voters/nonvoters/enrolled."""
    require(extract['source_sha256'] == TURNOUT_SHA, 'turnout source identity mismatch')
    sheet = next(s for s in extract['sheets'] if s['name'] == 'Voting by electorate & age')
    indexed = cells(sheet)
    expected = {'A5': 'Electorate Number', 'B5': 'Electorate name', 'C5': 'Age band', 'D5': 'Voters',
                'E5': 'Voters as % of Total Enrolled', 'F5': 'Non-voters',
                'G5': 'Non-voters as % of Total Enrolled', 'H5': 'Total enrolled'}
    require(all(indexed[k][2] == v for k, v in expected.items()), 'turnout header drift')
    rows = []
    identities = {}
    by_electorate = defaultdict(set)
    for key, cell in indexed.items():
        if not re.fullmatch(r'A[0-9]+', key) or cell[1] != 'n':
            continue
        row = key[1:]
        electorate = int(cell[2])
        name, age = indexed['B'+row][2], indexed['C'+row][2]
        values = []
        for col in ('D', 'F', 'H'):
            raw, status, _ = number(indexed[col+row])
            require(status == 'observed' and Decimal(raw) >= 0 and Decimal(raw) == Decimal(raw).to_integral_value(), 'invalid turnout count')
            values.append(int(raw))
        voters, nonvoters, enrolled = values
        require(voters + nonvoters == enrolled and enrolled > 0, 'turnout count conservation failed')
        require(electorate not in identities or identities[electorate] == name, 'electorate identity drift')
        identities[electorate] = name
        require(age not in by_electorate[electorate], 'duplicate electorate/age')
        by_electorate[electorate].add(age)
        ratio = Decimal(indexed['E'+row][2])
        require(abs(ratio - Decimal(voters)/enrolled) < Decimal('1e-12'), 'turnout percentage disagrees with counts')
        rows.append({'electorate_number': electorate, 'geography_name': name, 'boundary_vintage': '2020',
                     'election_year': 2023, 'age_band': age, 'voters': voters, 'nonvoters': nonvoters,
                     'enrolled': enrolled, 'turnout_percent': float(100*Decimal(voters)/enrolled),
                     'source_sha256': TURNOUT_SHA, 'sheet': sheet['name'], 'source_row': int(row),
                     'population': 'registered_electors_at_election_day_roll_closure',
                     'voters_definition': 'identified electors who cast or attempted to cast a vote; not identical to valid ballots',
                     'synthetic': False})
    require(len(identities) == 72 and all(len(v) == 11 for v in by_electorate.values()), 'incomplete electorate/age cohort')
    totals = {field: sum(r[field] for r in rows) for field in ('voters','nonvoters','enrolled')}
    require([totals[f] for f in ('voters','nonvoters','enrolled')] == [int(indexed[c+'6'][2]) for c in ('D','F','H')], 'national totals fail reconciliation')
    return rows, {**totals, 'electorates': len(identities), 'age_rows': len(rows), 'national_count_reconciliation': 'exact'}


def verify_capture(directory, manifest):
    """Bind the exact original/extract cohort independently of its mutable manifest."""
    from soc_source_binding import verify_bound_capture

    verify_bound_capture(directory, manifest)


def load_profiles(path):
    """Expand a deduplicated explicit header-profile library."""
    library = json.loads(path.read_text())
    require(library['schema_version'] == 'soc-official-profile-library-v1', 'unknown profile schema')
    return {'cohorts': {key: {**value, 'tables': [library['tables'][name] for name in value['table_ids']]}
                        for key, value in library['cohorts'].items()}}


def write_outputs(originals, profile_path, output):
    """Create reproducible long-form CSV/JSON and a processing receipt; no overwrite."""
    manifest = json.loads((originals/'manifest.json').read_text())
    verify_capture(originals, manifest)
    profiles = load_profiles(profile_path)
    output.mkdir(parents=True, exist_ok=False)
    all_rows = []
    for key, profile in profiles['cohorts'].items():
        raw = (originals/(key+'.cells.json')).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == profile['extract_sha256'], 'profile/extract identity mismatch')
        all_rows.extend(normalise_census(json.loads(raw), profile))
    turnout, summary = normalise_turnout(json.loads((originals/'turnout2023_age_descent.cells.json').read_text()))
    for name, rows in [('census-long',all_rows),('turnout-age',turnout)]:
        (output/(name+'.json')).write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n')
        with (output/(name+'.csv')).open('w',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    receipt={'census_rows':len(all_rows), 'census_cohorts':len(profiles['cohorts']), 'table_families':7,
             'turnout':summary, 'profiles_sha256':hashlib.sha256(profile_path.read_bytes()).hexdigest(),
             'status':'source_normalised_not_dashboard_published', 'source_publication_dates':'unknown; compilation and capture dates retained separately',
             'universe_caution':'Māori Census tables concern Māori-descent residents, not Māori-roll electors; household subset definitions require further review',
             'outputs':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}}
    (output/'normalisation-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals',type=Path,required=True)
    parser.add_argument('--profiles',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();write_outputs(args.originals,args.profiles,args.output)
