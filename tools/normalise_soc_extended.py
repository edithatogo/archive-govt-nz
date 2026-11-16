"""Normalise more tables from the six pinned SOC originals without acquisition.

Selection is explicit and source bytes are immutable. Source categories, footnotes,
multiple-response semantics and overlapping turnout margins remain distinguishable.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import defaultdict
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

from soc_source_binding import PINS, require, verify_bound_capture

# Exact aliases across the four already pinned workbooks, not fuzzy matching.
FAMILIES = {
    'Age': ('age', 'Age - 5 year groups'),
    'Labour force status': ('labour_force', 'Work and labour force status'),
    'Highest qualification': ('qualification', 'Highest qualification'),
    'Individual home ownership': ('home_ownership', 'Individual home ownership'),
    'Personal income': ('personal_income', 'Total personal income'),
    'Household income': ('household_income', 'Total household income'),
    'MeanMedian Weekly Rent': ('weekly_rent', 'Weekly rent paid by household'),
    'Status in employment': ('employment_status', 'Status in employment'),
    'Industry': ('industry', 'Industry'),
    'Occupation': ('occupation', 'Occupation'),
    'Study participation': ('study', 'Study participation'),
    'Birthplace': ('birthplace', 'Birthplace'),
    'Main means of travel Work': ('travel_work', 'Main means of travel to work'),
    'Main means of travel to Work': ('travel_work', 'Main means of travel to work'),
    'Main means of travel Ed': ('travel_education', 'Main means of travel to education'),
    'Main means of travel to Ed': ('travel_education', 'Main means of travel to education'),
    'Unpaid activities': ('unpaid_activities', 'Unpaid activities'),
    'Number of usual residents': ('household_size', 'Number of usual residents in household'),
    'Household composition': ('household_composition', 'Household composition'),
    'Sources of personal income': ('personal_income_sources', 'Sources of personal income'),
    'Sources of household income': ('household_income_sources', 'Sources of household income'),
    'Sector of landlord': ('landlord_sector', 'Sector of landlord'),
    'Family type': ('family_type', 'Family type'),
    'Family Type': ('family_type', 'Family type'),
    'Dwelling occupancy status': ('dwelling_occupancy', 'Dwelling Occupancy Status'),
}
MULTIPLE = {'personal_income_sources', 'household_income_sources', 'unpaid_activities'}
HOUSEHOLD = {'household_income', 'weekly_rent', 'household_size', 'household_composition',
             'household_income_sources', 'landlord_sector', 'family_type'}
ALIASES = {'Ikaroa-Rawhiti': 'Ikaroa-Rāwhiti', 'Tamaki Makaurau': 'Tāmaki Makaurau',
           'Te Tai Hauauru': 'Te Tai Hauāuru'}


def cell_index(sheet: dict[str, Any]) -> dict[str, list[Any]]:
    """Reject repeated native coordinates instead of overwriting an observation."""
    cells = sheet['cells']
    indexed = {cell[0]: cell for cell in cells}
    require(len(indexed) == len(cells), 'duplicate source cell')
    return indexed


def number(cell: list[Any] | None) -> tuple[str | None, str]:
    """Retain explicit confidentiality and blank cells without imputation."""
    if cell is None or cell[2] in (None, ''):
        return None, 'missing'
    require(cell[3] is None, 'formula is not a source observation')
    if cell[2] == '..C':
        return None, 'suppressed'
    require(cell[1] == 'n', 'unexpected numeric cell type')
    value = Decimal(str(cell[2]))
    require(value.is_finite(), 'nonfinite number')
    return str(value), 'observed'


def footnotes(sheets: dict[str, dict[str, Any]]) -> dict[str, tuple[str, str, str | None]]:
    """Retain verbatim variable notes with exact source coordinates."""
    indexed = cell_index(sheets['Variable specific footnotes'])
    result = {}
    for key, cell in indexed.items():
        if re.fullmatch(r'A\d+', key) and key != 'A1':
            row = key[1:]
            body = indexed.get('B'+row)
            url = indexed.get('C'+row)
            result[str(cell[2]).casefold()] = (
                '' if body is None else str(body[2]),
                'Variable specific footnotes!B'+row,
                None if url is None else str(url[2]),
            )
    return result


def census_rows(source_id: str, extract: dict[str, Any], record: dict[str, Any]) -> list[dict[str, Any]]:
    """Emit explicit selected tables, retaining dimensional and statistical context."""
    require(source_id in PINS and source_id.startswith('census'), 'unknown Census source')
    original_pin, _, system, boundary = PINS[source_id]
    require(extract.get('source_sha256') == original_pin, 'Census original source mismatch')
    sheets = {s['name']: s for s in extract['sheets']}
    require(len(sheets) == len(extract['sheets']), 'duplicate worksheet')
    contents = cell_index(sheets['Contents'])
    population_note = str(contents['B6'][2])
    licence = str(contents['B8'][2])
    notes = footnotes(sheets)
    age_names = {c[2] for c in sheets['Age']['cells'] if re.fullmatch(r'A\d+', c[0]) and int(c[0][1:]) > 3}
    output = []
    families_seen = set()
    for sheet_name, sheet in sheets.items():
        spec = FAMILIES.get(sheet_name.strip())
        if spec is None:
            continue
        family, concept = spec
        require(family not in families_seen, 'duplicate selected table family')
        families_seen.add(family)
        indexed = cell_index(sheet)
        header = 2 if family == 'weekly_rent' or (
            family in {'personal_income','household_income'} and system == 'general_electorate'
        ) else 3
        dimensional = family == 'dwelling_occupancy' and boundary == '2020'
        if dimensional:
            header = 4
        heads = {re.sub(r'\d', '', k): str(v[2]) for k, v in indexed.items()
                 if re.fullmatch(r'[A-Z]+'+str(header), k) and not k.startswith('A')}
        require(bool(heads), 'empty selected headers')
        note, locator, metadata_url = notes.get(concept.casefold(), ('', '', None))
        for key, row_cell in indexed.items():
            if not re.fullmatch(r'A\d+', key) or int(key[1:]) <= header:
                continue
            row_number = key[1:]
            raw_name = row_cell[2]
            name = ALIASES.get(raw_name, raw_name) if source_id == 'census2023_maori_2020' and family in {'weekly_rent', 'household_size', 'household_composition', 'household_income_sources', 'landlord_sector', 'family_type'} else raw_name
            require(name in age_names, 'unqualified source geography alias')
            role = 'reference_total' if name == 'Total' else (
                'outside_electorates' if str(name).casefold().startswith('area outside') else 'electorate'
            )
            for column, leaf in heads.items():
                parent = None
                if family == 'dwelling_occupancy':
                    if dimensional:
                        parent = ('Dwelling Under Construction' if column in 'BCD' else
                                  'Occupied Dwelling' if column in 'EFG' else
                                  'Unoccupied Dwelling' if column in 'HIJ' else 'All dwellings')
                    else:
                        parent = leaf
                category = parent+' / '+leaf if dimensional else leaf
                coordinate = column+row_number
                cell = indexed.get(coordinate)
                value, status = number(cell)
                kind = 'median' if leaf.startswith('Median ') else 'mean' if leaf.startswith('Mean ') else 'count'
                if value is not None and kind == 'count':
                    parsed = Decimal(value)
                    require(parsed >= 0 and parsed == parsed.to_integral_value(), 'invalid source count')
                unit = 'NZD_per_week' if family == 'weekly_rent' else (
                    'NZD_per_year' if kind in {'median','mean'} else 'source_count'
                )
                output.append({
                    'source_id': source_id, 'source_sha256': original_pin,
                    'source_url': record.get('url'), 'source_published_at': None,
                    'captured_at': record.get('captured_at'),
                    'reference_period': '2023 Census', 'geography_system': system,
                    'boundary_vintage': boundary, 'geography_name': name,
                    'source_geography_name': raw_name, 'area_role': role,
                    'geography_alias_evidence': 'explicit within-workbook Age-reference spelling' if raw_name != name else None,
                    'sheet': sheet_name, 'cell': coordinate, 'family_id': family,
                    'category': category, 'category_parent': parent, 'category_leaf': leaf,
                    'measurement_kind': kind, 'unit': unit, 'value': value,
                    'raw_token': None if cell is None else cell[2], 'status': status,
                    'response_mode': 'multiple_response' if family in MULTIPLE else 'source_categories',
                    'categories_additive': False,
                    'population_definition_status': 'requires_subset_review' if family in HOUSEHOLD else 'source_context_retained',
                    'publisher_population_note': population_note,
                    'source_table_context': indexed.get('B2', [None,None,None])[2],
                    'footnote_text': note or None, 'footnote_cell': locator or None,
                    'metadata_url': metadata_url, 'source_licence_note': licence,
                    'electoral_roll_population': False, 'synthetic': False,
                    'quality_note': 'Original Census rounding/suppression preserved; totals and subcategories must not be summed indiscriminately.',
                })
    keys = [(r['sheet'],r['geography_name'],r['category']) for r in output]
    require(len(keys) == len(set(keys)), 'duplicate Census observation')
    return output


def build_census(originals: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Use only the verified retained cohort; no live query or automatic schema inference."""
    manifest = json.loads((originals/'manifest.json').read_text())
    binding = verify_bound_capture(originals, manifest)
    records = {r['id']: r for r in manifest['records']}
    output = []
    for identity in sorted(k for k in PINS if k.startswith('census')):
        output.extend(census_rows(identity, json.loads((originals/(identity+'.cells.json')).read_text()), records[identity]))
    tables = {(r['source_id'],r['family_id']) for r in output}
    return output, {'rows':len(output), 'cohorts':4, 'tables':len(tables),
                    'table_families':len({r['family_id'] for r in output}),
                    'binding':binding, 'status':'source_native_candidate_not_published',
                    'not_automatically_analysis_eligible':True}


def normalise_descent_tables(sheets: list[dict[str, Any]]) -> dict[str, Any]:
    """Preserve all published descent strata and independently reconcile three margins."""
    expected_names = ['Voting by electorate & age','Voting by electorate & descent ','Voting by age & descent']
    indexed_sheets = {s['name']:s for s in sheets}
    require(set(indexed_sheets) == set(expected_names), 'unexpected turnout worksheets')
    all_rows, references = {}, []
    identities: dict[int, str] = {}
    for position, name in enumerate(expected_names):
        indexed = cell_index(indexed_sheets[name])
        detailed = position == 2
        count_cols = ('E','G','I') if detailed else ('D','F','H')
        rate_col = 'F' if detailed else 'E'
        expected = {'A':'Electorate Number','B':'Electorate name',
                    **({'C':'Age band','D':'Voter designation by descent'} if detailed else
                       {'C':'Voter designation by descent' if position==1 else 'Age band'}),
                    count_cols[0]:'Voters',count_cols[1]:'Non-voters',count_cols[2]:'Total enrolled'}
        require(all(indexed.get(col+'5',[None,None,None])[2] == label for col,label in expected.items()), 'turnout header mismatch')
        parsed = []
        for key, name_cell in indexed.items():
            if not re.fullmatch(r'B\d+',key) or int(key[1:]) < 6:
                continue
            number_row = key[1:]
            if count_cols[0]+number_row not in indexed:
                continue
            code_cell = indexed.get('A'+number_row)
            area = code_cell is not None and code_cell[1]=='n'
            code = int(code_cell[2]) if area else None
            if area:
                require(Decimal(str(code_cell[2])) == code and 1 <= code <= 72,
                        'invalid electorate identity')
                require(code not in identities or identities[code] == name_cell[2],
                        'electorate identity drift across source tables')
                identities[code] = name_cell[2]
            counts = []
            for column in count_cols:
                value,state = number(indexed.get(column+number_row))
                require(state=='observed' and value is not None, 'missing turnout count')
                dec = Decimal(value)
                require(dec >= 0 and dec == dec.to_integral_value(), 'invalid turnout count')
                counts.append(int(dec))
            voters, nonvoters, enrolled = counts
            require(voters+nonvoters==enrolled and enrolled>0, 'turnout conservation failure')
            ratio,state=number(indexed.get(rate_col+number_row))
            require(state=='observed' and ratio is not None, 'missing turnout ratio')
            nonvoter_col = 'H' if detailed else 'G'
            nonvoter_ratio, nonvoter_state = number(indexed.get(nonvoter_col+number_row))
            require(nonvoter_state == 'observed' and nonvoter_ratio is not None,
                    'missing nonvoter ratio')
            with localcontext() as context:
                context.prec=40
                require(abs(Decimal(ratio)-Decimal(voters)/enrolled) < Decimal('1e-12'), 'turnout ratio mismatch')
                require(abs(Decimal(nonvoter_ratio)-Decimal(nonvoters)/enrolled) < Decimal('1e-12'),
                        'nonvoter ratio mismatch')
                percentage=format(Decimal(100)*voters/enrolled,'.12f')
            age = str(indexed['C'+number_row][2]) if position!=1 else 'All ages'
            descent = str(indexed[('D' if detailed else 'C')+number_row][2]) if position!=0 else 'All voters'
            row={'table':name,'source_row':int(number_row),'electorate_number':code,
                 'geography_name':name_cell[2], 'age_band':age,'descent':descent,
                 'voters':voters,'nonvoters':nonvoters,'enrolled':enrolled,
                 'turnout_percent':percentage,'published_ratio_token':ratio,
                 'area_role':'electorate' if area else 'reference_total',
                 'boundary_vintage':'2020','election_year':2023,
                 'source_sha256':PINS['turnout2023_age_descent'][0],
                 'population':'registered electors; descent self-reported on enrolment',
                 'synthetic':False,'additive_across_tables':False}
            (parsed if area else references).append(row)
        keys=[(r['electorate_number'],r['age_band'],r['descent']) for r in parsed]
        require(len(keys)==len(set(keys)), 'duplicate turnout stratum')
        all_rows[position]=parsed
    require(set(identities) == set(range(1, 73)), 'incomplete electorate identity cohort')
    require([len(all_rows[i]) for i in range(3)] == [792,137,1507], 'incomplete turnout strata')
    def aggregate(rows: list[dict[str,Any]], keys: tuple[str,...]) -> dict[tuple[Any,...],tuple[int,int,int]]:
        result=defaultdict(lambda:[0,0,0])
        for row in rows:
            key=tuple(row[k] for k in keys)
            for n,col in enumerate(('voters','nonvoters','enrolled')):result[key][n]+=row[col]
        return {k:tuple(v) for k,v in result.items()}
    for dimensions, target in [(('electorate_number','age_band'),0), (('electorate_number','descent'),1)]:
        require(aggregate(all_rows[2],dimensions)==aggregate(all_rows[target],dimensions), 'turnout margin disagreement')
    totals=aggregate(all_rows[0],())[()]
    require(totals==(2858896,829396,3688292), 'national turnout margin disagreement')
    for ref in references:
        source_position=expected_names.index(ref['table'])
        matched=[r for r in all_rows[source_position]
                 if (str(ref['age_band']).casefold() in {'all ages','all age bands'} or r['age_band']==ref['age_band'])
                 and (ref['descent']=='All voters' or r['descent']==ref['descent'])]
        require(tuple(sum(r[k] for r in matched) for k in ('voters','nonvoters','enrolled'))
                ==tuple(ref[k] for k in ('voters','nonvoters','enrolled')), 'published national stratum disagreement')
    return {'electorate_descent':all_rows[1], 'electorate_age_descent':all_rows[2],
            'reference_totals':references,
            'receipt':{'margins_exact':True,'voters':totals[0],'enrolled':totals[2],
                       'overlap_warning':'Tables are alternative margins of the same electorate cohort; never sum across tables.'}}


def write_table(output: Path, name: str, rows: list[dict[str,Any]]) -> dict[str, Any]:
    """Retain machine-readable nulls and a same-grain CSV without overwriting sources."""
    json_path=output/(name+'.json')
    json_path.write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    with (output/(name+'.csv')).open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    return {'rows':len(rows),'json_sha256':hashlib.sha256(json_path.read_bytes()).hexdigest()}


def run(originals: Path, output: Path) -> dict[str,Any]:
    """Create one new local candidate from immutable retained inputs."""
    census,receipt=build_census(originals)
    extract=json.loads((originals/'turnout2023_age_descent.cells.json').read_text())
    descent=normalise_descent_tables(extract['sheets'])
    output.mkdir(parents=True,exist_ok=False)
    outputs={'census-extended':write_table(output,'census-extended',census)}
    for key in ('electorate_descent','electorate_age_descent','reference_totals'):
        outputs[key]=write_table(output,key,descent[key])
    result={'schema_version':'soc-extended-normalisation-v1','census':receipt,
            'turnout':descent['receipt'],'outputs':outputs,'published':False,
            'validation_runtime_scope':'recorded separately; not a full repository qualification'}
    (output/'receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--originals',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(run(args.originals,args.output),indent=2))
