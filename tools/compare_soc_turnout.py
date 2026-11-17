"""Source-checked 2023 turnout/socioeconomic association after age adjustment.

An area-level descriptive sensitivity exercise. Not causal, individual, or predictive.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from statistics import correlation

SOURCE_CENSUS = {
    'general_electorate': 'c3bd589f7aa6ff053c3a1ac9c1d4d678e6f30908c5b7d5bcf6533b38cd501fe2',
    'maori_electorate': 'd775725a52511a4869c2da4e7a17dabff07b0bb48cebb95a5aafe6c6e60f2735',
}
SOURCE_TURNOUT = 'ecf32160d7aa7a024861bd402877f2eacd11a1a5308eac385f2948447c1a78be'
METRICS = ('median_personal_income_nzd', 'unemployment_share_labour_force_percent',
           'not_homeowner_share_stated_percent', 'bachelor_or_higher_share_stated_percent',
           'under30_resident_share_percent')


def require(value: bool, msg: str) -> None:
    if not value:
        raise ValueError(msg)


def _number(value: str) -> float:
    require(isinstance(value, str) and value and value.strip()==value, 'invalid numeric')
    number=Decimal(value)
    require(number.is_finite(), 'nonfinite number')
    return float(number)


def _r(xs: list[float], ys: list[float]) -> dict[str,object]:
    n=len(xs)
    require(n==len(ys), 'pair mismatch')
    def pearson(a:list[float],b:list[float]) -> float | None:
        if len(a)<4 or len(set(a))<2 or len(set(b))<2:return None
        return round(correlation(a,b),12)
    result=pearson(xs,ys)
    loo=[pearson(xs[:i]+xs[i+1:],ys[:i]+ys[i+1:]) for i in range(n)] if n>=5 else []
    loo=[p for p in loo if p is not None]
    return {'n':n,'pearson':result,'leave_one_out_min':min(loo) if loo else None,
            'leave_one_out_max':max(loo) if loo else None}


def compare(panel:list[dict[str,str]], age:list[dict[str,str]]) -> dict:
    """Compare empirical raw and age-adjusted turnout associations on same support."""
    require(len(panel)==72 and len(age)==144,'incomplete source cohort')
    places:dict[tuple[int,str],dict]={}
    for p in panel:
        sys=p.get('geography_system')
        require(sys in SOURCE_CENSUS,'invalid geography system')
        require(p.get('boundary_vintage')=='2020','incompatible boundary vintage')
        require(p.get('election_year')=='2023','incorrect election year')
        require(p.get('census_original_sha256')==SOURCE_CENSUS[sys]
                and p.get('turnout_original_sha256')==SOURCE_TURNOUT,'source identity mismatch')
        require(p.get('synthetic')=='False' and p.get('causal_claim')=='False','unqualified result')
        require(p.get('population_relationship')=='different_populations_same_area_context','population mismatch')
        name=p.get('geography_name')
        key=(int(p['electorate_number']),sys)
        require(key not in places,'duplicate electorate')
        voters=int(p['voters']);enrolled=int(p['enrolled'])
        require(0<=voters<=enrolled and enrolled>0, 'invalid turnout denominator')
        require(abs(100*voters/enrolled-_number(p['turnout_percent']))<1e-7,'turnout mismatch')
        places[key]={'name':name,'system':sys,'voters':voters,'enrolled':enrolled,
                     'raw':_number(p['turnout_percent']), 'data':p, 'ages':{}}
    for a in age:
        sys=a.get('geography_system')
        require(sys in SOURCE_CENSUS and a.get('boundary_vintage')=='2020','incompatible boundary vintage')
        require(a.get('source_sha256')==SOURCE_TURNOUT and a.get('election_year')=='2023','source identity or year mismatch')
        require(a.get('synthetic')=='False' and a.get('causal_claim')=='False','unqualified result')
        standard=a.get('standard')
        require(standard in {'national_enrolled_2023','same_roll_system_enrolled_2023'},'invalid standard')
        key=(int(a['electorate_number']),sys)
        require(key in places,'electorate not found')
        p=places[key]
        require(p['name']==a.get('geography_name') and int(a['voters'])==p['voters']
                and int(a['enrolled'])==p['enrolled'],'electorate identity or turnout mismatch')
        require(standard not in p['ages'],'duplicate standardisation')
        adjusted=_number(a['standardised_turnout_percent'])
        require(0<=adjusted<=100,'invalid adjusted rate')
        p['ages'][standard]=adjusted
    require(all(len(x['ages'])==2 for x in places.values()),'missing age standardisation')
    groups={}
    for system in SOURCE_CENSUS:
        areas=[p for p in places.values() if p['system']==system]
        comparisons={}
        for metric in METRICS:
            xs=[];ys={'raw':[],'national_age_adjusted':[],'same_roll_age_adjusted':[]}
            for p in areas:
                token=p['data'].get(metric,'')
                if token=='':continue
                if metric=='median_personal_income_nzd':
                    require(p['data'].get('indicator_status')=='observed','missing or suppressed income')
                x=_number(token)
                require(x>=0 and (metric=='median_personal_income_nzd' or x<=100),'invalid indicator')
                xs.append(x)
                ys['raw'].append(p['raw'])
                ys['national_age_adjusted'].append(p['ages']['national_enrolled_2023'])
                ys['same_roll_age_adjusted'].append(p['ages']['same_roll_system_enrolled_2023'])
            comparisons[metric]={name:_r(xs,y) for name,y in ys.items()}
        groups[system]={'n_areas':len(areas),'comparisons':comparisons}
    return {'schema':'soc-age-adjusted-associations-v1','scope':'retrospective_geographic_descriptive_only',
            'source_status':'source_derived_candidate_not_published','groups':groups,
            'boundary_vintage':'2020','census_reference_year':2023,'election_year':2023,
            'causal_inference':False,'p_values':None,'prognostic_prediction':False,
            'interpretation':'Area-level, non-causal, unweighted associations; no spatial adjustment or individual inference. Māori n=7 highly unstable.',
            'source_sha256':{'census':SOURCE_CENSUS,'turnout':SOURCE_TURNOUT}}


def main() -> int:
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('panel','age','output','panel-sha256','age-sha256'):p.add_argument('--'+key,required=True)
    args=p.parse_args()
    for name in ('panel','age'):
        path=Path(getattr(args,name))
        require(hashlib.sha256(path.read_bytes()).hexdigest()==getattr(args,name+'_sha256'), 'input hash mismatch')
    with open(args.panel,newline='',encoding='utf-8') as f: panel=list(csv.DictReader(f))
    with open(args.age,newline='',encoding='utf-8') as f: age=list(csv.DictReader(f))
    result=compare(panel,age)
    dest=Path(args.output);require(not dest.exists(),'output exists')
    dest.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+'\n')
    print('evaluated',len(panel),'areas without empirical or causal claims')
    return 0

if __name__=='__main__':raise SystemExit(main())
