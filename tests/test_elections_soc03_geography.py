"""Independent synthetic arithmetic and population controls for SOC03."""
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from importlib import import_module

import pytest

from archive_govt_nz.domains.elections.soc_contracts import Cell, Series, Source


def api():
    try:
        return import_module('archive_govt_nz.domains.elections.soc_geography')
    except ModuleNotFoundError:
        pytest.fail('SOC03 implementation missing')


def source(identity='values'):
    return Source(identity, 'https://example.org/table', 'r1', sha256(identity.encode()).hexdigest(),
                  len(identity), datetime(2024, 1, 1, tzinfo=UTC),
                  datetime(2024, 1, 2, tzinfo=UTC), 'synthetic-rights', True)


def counts():
    return Series('numerator', date(2023, 3, 7), date(2023, 3, 7), 'sa2', '2023',
                  'residents', 'count', 'persons', (source(),),
                  (Cell('a', Decimal(100), 'observed', 'row:1'),
                   Cell('b', Decimal(20), 'provisional', 'row:2', ('rounded',))))


def crosswalk():
    g = api()
    return g.Crosswalk('sa2', '2023', 'general_electorate', '2025', 'residents',
                       'population', source('concordance'),
                       (g.Weight('a', 'X', Decimal('.75')),
                        g.Weight('a', 'Y', Decimal('.25')),
                        g.Weight('b', 'Y', Decimal(1))))


def test_weighted_counts_conserve_total_and_are_labelled_estimates():
    output = api().allocate_counts(counts(), crosswalk())
    assert [c.value for c in output.series.cells] == [Decimal(75), Decimal(45)]
    assert output.source_total == output.target_total == Decimal(120)
    assert output.conservation_error == 0
    assert all(c.status == 'estimated' for c in output.series.cells)
    assert output.series.method == 'population_weighted_count_estimate'
    assert {s.source_id for s in output.series.sources} == {'values', 'concordance'}
    assert 'rounded' in output.series.cells[1].flags


def test_fractional_counts_are_not_misrepresented_as_observed():
    s = replace(counts(), cells=(Cell('a', Decimal(3), 'observed', 'r1'), counts().cells[1]))
    result = api().allocate_counts(s, crosswalk())
    assert result.series.cells[0].value == Decimal('2.25')
    assert result.series.cells[0].status == 'estimated'


def test_suppressed_component_suppresses_each_affected_target_and_totals():
    s = replace(counts(), cells=(Cell('a', None, 'suppressed', 'row:1'), counts().cells[1]))
    result = api().allocate_counts(s, crosswalk())
    assert all(c.value is None and c.status == 'suppressed' for c in result.series.cells)
    assert result.source_total is result.target_total is result.conservation_error is None


@pytest.mark.parametrize('kind', ['median', 'mean', 'rate', 'index'])
def test_nonadditive_measures_cannot_be_spatially_averaged(kind):
    with pytest.raises(ValueError, match='count'):
        api().allocate_counts(replace(counts(), measure_kind=kind), crosswalk())


def test_population_and_boundary_mismatch_rejected():
    for s in [replace(counts(), universe='households'), replace(counts(), boundary_vintage='2020')]:
        with pytest.raises(ValueError, match='support'):
            api().allocate_counts(s, crosswalk())


def test_weight_sums_and_duplicate_edges_rejected():
    g = api()
    w = crosswalk()
    with pytest.raises(ValueError, match='weights'):
        replace(w, weights=(g.Weight('a', 'X', Decimal('.8')), g.Weight('b', 'Y', Decimal(1))))
    with pytest.raises(ValueError, match='duplicate'):
        replace(w, weights=w.weights + w.weights[:1])


@pytest.mark.parametrize('weight', [Decimal(-1), Decimal('1.1'), Decimal('NaN')])
def test_invalid_weights_rejected(weight):
    with pytest.raises(ValueError):
        api().Weight('a', 'X', weight)


def test_national_or_general_to_maori_broadcast_rejected():
    w = crosswalk()
    with pytest.raises(ValueError, match='disaggregation'):
        replace(w, source_system='national')
    with pytest.raises(ValueError, match='electorate'):
        replace(w, source_system='general_electorate', target_system='maori_electorate')


def test_unmatched_source_geographies_do_not_disappear():
    with pytest.raises(ValueError, match='coverage'):
        api().allocate_counts(replace(counts(), cells=counts().cells[:1]), crosswalk())


def test_rate_uses_counts_and_quality_not_mean_of_percentages():
    numerator = counts()
    denominator = replace(numerator, metric='total', cells=(
        Cell('a', Decimal(200), 'observed', 'r3'), Cell('b', Decimal(100), 'observed', 'r4')))
    result = api().derive_rate(numerator, denominator, metric='share', denominator_metric='total')
    assert [c.value for c in result.cells] == [Decimal(50), Decimal(20)]
    assert result.cells[1].status == 'provisional'
    assert 'rounded' in result.cells[1].flags
    assert set(result.lineage) == {numerator.digest, denominator.digest}


def test_zero_denominator_and_impossible_rate_are_unavailable():
    numerator = counts()
    denominator = replace(numerator, metric='total', cells=(
        Cell('a', Decimal(0), 'observed', 'r3'), Cell('b', Decimal(10), 'observed', 'r4')))
    result = api().derive_rate(numerator, denominator, metric='share', denominator_metric='total')
    assert all(c.value is None and c.status == 'unavailable' for c in result.cells)
    assert 'zero_denominator' in result.cells[0].flags
    assert 'numerator_exceeds_denominator' in result.cells[1].flags


def test_rates_require_declared_denominator_and_same_statistical_universe():
    n = counts()
    d = replace(n, metric='total')
    with pytest.raises(ValueError, match='denominator'):
        api().derive_rate(n, d, metric='rate', denominator_metric='wrong')
    with pytest.raises(ValueError, match='support'):
        api().derive_rate(n, replace(d, universe='registered_voters'), metric='rate', denominator_metric='total')
