"""SOC06 deterministic exports, state distinctions and independent byte readback."""
import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from importlib import import_module

import pytest

from archive_govt_nz.domains.elections.soc_contracts import Cell, Series, Source
from archive_govt_nz.domains.elections.soc_joins import join_exact

WHEN = datetime(2026, 11, 16, tzinfo=UTC)
CODE = 'a' * 40


def api():
    try:
        return import_module('archive_govt_nz.domains.elections.soc_publication')
    except ModuleNotFoundError:
        pytest.fail('SOC06 implementation missing')


def panel():
    s = Source('s', 'https://example.org/data', 'r1', sha256(b'data').hexdigest(), 4,
               datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 2, tzinfo=UTC), 'synthetic', True)
    x = Series('income', date(2023,1,1), date(2023,1,1), 'sa2', '2023', 'residents',
               'mean', 'NZD', (s,), tuple(Cell(str(i), Decimal(i), 'observed', 'r:'+str(i)) for i in range(4)))
    y = replace(x, metric='turnout', unit='percent', measure_kind='rate',
                cells=tuple(replace(c, value=c.value*2) for c in x.cells))
    return join_exact(x, y, as_of=WHEN, allow_synthetic=True)


def bundle(subject=None):
    return api().build_bundle(subject or panel(), validated_at=WHEN, code_revision=CODE,
                              validation_receipt='synthetic-diagnostic-only', allow_synthetic=True)


def test_bundle_is_byte_reproducible_and_explicitly_not_deployed():
    a, b = bundle(), bundle()
    assert a.files == b.files
    assert a.manifest_sha256 == b.manifest_sha256
    doc = json.loads(dict(a.files)['data.json'])
    assert doc['release_status'] == 'candidate_not_published'
    assert doc['synthetic'] is True
    assert 'SYNTHETIC' in dict(a.files)['table.html'].decode()
    assert doc['panel']['indicator']['period_end'] == '2023-01-01'
    assert doc['validated_at'] == WHEN.isoformat()
    assert doc['deployed_at'] is None


def test_synthetic_bundle_requires_explicit_optin():
    with pytest.raises(ValueError, match='synthetic'):
        api().build_bundle(panel(), validated_at=WHEN, code_revision=CODE,
                           validation_receipt='diagnostic')


def test_successful_readback_is_not_a_deployment_attestation():
    b = bundle()
    result = api().verify_readback(dict(b.files), expected_manifest_sha256=b.manifest_sha256)
    assert result['byte_parity'] is True
    assert result['deployment_verified'] is False
    assert result['manifest_sha256'] == b.manifest_sha256


@pytest.mark.parametrize('mutation', ['data', 'manifest', 'extra', 'missing'])
def test_readback_fails_on_tamper_extra_or_missing_assets(mutation):
    b = bundle()
    files = dict(b.files)
    if mutation == 'data':
        files['data.json'] += b' '
    elif mutation == 'manifest':
        files['manifest.json'] += b' '
    elif mutation == 'extra':
        files['legacy.html'] = b'old content'
    else:
        del files['table.csv']
    with pytest.raises(ValueError):
        api().verify_readback(files, expected_manifest_sha256=b.manifest_sha256)


def test_html_escapes_untrusted_geography_and_metric_text():
    p = panel()
    malicious = '<img src=x onerror=alert(1)>'
    x = replace(p.indicator, metric=malicious, cells=(replace(p.indicator.cells[0], geography_id=malicious),) + p.indicator.cells[1:])
    y = replace(p.outcome, cells=(replace(p.outcome.cells[0], geography_id=malicious),) + p.outcome.cells[1:])
    rendered = dict(bundle(replace(p, indicator=x, outcome=y)).files)['table.html'].decode()
    assert '<img' not in rendered
    assert '&lt;img' in rendered
    assert '<caption>' in rendered and 'scope="col"' in rendered


def test_csv_text_cells_cannot_execute_spreadsheet_formula():
    p = panel()
    x = replace(p.indicator, cells=(replace(p.indicator.cells[0], geography_id='=1+1'),) + p.indicator.cells[1:])
    y = replace(p.outcome, cells=(replace(p.outcome.cells[0], geography_id='=1+1'),) + p.outcome.cells[1:])
    result = bundle(replace(p, indicator=x, outcome=y))
    csv = dict(result.files)['table.csv'].decode()
    assert "'=1+1" in csv
    assert json.loads(dict(result.files)['data.json'])['panel']['pairs'][-1]['geography_id'] == '=1+1'


def test_missing_values_are_blank_not_zero_in_export():
    p = panel()
    x = replace(p.indicator, cells=(replace(p.indicator.cells[0], value=None, status='suppressed'),) + p.indicator.cells[1:])
    table = dict(bundle(replace(p, indicator=x)).files)['table.csv'].decode()
    assert '0,,suppressed,0,observed,indicator_suppressed' in table


def test_validation_time_cannot_precede_panel_asof():
    with pytest.raises(ValueError, match='validation'):
        api().build_bundle(panel(), validated_at=WHEN-timedelta(days=1), code_revision=CODE,
                           validation_receipt='diagnostic', allow_synthetic=True)


def test_unknown_source_state_does_not_become_absence():
    p = api()
    assert p.Coverage('s').state == 'unknown'
    assert p.Coverage('s', known_present=True).state == 'archived_unverified'
    assert p.Coverage('s', known_present=True, original_sha256='a'*64).state == 'archived_verified_not_normalised'


def test_lifecycle_requires_prior_evidence_and_does_not_claim_serving():
    p = api()
    with pytest.raises(ValueError, match='prerequisite'):
        p.Coverage('s', panel_sha256='b'*64)
    evidence = p.Coverage('s', True, 'a'*64, 'b'*64, 'c'*64)
    assert evidence.state == 'joined_not_published'
    assert evidence.public()['served_revision'] is None


def test_operational_freshness_separate_from_census_age():
    p = api()
    assert p.freshness(None, now=WHEN, maximum_age=timedelta(days=1)) == 'unknown'
    assert p.freshness(WHEN-timedelta(hours=1), now=WHEN, maximum_age=timedelta(days=1)) == 'fresh'
    assert p.freshness(WHEN-timedelta(days=2), now=WHEN, maximum_age=timedelta(days=1)) == 'stale'
    with pytest.raises(ValueError, match='future'):
        p.freshness(WHEN+timedelta(days=1), now=WHEN, maximum_age=timedelta(days=1))


def test_release_selection_preserves_last_good_on_bad_candidate():
    b = bundle()
    previous = dict(b.files)
    broken = dict(b.files)
    broken['data.json'] = b'corrupt'
    selected = api().select_release(previous, broken, expected_manifest_sha256=b.manifest_sha256, previous_manifest_sha256=b.manifest_sha256)
    assert selected['selection'] == 'retain_last_good'
    assert selected['files'] == previous
    assert selected['published'] is False


def test_invalid_previous_release_is_not_called_last_good():
    b = bundle()
    broken = dict(b.files)
    broken['data.json'] = b'corrupt'
    with pytest.raises(ValueError):
        api().select_release(broken, broken, expected_manifest_sha256=b.manifest_sha256, previous_manifest_sha256=b.manifest_sha256)


def test_last_good_requires_an_independent_previous_pin():
    b = bundle()
    with pytest.raises(ValueError, match='previous manifest'):
        api().select_release(dict(b.files), dict(b.files), expected_manifest_sha256=b.manifest_sha256)


def test_bad_candidate_without_last_good_holds_without_publishing():
    b = bundle()
    broken = dict(b.files)
    broken['data.json'] = b'corrupt'
    result = api().select_release(None, broken, expected_manifest_sha256=b.manifest_sha256)
    assert result['selection'] == 'hold' and result['files'] is None
    assert result['published'] is False
