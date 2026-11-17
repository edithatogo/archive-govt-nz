"""Real-data display contracts for SOC06 standalone, not-public-release preview."""
from __future__ import annotations

import copy
import os
import csv
import hashlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from build_soc_preview import build_dataset, render_html, write_bundle


PANEL = Path(os.environ.get('SOC_PANEL_CSV', 'build/soc-real-panel.csv'))
AGE = Path(os.environ.get('SOC_AGE_CSV', 'build/soc-age-standardised.csv'))

pytestmark = pytest.mark.skipif(
    not PANEL.is_file() or not AGE.is_file(),
    reason="Requires separately verified real 2023 Census/turnout panel artifacts",
)


def fixture():
    with PANEL.open(newline='', encoding='utf-8') as f:
        p = list(csv.DictReader(f))
    with AGE.open(newline='', encoding='utf-8') as f:
        a = list(csv.DictReader(f))
    return p, a


def test_real_2023_join_and_age_standardization_are_preserved():
    p, a = fixture()
    result = build_dataset(p,a)
    assert len(result['areas']) == 72
    assert set(result['sources']) == {'census2023_general_2020','census2023_maori_2020','turnout2023_age_descent'}
    auckland = next(r for r in result['areas'] if r['name']=='Auckland Central')
    assert auckland['median_income_nzd'] == '44900'
    assert auckland['voters'] == 35270 and auckland['enrolled'] == 45426
    assert auckland['age_national_percent'] == '78.305667439161'
    assert result['reporting']['record_count'] == 72
    assert result['reporting']['matched_income_areas'] == 72
    assert result['reporting']['age_standardisation_observations'] == 144


def test_reject_duplicate_age_row():
    p,a=fixture()
    with pytest.raises(ValueError, match='duplicate'):
        build_dataset(p,a+[a[0]])


def test_reject_incompatible_boundary_and_year():
    p,a=fixture()
    modified=copy.deepcopy(p)
    modified[0]['boundary_vintage']='2025'
    with pytest.raises(ValueError, match='boundary'):
        build_dataset(modified,a)
    modified=copy.deepcopy(a)
    modified[0]['election_year']='2026'
    with pytest.raises(ValueError, match='year'):
        build_dataset(p,modified)


def test_reject_unreviewed_synthetic_or_unsupported_inference():
    p,a=fixture()
    q=copy.deepcopy(p)
    q[0]['synthetic']='True'
    with pytest.raises(ValueError, match='synthetic'):
        build_dataset(q,a)
    q=copy.deepcopy(a)
    q[0]['causal_claim']='True'
    with pytest.raises(ValueError, match='causal'):
        build_dataset(p,q)


def test_denominator_conservation_and_missingness_are_explicit():
    p,a=fixture()
    q=copy.deepcopy(p)
    q[0]['voters']='999999'
    with pytest.raises(ValueError,match='turnout'):
        build_dataset(q,a)
    q=copy.deepcopy(p)
    q[0]['median_personal_income_nzd']=''
    q[0]['indicator_status']='suppressed'
    result=build_dataset(q,a)
    auckland=next(r for r in result['areas'] if r['name']=='Auckland Central')
    assert auckland['median_income_nzd'] is None
    assert result['reporting']['matched_income_areas']==71


def test_output_is_accessible_self_contained_and_cannot_execute_user_input():
    p,a=fixture()
    q=copy.deepcopy(p)
    evil='</script><img src=x onerror=alert(1)>'
    q[0]['geography_name']=evil
    for row in a:
        if row['geography_name']=='Auckland Central': row['geography_name']=evil
    result=build_dataset(q,a)
    page=render_html(result)
    assert '<img src=x' not in page
    assert '\\u003c/script\\u003e' in page
    assert '<label for="metric">' in page
    assert '2023 Census' in page
    assert 'candidate; not published' in page.lower()
    assert 'Māori' in page


def test_bundle_receipts_bind_independent_pinned_csv_and_refuse_overwrite(tmp_path: Path):
    hashes={'panel':hashlib.sha256(PANEL.read_bytes()).hexdigest(),
            'age':hashlib.sha256(AGE.read_bytes()).hexdigest()}
    output=tmp_path/'out'
    evidence=write_bundle(PANEL,AGE,output,expected_hashes=hashes)
    assert evidence['record_count']==72
    assert evidence['publication_verified'] is False
    assert (output/'index.html').exists()
    assert (output/'data.json').exists()
    assert (output/'manifest.json').exists()
    with pytest.raises(ValueError,match='already exists'):
        write_bundle(PANEL,AGE,output,expected_hashes=hashes)
    with pytest.raises(ValueError,match='hash'):
        write_bundle(PANEL,AGE,tmp_path/'out2',expected_hashes={**hashes,'panel':'0'*64})
