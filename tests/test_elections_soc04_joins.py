"""SOC04 explicit time, coverage and population-context regressions."""
from dataclasses import replace
from datetime import UTC, date, datetime
from decimal import Decimal
from hashlib import sha256
from importlib import import_module

import pytest

from archive_govt_nz.domains.elections.soc_contracts import Cell, Series, Source

AS_OF = datetime(2026, 11, 16, tzinfo=UTC)


def api():
    try:
        return import_module('archive_govt_nz.domains.elections.soc_joins')
    except ModuleNotFoundError:
        pytest.fail('SOC04 implementation missing')


def pair():
    xsource = Source('census', 'https://example.org/census', '2023-r1', sha256(b'x').hexdigest(), 1,
                     datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 1, 2, tzinfo=UTC), 'synthetic', True)
    ysource = Source('votes', 'https://example.org/votes', '2026-preliminary', sha256(b'y').hexdigest(), 1,
                     datetime(2026, 11, 8, tzinfo=UTC), datetime(2026, 11, 9, tzinfo=UTC), 'synthetic', True)
    x = Series('income', date(2023, 3, 7), date(2023, 3, 7), 'general_electorate', '2025',
               'residents', 'median', 'NZD', (xsource,),
               (Cell('A', Decimal(20), 'observed', 'r1'),
                Cell('B', None, 'suppressed', 'r2'),
                Cell('unused', Decimal(80), 'observed', 'r3')))
    y = Series('party:test-party:vote-share', date(2026, 11, 7), date(2026, 11, 7),
               'general_electorate', '2025', 'registered_voters', 'rate', 'percent', (ysource,),
               tuple(Cell(g, Decimal(v), 'provisional', 'r:'+g) for g, v in [('A', 10), ('B', 20), ('C', 30)]))
    return x, y


def join(x=None, y=None, **kwargs):
    initial = pair()
    return api().join_exact(x or initial[0], y or initial[1], as_of=AS_OF,
                           population_relation='area_context', allow_synthetic=True, **kwargs)


def test_outcome_left_join_keeps_missing_and_suppressed_targets():
    panel = join()
    assert [p.geography_id for p in panel.pairs] == ['A', 'B', 'C']
    assert panel.unmatched_targets == ('C',)
    assert panel.unused_indicators == ('unused',)
    assert panel.pairs[1].exclusion == 'indicator_suppressed'
    assert panel.pairs[2].exclusion == 'missing_indicator'
    assert panel.lag_days == (date(2026, 11, 7) - date(2023, 3, 7)).days
    assert panel.public()['relationship'] == 'area_context_not_individual'


@pytest.mark.parametrize('field,value', [('boundary_vintage', '2020'), ('geography_system', 'maori_electorate')])
def test_incompatible_geography_is_rejected(field, value):
    x, _ = pair()
    with pytest.raises(ValueError, match='geographic'):
        join(x=replace(x, **{field: value}))


def test_population_difference_requires_explicit_context():
    x, y = pair()
    with pytest.raises(ValueError, match='population'):
        api().join_exact(x, y, as_of=AS_OF, allow_synthetic=True)


def test_synthetic_opt_in_and_empirical_mixing_controls():
    x, y = pair()
    with pytest.raises(ValueError, match='synthetic'):
        api().join_exact(x, y, as_of=AS_OF, population_relation='area_context')
    observed_y = replace(y, sources=(replace(y.sources[0], synthetic=False),))
    with pytest.raises(ValueError, match='synthetic'):
        join(y=observed_y)


def test_future_publication_is_rejected_for_both_inputs():
    x, y = pair()
    late = datetime(2026, 12, 1, tzinfo=UTC)
    for target in ['indicator', 'outcome']:
        original = x if target == 'indicator' else y
        changed = replace(original, sources=(replace(original.sources[0], published_at=late, captured_at=late),))
        with pytest.raises(ValueError, match='publication'):
            join(x=changed if target == 'indicator' else x, y=changed if target == 'outcome' else y)


def test_future_predictor_measurement_rejected():
    x, _ = pair()
    with pytest.raises(ValueError, match='predictor'):
        join(x=replace(x, period_start=date(2026, 11, 8), period_end=date(2026, 11, 8)))


def test_lag_bound_is_explicit():
    with pytest.raises(ValueError, match='stale'):
        join(max_lag_days=30)
    with pytest.raises(ValueError, match='lag'):
        join(max_lag_days=-1)


def test_prospective_evaluation_allows_later_outcomes_but_not_later_predictors():
    cutoff = datetime(2026, 11, 6, tzinfo=UTC)
    assert join(predictor_cutoff=cutoff, event_at=datetime(2026, 11, 7, tzinfo=UTC)).public()['analysis_mode'] == 'prospective_evaluation'
    x, _ = pair()
    late = datetime(2026, 11, 7, tzinfo=UTC)
    x = replace(x, sources=(replace(x.sources[0], published_at=late, captured_at=late),))
    with pytest.raises(ValueError, match='predictor publication'):
        join(x=x, predictor_cutoff=cutoff, event_at=datetime(2026, 11, 7, tzinfo=UTC))


def test_prospective_cutoff_cannot_follow_election_start():
    with pytest.raises(ValueError, match='cutoff'):
        join(predictor_cutoff=datetime(2026, 11, 8, tzinfo=UTC), event_at=datetime(2026, 11, 7, tzinfo=UTC))


def test_naive_asof_is_rejected():
    x, y = pair()
    with pytest.raises(ValueError, match='timezone'):
        api().join_exact(x, y, as_of=datetime(2026, 11, 16), population_relation='area_context', allow_synthetic=True)


def test_panel_hash_binds_source_vintage_and_cutoff():
    panel = join()
    x, y = pair()
    changed = replace(y, sources=(replace(y.sources[0], revision='corrected'),))
    assert panel.digest != join(y=changed).digest
    api().verify_panel_inputs(panel, indicator_sha256=x.digest, outcome_sha256=y.digest)
    with pytest.raises(ValueError, match='input digest'):
        api().verify_panel_inputs(panel, indicator_sha256='0'*64, outcome_sha256=y.digest)


def test_declared_outcome_denominator_and_party_identity_survive_join():
    public = join().public()
    assert public['outcome']['metric'] == 'party:test-party:vote-share'
    assert public['outcome']['universe'] == 'registered_voters'
    assert public['indicator']['unit'] == 'NZD'


def test_prospective_requires_explicit_event_time_not_a_timezone_guess():
    with pytest.raises(ValueError, match='event'):
        join(predictor_cutoff=datetime(2026, 11, 6, tzinfo=UTC))


def test_event_time_comparison_is_timezone_aware():
    from datetime import timedelta, timezone
    event = datetime(2026, 11, 7, tzinfo=timezone(timedelta(hours=13)))
    # 12:00 UTC on 6 Nov is AFTER midnight NZDT on 7 Nov.
    with pytest.raises(ValueError, match='cutoff'):
        join(predictor_cutoff=datetime(2026, 11, 6, 12, tzinfo=UTC), event_at=event)
