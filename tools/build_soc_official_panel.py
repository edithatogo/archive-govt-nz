"""Build a retrospective 2023 income/turnout panel on direct 2020 boundaries.

No fuzzy matching, spatial interpolation, individual-voter linkage or prospective
availability is inferred. Input original/transform identities remain inspectable.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path

CENSUS = {'census2023_general_2020': 'c3bd589f7aa6ff053c3a1ac9c1d4d678e6f30908c5b7d5bcf6533b38cd501fe2',
          'census2023_maori_2020': 'd775725a52511a4869c2da4e7a17dabff07b0bb48cebb95a5aafe6c6e60f2735'}
TURNOUT = 'ecf32160d7aa7a024861bd402877f2eacd11a1a5308eac385f2948447c1a78be'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def build_panel(census, turnout):
    """Preserve all target electorates and disclose every missing covariate."""
    selected = [r for r in census if r['source_id'] in CENSUS and r['boundary_vintage']=='2020'
                and r['sheet']=='Personal income' and r['category']=='Median Personal Income'
                and r['area_role']=='electorate']
    require(bool(selected), 'approved 2020 Census cohort required')
    index = {}
    for r in selected:
        require(r['synthetic'] is False and r['source_sha256']==CENSUS[r['source_id']], 'Census source identity mismatch')
        require(r['measurement_kind']=='median' and r['unit']=='NZD_per_year', 'income metric mismatch')
        require(r['geography_name'] not in index, 'duplicate Census geography')
        index[r['geography_name']] = r
    groups = defaultdict(list)
    seen = set()
    for r in turnout:
        require(r['synthetic'] is False and r['source_sha256']==TURNOUT, 'turnout source identity mismatch')
        require(r['boundary_vintage']=='2020' and r['election_year']==2023, 'wrong electoral vintage')
        key = (r['electorate_number'],r['age_band'])
        require(key not in seen, 'duplicate turnout age stratum');seen.add(key)
        require(r['voters']+r['nonvoters']==r['enrolled'], 'turnout count conservation failure')
        groups[r['electorate_number']].append(r)
    rows, unmatched = [], []
    for code, age_rows in sorted(groups.items()):
        require(len(age_rows)==11 and len({r['geography_name'] for r in age_rows})==1, 'incomplete or mixed electorate strata')
        name = age_rows[0]['geography_name'];income=index.get(name)
        voters=sum(r['voters'] for r in age_rows);enrolled=sum(r['enrolled'] for r in age_rows)
        require(enrolled > 0, 'nonpositive denominator')
        if income is None or income['value'] is None:unmatched.append(name)
        rows.append({'electorate_number':code,'geography_name':name,'boundary_vintage':'2020','election_year':2023,
                     'voters':voters,'enrolled':enrolled,'turnout_percent':100*voters/enrolled,
                     'median_personal_income_nzd':income['value'] if income else None,
                     'indicator_status':income['status'] if income else 'missing',
                     'geography_system':income['geography_system'] if income else None,
                     'census_original_sha256':income['source_sha256'] if income else None,
                     'census_cell':income['cell'] if income else None,
                     'census_population_note':income['publisher_population_note'] if income else None,
                     'turnout_original_sha256':TURNOUT,
                     'turnout_source_rows':';'.join(str(r['source_row']) for r in age_rows),
                     'population_relationship':'different_populations_same_area_context',
                     'source_published_at':None,'synthetic':False,'causal_claim':False})
    receipt={'schema_version':'soc-real-income-turnout-panel-v1','rows':len(rows),'matched':len(rows)-len(unmatched),
             'unmatched':unmatched,'unused_census_areas':sorted(set(index)-{r['geography_name'] for r in rows}),
             'analysis_mode':'retrospective_area_context', 'join_method':'exact_source_name_on_same_2020_boundary',
             'availability_caution':'Census workbooks compiled in 2025; do not present this as a pre-election 2023 forecast.',
             'turnout_caution':'Identified electors casting or attempting a vote, not valid-ballot counts.',
             'publication_status':'candidate_not_dashboard_published'}
    return rows,receipt


def run(census_path, turnout_path, output):
    rows,receipt=build_panel(json.loads(census_path.read_text()),json.loads(turnout_path.read_text()))
    output.mkdir(parents=True,exist_ok=False)
    with (output/'income-turnout-2023.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    (output/'income-turnout-2023.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':'))+'\n')
    receipt['inputs_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (census_path,turnout_path)}
    receipt['outputs_sha256']={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.iterdir())}
    (output/'panel-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--census',type=Path,required=True);p.add_argument('--turnout',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();run(args.census,args.turnout,args.output)
