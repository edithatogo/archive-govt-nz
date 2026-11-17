"""Build a read-only SOC06 election/social context preview from pinned, audited CSVs.

This module cannot publish to Hugging Face or authorize a statistical inference.
Full resolution of source rights and publisher deployment remains external.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

CENSUS = {
    'general_electorate': 'c3bd589f7aa6ff053c3a1ac9c1d4d678e6f30908c5b7d5bcf6533b38cd501fe2',
    'maori_electorate': 'd775725a52511a4869c2da4e7a17dabff07b0bb48cebb95a5aafe6c6e60f2735',
}
TURNOUT = 'ecf32160d7aa7a024861bd402877f2eacd11a1a5308eac385f2948447c1a78be'
AGE_STANDARDS = {'national_enrolled_2023', 'same_roll_system_enrolled_2023'}
METRICS = {
    'median_income_nzd': '2023 median personal income (NZD/year)',
    'unemployment_percent': '2023 area unemployment (labour-force %)',
    'non_homeowner_percent': '2023 non-ownership among stated 15+ population (%)',
    'bachelor_percent': '2023 Bachelor-level or higher qualification among stated 15+ (%)',
    'under30_percent': '2023 residents under 30 (%)',
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _num(v: str, *, integer: bool = False, lower: Decimal | None = None,
         upper: Decimal | None = None) -> Decimal:
    require(isinstance(v, str) and bool(re.fullmatch(r'[0-9]+(?:\.[0-9]+)?', v)), 'invalid numeric token')
    try:
        n=Decimal(v)
    except InvalidOperation as exc:
        raise ValueError('invalid numeric token') from exc
    require(not integer or n == n.to_integral_value(), 'invalid integer')
    require(lower is None or n >= lower, 'value out of range')
    require(upper is None or n <= upper, 'value out of range')
    return n


def _assert_public(record: dict[str, str], *, age: bool = False) -> None:
    require(record.get('synthetic') == 'False', 'synthetic data are not allowed')
    require(record.get('causal_claim') == 'False', 'causal claims are not allowed')
    require(record.get('boundary_vintage') == '2020', 'incompatible boundary vintage')
    require(record.get('election_year') == '2023', 'incorrect election year')
    require(record.get('geography_system') in CENSUS, 'invalid geographic system')
    source = record.get('source_sha256') if age else record.get('turnout_original_sha256')
    require(source == TURNOUT, 'turnout original SHA mismatch')
    if not age:
        require(record.get('census_original_sha256') == CENSUS[record['geography_system']],
                'Census original SHA mismatch')
        require(record.get('population_relationship') == 'different_populations_same_area_context',
                'invalid population interpretation')
    else:
        require(record.get('age_strata') == '11', 'incomplete age strata')


def build_dataset(panel: list[dict[str,str]], age: list[dict[str,str]]) -> dict:
    """Validate compatible electorate-vintage identities, conservatively mark missingness."""
    require(len(panel) == 72, 'incomplete empirical cohort')
    groups: dict[tuple[int,str],dict] = {}
    for row in panel:
        _assert_public(row)
        code=int(_num(row['electorate_number'], integer=True, lower=Decimal(1)))
        system=row['geography_system']; key=(code,system)
        require(key not in groups, 'duplicate electorate')
        v=int(_num(row['voters'], integer=True, lower=Decimal(0)))
        n=int(_num(row['enrolled'], integer=True, lower=Decimal(1)))
        require(v<=n, 'invalid turnout numerator or denominator')
        actual=_num(row['turnout_percent'],lower=Decimal(0),upper=Decimal(100))
        require(abs(actual-Decimal(100)*v/n)<Decimal('0.0000001'), 'turnout differs from source counts')
        income = row.get('median_personal_income_nzd','')
        require(row.get('indicator_status') in {'observed','suppressed','missing','unavailable'}, 'invalid income status')
        if row['indicator_status']=='observed':
            _num(income, lower=Decimal(0))
        else:
            require(income == '', 'suppressed income must remain unavailable')
        indicators={
            'median_income_nzd': income if income else None,
            'unemployment_percent': row.get('unemployment_share_labour_force_percent') or None,
            'non_homeowner_percent': row.get('not_homeowner_share_stated_percent') or None,
            'bachelor_percent': row.get('bachelor_or_higher_share_stated_percent') or None,
            'under30_percent': row.get('under30_resident_share_percent') or None,
        }
        for name in METRICS:
            if indicators[name] is not None:
                _num(indicators[name],lower=Decimal(0),upper=None if name=='median_income_nzd' else Decimal(100))
        groups[key]={'id':str(code),'name':row['geography_name'],'geography_system':system,
                     'voters':v,'enrolled':n,'turnout_percent':str(actual),
                     'age_national_percent':None,'age_same_roll_percent':None,
                     **indicators,'indicator_status':row['indicator_status']}
    seen_age: set[tuple[int,str,str]]=set()
    for row in age:
        _assert_public(row,age=True)
        system=row['geography_system'];code=int(_num(row['electorate_number'],integer=True,lower=Decimal(1)))
        standard=row.get('standard')
        require(standard in AGE_STANDARDS, 'unsupported age reference')
        key=(code,system,standard)
        require(key not in seen_age, 'duplicate standardisation row')
        seen_age.add(key)
        require((code,system) in groups, 'unmatched standardisation electorate')
        target=groups[(code,system)]
        require(row['geography_name']==target['name'],'electorate identity disagreement')
        require(int(_num(row['voters'],integer=True))==target['voters']
                and int(_num(row['enrolled'],integer=True))==target['enrolled'],
                'turnout denominator discrepancy')
        rate=str(_num(row['standardised_turnout_percent'],lower=Decimal(0),upper=Decimal(100)))
        if standard=='national_enrolled_2023':target['age_national_percent']=rate
        else:target['age_same_roll_percent']=rate
    require(len(age)==144, 'incomplete age-standardisation cohort')
    require(all(x['age_national_percent'] and x['age_same_roll_percent'] for x in groups.values()),
            'missing age standardisation')
    areas=sorted(groups.values(),key=lambda x:(x['geography_system'],x['name']))
    return {'schema_version':'soc-2023-area-preview-v1','publication_status':'candidate_not_published',
            'observation_reference_year':2023, 'electorate_boundary_vintage':'2020',
            'source_published_at':None,
            'sources':{
              'census2023_general_2020':CENSUS['general_electorate'],
              'census2023_maori_2020':CENSUS['maori_electorate'],
              'turnout2023_age_descent':TURNOUT,
            }, 'areas':areas,'metrics':METRICS,
            'reporting':{'record_count':len(areas),'matched_income_areas':sum(x['median_income_nzd'] is not None for x in areas),
                         'age_standardisation_observations':len(age),
                         'general_electorates':sum(x['geography_system']=='general_electorate' for x in areas),
                         'maori_electorates':sum(x['geography_system']=='maori_electorate' for x in areas)},
            'methods':{'design':'retrospective area-level comparison; not person-level or causal',
                       'income':'2023 Census median of resident population; not electoral-roll income',
                       'turnout':'2023 registered elector vote or attempted vote / enrolled',
                       'age':'direct standardisation against national or same-roll age distribution',
                       'missingness':'source confidential and unavailable metrics are not imputed'},
            'synthetic':False,'causal_effect':None,'p_value':None}


def render_html(data:dict) -> str:
    """Render accessible self-contained preview; escape all source labels and JSON."""
    safe_json=json.dumps(data,ensure_ascii=False,sort_keys=True,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    lines=["<!doctype html><html lang=\"en-NZ\"><head><meta charset=\"utf-8\">",
           "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">",
           "<title>2023 electorate socioeconomic context — unpublished candidate</title>",
           "<style>body{font:16px system-ui,sans-serif;max-width:1140px;margin:auto;padding:1rem;color:#182634;background:#fff}"
           "select{padding:.5rem;font:inherit}table{border-collapse:collapse;width:100%}th,td{border:1px solid #9daeb6;padding:.35rem;text-align:left}"
           "thead{background:#e7eef5}caption{text-align:left;font-weight:bold;padding:.5rem}svg{width:100%;max-width:900px;height:auto;background:#f5f9fb}"
           ".notice{border-left:4px solid #53677a;padding:1rem;background:#edf2f7}a{color:#064885}"
           "</style></head><body>",
           "<main><h1>2023 election: socioeconomic context</h1>",
           "<p class=\"notice\"><strong>Candidate; not published.</strong> This is an exploratory, 2023 area-level analysis. "
           "No inference about individual voters, donation effects, or causation. Census residents and enrolled electors are different populations.</p>",
           "<p>2023 Census, 2023 election turnout, 2020 electorate boundaries. These observations are historical, not 2026 forecasts.</p>",
           "<label for=\"metric\">Socioeconomic indicator: </label><select id=\"metric\"></select> "
           "<label for=\"group\">Electoral system: </label><select id=\"group\"><option value=\"general_electorate\">General electorates</option>"
           "<option value=\"maori_electorate\">Māori electorates</option></select>",
           "<figure><svg id=\"scatter\" viewBox=\"0 0 880 440\" role=\"img\" aria-label=\"Interactive plot of area-level socioeconomic measures against turnout\"></svg>"
           "<figcaption>Each circle is an electorate. The pattern is descriptive and does not establish a causal relationship.</figcaption></figure>",
           "<p id=\"count\" aria-live=\"polite\"></p>",
           "<table><caption>Electorate observations, including adjusted turnout</caption><thead><tr>"
           "<th scope=\"col\">Electorate</th><th scope=\"col\">Observed turnout (%)</th><th scope=\"col\">Age-standardised national (%)</th>"
           "<th scope=\"col\">Age-standardised same-roll (%)</th><th scope=\"col\">Selected indicator</th></tr></thead><tbody id=\"rows\"></tbody></table>",
           "<h2>Sources and limitations</h2><p>Data collected from <a href=\"https://www3.parliament.nz/en/mps-and-electorates/electorate-data-2023/\">"
           "NZ Parliament electorate Census extracts</a> and <a href=\"https://elections.nz/\">Electoral Commission 2023 turnout tables</a>. "
           "Original SHA-256 source identities, historical boundaries and definitions are in the companion data bundle.</p>",
           "<p>Last observation 2023; source publication date not verified. Processing and deployed timestamps are not asserted. "
           "Published source cells may be confidentially rounded or suppressed.</p></main>",
           f"<script type=\"application/json\" id=\"soc-data\">{safe_json}</script>",
           "<script>(function(){'use strict';const d=JSON.parse(document.getElementById('soc-data').textContent);"
           "const metric=document.getElementById('metric'),group=document.getElementById('group'),svg=document.getElementById('scatter'),tbody=document.getElementById('rows');"
           "for(const [key,label] of Object.entries(d.metrics)){const o=document.createElement('option');o.value=key;o.textContent=label;metric.append(o)}"
           "function draw(){const values=d.areas.filter(a=>a.geography_system===group.value);const key=metric.value;"
           "document.getElementById('count').textContent=values.length+' areas; '+values.filter(a=>a[key]!==null).length+' with numeric indicators';"
           "tbody.replaceChildren();while(svg.lastChild)svg.removeChild(svg.lastChild);"
           "const valid=values.filter(a=>a[key]!==null),nums=valid.map(a=>Number(a[key])),x0=Math.min(...nums),x1=Math.max(...nums);"
           "const make=(tag,attrs)=>{const x=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [k,v] of Object.entries(attrs))x.setAttribute(k,String(v));svg.append(x);return x};"
           "make('line',{x1:52,y1:390,x2:820,y2:390,stroke:'#182634'});make('line',{x1:52,y1:20,x2:52,y2:390,stroke:'#182634'});"
           "for(const a of valid){const xx=52+768*(Number(a[key])-x0)/(x1-x0||1);const yy=390-370*Number(a.turnout_percent)/100;"
           "const c=make('circle',{cx:xx,cy:yy,r:4,fill:'#125b8e'});const title=document.createElementNS('http://www.w3.org/2000/svg','title');title.textContent=a.name;c.append(title)}"
           "for(const a of values){const tr=document.createElement('tr');for(const v of [a.name,a.turnout_percent,a.age_national_percent,a.age_same_roll_percent,a[key]??'Suppressed / unavailable']){"
           "const td=document.createElement('td');td.textContent=String(v);tr.append(td)}tbody.append(tr)}}metric.addEventListener('change',draw);group.addEventListener('change',draw);draw()})();</script></body></html>"
           ]
    return '\n'.join(lines)


def write_bundle(panel_csv:Path,age_csv:Path,output:Path,*,expected_hashes:dict[str,str]) -> dict:
    """Require independently pinned inputs, produce candidate-only immutable bundle."""
    require(not output.exists(),'output already exists')
    for key,path in [('panel',panel_csv),('age',age_csv)]:
        require(re.fullmatch('[0-9a-f]{64}',expected_hashes.get(key,'')) is not None,'invalid input hash pin')
        require(hashlib.sha256(path.read_bytes()).hexdigest()==expected_hashes[key],'input hash mismatch')
    with panel_csv.open(newline='',encoding='utf-8') as f:p=list(csv.DictReader(f))
    with age_csv.open(newline='',encoding='utf-8') as f:a=list(csv.DictReader(f))
    data=build_dataset(p,a)
    output.mkdir(parents=True)
    raw=(json.dumps(data,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()
    html_text=render_html(data).encode()
    (output/'data.json').write_bytes(raw)
    (output/'index.html').write_bytes(html_text)
    manifest={'schema_version':'soc-dashboard-preview-v1','publication_status':'candidate_not_published',
              'input_sha256':expected_hashes,'record_count':len(data['areas']),
              'outputs':{x:hashlib.sha256((output/x).read_bytes()).hexdigest() for x in ['data.json','index.html']},
              'publication_verified':False}
    (output/'manifest.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
    return manifest


def main() -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--panel',type=Path,required=True)
    parser.add_argument('--age',type=Path,required=True)
    parser.add_argument('--panel-sha256',required=True)
    parser.add_argument('--age-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    manifest=write_bundle(a.panel,a.age,a.output,expected_hashes={'panel':a.panel_sha256,'age':a.age_sha256})
    print(json.dumps(manifest,indent=2))
    return 0


if __name__=='__main__':raise SystemExit(main())
