"""SOC05 tests for retrospective area-level effect of age standardisation on associations."""
import copy
import os
import csv
import hashlib
import sys
from pathlib import Path

import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'tools'))
from compare_soc_turnout import compare

PANEL=Path(os.environ.get('SOC_PANEL_CSV', 'build/soc-real-panel.csv'))
AGE=Path(os.environ.get('SOC_AGE_CSV', 'build/soc-age-standardised.csv'))

pytestmark = pytest.mark.skipif(
    not PANEL.is_file() or not AGE.is_file(),
    reason="Requires separately verified real 2023 Census/turnout panel artifacts",
)


def rows():
    with PANEL.open() as f:panel=list(csv.DictReader(f))
    with AGE.open() as f:age=list(csv.DictReader(f))
    return panel,age


def test_65_general_7_maori_and_supported_comparisons():
    p,a=rows();out=compare(p,a)
    assert out['scope']=='retrospective_geographic_descriptive_only'
    assert out['source_status']=='source_derived_candidate_not_published'
    assert out['groups']['general_electorate']['n_areas']==65
    assert out['groups']['maori_electorate']['n_areas']==7
    assert out['groups']['general_electorate']['comparisons']['median_personal_income_nzd']['raw']['n']==65
    assert out['groups']['general_electorate']['comparisons']['median_personal_income_nzd']['national_age_adjusted']['n']==65
    assert out['groups']['general_electorate']['comparisons']['median_personal_income_nzd']['raw']['pearson'] != out['groups']['general_electorate']['comparisons']['median_personal_income_nzd']['national_age_adjusted']['pearson']


def test_unpublished_and_noncausal_claims():
    p,a=rows();out=compare(p,a)
    assert out['causal_inference'] is False
    assert out['p_values'] is None
    assert out['prognostic_prediction'] is False


def test_tampered_turnout_counts_rejected():
    p,a=rows();q=copy.deepcopy(p);q[0]['enrolled']='10'
    with pytest.raises(ValueError,match='turnout'):
        compare(q,a)


def test_mismatched_election_vintage_rejected():
    p,a=rows();q=copy.deepcopy(p);q[0]['boundary_vintage']='2025'
    with pytest.raises(ValueError,match='boundary'):
        compare(q,a)


def test_suppressed_indicator_excluded_not_zero():
    p,a=rows();q=copy.deepcopy(p);q[0]['median_personal_income_nzd']='';q[0]['indicator_status']='suppressed'
    res=compare(q,a)
    assert res['groups']['general_electorate']['comparisons']['median_personal_income_nzd']['raw']['n']==64


def test_no_false_population_merging():
    p,a=rows();q=copy.deepcopy(a);q[0]['geography_system']='maori_electorate'
    with pytest.raises(ValueError):
        compare(p,q)
