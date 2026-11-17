"""SOC05 independent numerical references and missingness-policy controls."""
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
from statistics import correlation

import pytest

from archive_govt_nz.domains.elections.soc_contracts import Cell, Series, Source
from archive_govt_nz.domains.elections.soc_joins import join_exact


def api():
    try:
        return import_module('archive_govt_nz.domains.elections.soc_analysis')
    except ModuleNotFoundError:
        pytest.fail('SOC05 implementation missing')


def panel(xs=(1, 2, 3, 4), ys=(2, 5, 6, 10)):
    original = Source('s', 'https://example.org/data', 'r1', sha256(b'data').hexdigest(), 4,
                      datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 2, tzinfo=UTC), 'synthetic', True)
    def series(values, metric):
        return Series(metric, date(2023, 1, 1), date(2023, 1, 1), 'sa2', '2023',
                      'residents', 'mean', 'units', (original,),
                      tuple(Cell(str(k), Decimal(str(v)), 'observed', 'r:'+str(k))
                            for k, v in enumerate(values)))
    return join_exact(series(xs, 'x'), series(ys, 'y'),
                      as_of=datetime(2026, 1, 1, tzinfo=UTC), allow_synthetic=True)


def test_pearson_matches_independent_standard_library_oracle():
    result = api().analyse(panel())
    assert result.status == 'ok'
    assert float(result.pearson) == pytest.approx(correlation([1,2,3,4], [2,5,6,10]))
    assert result.n_pairs == result.target_count == 4
    assert result.panel_digest == panel().digest
    assert result.public()['causal_effect'] is None
    assert result.public()['p_value'] is None


def test_spearman_uses_average_ties():
    result = api().analyse(panel((1, 2, 2, 4), (4, 1, 1, 2)))
    expected = correlation([1, 2.5, 2.5, 4], [4, 1.5, 1.5, 3])
    assert float(result.spearman) == pytest.approx(expected)


@pytest.mark.parametrize('ys,expected', [((2,4,6,8), 1), ((8,6,4,2), -1)])
def test_perfect_direction_is_not_numerically_out_of_range(ys, expected):
    result = api().analyse(panel(ys=ys))
    assert float(result.pearson) == pytest.approx(expected)
    assert -1 <= result.pearson <= 1


def test_zero_variance_and_small_sample_return_no_effect():
    for subject, status in [(panel((1,1,1,1)), 'zero_variance'), (panel((1,2), (3,4)), 'insufficient_data')]:
        result = api().analyse(subject)
        assert result.status == status
        assert result.pearson is result.spearman is None


def test_confidential_cells_are_excluded_without_imputation():
    p = panel()
    x = replace(p.indicator, cells=(Cell('0', None, 'suppressed', 'r0'),) + p.indicator.cells[1:])
    p = replace(p, indicator=x)
    result = api().analyse(p)
    assert result.n_pairs == 3
    assert result.excluded == (('0', 'indicator_suppressed'),)
    assert result.coverage_fraction == Decimal('.75')


def test_estimated_inputs_require_explicit_analysis_policy():
    p = panel()
    first = replace(p.indicator.cells[0], status='estimated')
    p = replace(p, indicator=replace(p.indicator, cells=(first,) + p.indicator.cells[1:]))
    assert api().analyse(p).n_pairs == 3
    assert api().analyse(p, include_estimated=True).n_pairs == 4
    assert api().analyse(p, include_estimated=True).public()['include_estimated'] is True


def test_provisional_outcomes_can_be_excluded_explicitly():
    p = panel()
    p = replace(p, outcome=replace(p.outcome, cells=tuple(replace(c, status='provisional') for c in p.outcome.cells)))
    assert api().analyse(p).n_pairs == 4
    assert api().analyse(p, include_provisional=False).status == 'insufficient_data'


def test_leave_one_out_bounds_match_independent_recalculation():
    xs = [1,2,3,4,5]
    ys = [2,6,7,8,3]
    independent = [correlation(xs[:k]+xs[k+1:], ys[:k]+ys[k+1:]) for k in range(5)]
    result = api().analyse(panel(xs, ys))
    assert float(result.leave_one_out_min) == pytest.approx(min(independent))
    assert float(result.leave_one_out_max) == pytest.approx(max(independent))
    assert result.public()['sensitivity_method'] == 'leave_one_area_out_not_confidence_interval'


def test_large_offsets_do_not_destroy_covariance_precision():
    # Construct exactly, independent of ambient Decimal precision.
    xs = [Decimal('10000000000000000000' + str(k) + '00000000000000000000') for k in [1,2,3,4]]
    result = api().analyse(panel(xs, (2,4,6,8)))
    assert float(result.pearson) == pytest.approx(1)


def test_invalid_sample_policy_is_rejected():
    for minimum in [0, 2, True]:
        with pytest.raises(ValueError, match='minimum'):
            api().analyse(panel(), minimum_pairs=minimum)


def test_flags_do_not_lose_allocation_estimate_status():
    p = panel()
    cell = replace(p.indicator.cells[0], flags=('population_allocation_estimate',))
    p = replace(p, indicator=replace(p.indicator, cells=(cell,) + p.indicator.cells[1:]))
    assert api().analyse(p).n_pairs == 3


def test_analysis_does_not_claim_individual_or_causal_effect():
    public = api().analyse(panel()).public()
    assert public['method'] == 'unweighted_area_level_descriptive_association'
    assert public['synthetic'] is True
    assert 'not individual voter behaviour' in public['limitation']


def test_minimum_sample_policy_is_preserved_in_receipt():
    result = api().analyse(panel(), minimum_pairs=4)
    assert result.public()['minimum_pairs'] == 4
