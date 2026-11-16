"""SOC02 synthetic CSV profile and confidentiality regression controls."""
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from importlib import import_module

import pytest

from archive_govt_nz.domains.elections.soc_contracts import Source

RAW = b'Area,Year,Unit,Value,Status,Sex\nA,2023,people,12,OK,All\nB,2023,people,,S,All\nC,2023,people,0,OK,All\nA,2023,people,5,OK,Female\n'


def api():
    try:
        return import_module('archive_govt_nz.domains.elections.soc_ingestion')
    except ModuleNotFoundError:
        pytest.fail('SOC02 implementation missing')


def profile(raw=RAW):
    p = api()
    source = Source('synthetic-census', 'https://example.org/census.csv', 'r1',
                    sha256(raw).hexdigest(), len(raw),
                    datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 2, tzinfo=UTC),
                    'synthetic-only', True)
    return p.CsvProfile(source, 'resident_count', date(2023, 3, 7), date(2023, 3, 7),
                        'general_electorate', '2025', 'residents', 'count', 'persons',
                        '2023', 'people', ('Area', 'Year', 'Unit', 'Value', 'Status'),
                        (('Sex', 'All'),), (('OK', 'observed'), ('S', 'suppressed')))


def run(raw=RAW, **kwargs):
    return api().normalise_csv(raw, profile(raw), allow_synthetic=True, **kwargs)


def test_selects_one_stratum_and_preserves_missing_zero_and_locator():
    result = run()
    assert [c.value for c in result.series.cells] == [Decimal(12), None, Decimal(0)]
    assert result.series.cells[1].status == 'suppressed'
    assert result.series.cells[0].locator == 'csv-record:2'
    assert (result.rows_read, result.rows_selected, result.rows_excluded) == (4, 3, 1)
    assert result.profile_sha256 in result.series.lineage


def test_synthetic_requires_explicit_opt_in():
    with pytest.raises(ValueError, match='synthetic'):
        api().normalise_csv(RAW, profile())


def test_source_byte_hash_is_checked_before_parsing():
    with pytest.raises(ValueError, match='hash'):
        api().normalise_csv(RAW.replace(b'12', b'13'), profile(), allow_synthetic=True)


def test_unmapped_dimension_is_not_silently_collapsed():
    raw = RAW.replace(b'Sex\n', b'Sex,Age\n').replace(b'All\n', b'All,Total\n').replace(b'Female\n', b'Female,Total\n')
    with pytest.raises(ValueError, match='headers'):
        run(raw)


def test_duplicate_geographic_key_is_rejected():
    with pytest.raises(ValueError, match='duplicate'):
        run(RAW + b'A,2023,people,7,OK,All\n')


@pytest.mark.parametrize('replacement', [b'NaN', b'Infinity', b'1e9999', b'-1', b'1.5'])
def test_invalid_observed_count_is_rejected(replacement):
    with pytest.raises(ValueError):
        run(RAW.replace(b'12', replacement))


def test_suppressed_cell_with_numeric_payload_never_passes_through():
    with pytest.raises(ValueError, match='confidential'):
        run(RAW.replace(b'people,,S', b'people,99,S'))


def test_source_specific_suppression_token_is_mapped_explicitly():
    raw = RAW.replace(b'people,,S', b'people,CONCEALED,S')
    pr = replace(profile(raw), missing_tokens=('', 'CONCEALED'))
    result = api().normalise_csv(raw, pr, allow_synthetic=True)
    assert result.series.cells[1].value is None
    assert 'CONCEALED' not in str(result.series.public())


@pytest.mark.parametrize('old,new', [(b'12,OK', b'12,UNKNOWN'), (b'A,2023,people', b'A,2023,dollars')])
def test_unknown_status_or_unit_rejected(old, new):
    with pytest.raises(ValueError):
        run(RAW.replace(old, new))


def test_period_filter_does_not_mix_years():
    result = run(RAW + b'A,2020,people,500,OK,All\n')
    assert result.rows_excluded == 2
    assert len(result.series.cells) == 3


def test_profile_changes_are_bound_into_digest():
    p = profile()
    a = api().normalise_csv(RAW, p, allow_synthetic=True)
    b = api().normalise_csv(RAW, replace(p, metric='other'), allow_synthetic=True)
    assert a.profile_sha256 != b.profile_sha256
    assert a.series.digest != b.series.digest


def test_exponent_scales_values_without_float_conversion():
    result = api().normalise_csv(RAW, replace(profile(), unit_exponent=3), allow_synthetic=True)
    assert result.series.cells[0].value == Decimal(12000)


@pytest.mark.parametrize('extra', [b'bad,ragged\n', b'A,2023,people,2,OK,All,extra\n'])
def test_ragged_rows_rejected_even_outside_selected_cohort(extra):
    with pytest.raises(ValueError, match='shape'):
        run(RAW + extra)


def test_no_selected_observations_is_explicit_error():
    with pytest.raises(ValueError, match='empty'):
        api().normalise_csv(RAW, replace(profile(), selectors=(('Sex', 'Unknown'),)), allow_synthetic=True)


def test_bounded_parser_has_explicit_limits():
    with pytest.raises(ValueError, match='limit'):
        run(max_bytes=2)
    with pytest.raises(ValueError, match='limit'):
        run(max_rows=2)


def test_duplicate_header_rejected():
    with pytest.raises(ValueError, match='headers'):
        run(RAW.replace(b'Area,Year', b'Area,Area'))
