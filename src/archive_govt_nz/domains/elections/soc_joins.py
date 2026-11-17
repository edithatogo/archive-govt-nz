"""SOC04 explicit contextual exact joins with source-vintage and time constraints.

No spatial conversion, donor resolution or individual-level linkage is performed.
Prospective evaluation separates predictor availability from later outcome evaluation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256

from archive_govt_nz.domains.elections.soc_contracts import (
    Cell, Series, aware, digest, require,
)


@dataclass(frozen=True, slots=True)
class Pair:
    """An outcome-left matched row; a missing indicator is not a zero observation."""

    geography_id: str
    indicator: Cell | None
    outcome: Cell

    @property
    def exclusion(self) -> str | None:
        """Give explicit missingness reasons while retaining all outcome rows."""
        if self.indicator is None:
            return 'missing_indicator'
        reasons = []
        if self.indicator.value is None:
            reasons.append('indicator_' + self.indicator.status)
        if self.outcome.value is None:
            reasons.append('outcome_' + self.outcome.status)
        return ';'.join(reasons) or None


@dataclass(frozen=True, slots=True)
class Panel:
    """A reproducible join specification whose rows derive only from validated inputs."""

    indicator: Series
    outcome: Series
    as_of: datetime
    population_relation: str = 'same_population'
    predictor_cutoff: datetime | None = None
    max_lag_days: int | None = None
    allow_synthetic: bool = False
    event_at: datetime | None = None

    def __post_init__(self) -> None:
        aware(self.as_of)
        require(self.indicator.synthetic == self.outcome.synthetic,
                'mixed synthetic/empirical inputs')
        require(not self.indicator.synthetic or self.allow_synthetic,
                'synthetic input not allowed')
        require((self.indicator.geography_system, self.indicator.boundary_vintage)
                == (self.outcome.geography_system, self.outcome.boundary_vintage),
                'geographic support mismatch')
        require(self.population_relation in {'same_population', 'area_context'},
                'invalid population relationship')
        require(self.population_relation == 'area_context'
                or self.indicator.universe == self.outcome.universe,
                'population relationship must be explicit')
        require(bool(self.outcome.cells), 'empty electoral outcome')
        require(self.outcome.period_end <= self.as_of.date(), 'future outcome period')
        require(self.lag_days >= 0, 'predictor measurement follows outcome')
        if self.max_lag_days is not None:
            require(type(self.max_lag_days) is int and self.max_lag_days >= 0,
                    'invalid lag limit')
            require(self.lag_days <= self.max_lag_days, 'stale predictor')
        for series in (self.indicator, self.outcome):
            require(all(s.published_at <= self.as_of for s in series.sources),
                    'input publication follows analysis cutoff')
        if self.predictor_cutoff is not None:
            aware(self.predictor_cutoff)
            require(self.event_at is not None, 'explicit event time required')
            if self.event_at is None:
                raise ValueError('explicit event time required')
            aware(self.event_at)
            require(self.event_at.date() == self.outcome.period_start, 'event date mismatch')
            require(self.predictor_cutoff <= min(self.as_of, self.event_at),
                    'predictor cutoff follows outcome start')
            require(self.indicator.period_end <= self.predictor_cutoff.date(),
                    'predictor measurement follows cutoff')
            require(all(s.published_at <= self.predictor_cutoff for s in self.indicator.sources),
                    'predictor publication follows cutoff')

    @property
    def lag_days(self) -> int:
        """Age of predictor measurement at the start of the outcome reference period."""
        return (self.outcome.period_start - self.indicator.period_end).days

    @property
    def pairs(self) -> tuple[Pair, ...]:
        """Reconstruct a one-to-one outcome-left join without mutable cached results."""
        lookup = {cell.geography_id: cell for cell in self.indicator.cells}
        return tuple(Pair(cell.geography_id, lookup.get(cell.geography_id), cell)
                     for cell in sorted(self.outcome.cells, key=lambda cell: cell.geography_id))

    @property
    def unmatched_targets(self) -> tuple[str, ...]:
        """List outcome geographies lacking any indicator observation."""
        return tuple(pair.geography_id for pair in self.pairs if pair.indicator is None)

    @property
    def unused_indicators(self) -> tuple[str, ...]:
        """List source geographies not used, rather than silently discarding them."""
        target = {cell.geography_id for cell in self.outcome.cells}
        return tuple(sorted(cell.geography_id for cell in self.indicator.cells
                            if cell.geography_id not in target))

    def public(self) -> dict[str, object]:
        """Export full input semantics and explicitly separate missingness from zero."""
        return {'schema_version': 'soc-panel-v1', 'indicator': self.indicator.public(),
                'outcome': self.outcome.public(), 'indicator_digest': self.indicator.digest,
                'outcome_digest': self.outcome.digest, 'as_of': self.as_of.isoformat(),
                'analysis_mode': 'retrospective' if self.predictor_cutoff is None else 'prospective_evaluation',
                'predictor_cutoff': self.predictor_cutoff.isoformat() if self.predictor_cutoff else None,
                'relationship': 'area_context_not_individual' if self.population_relation == 'area_context'
                                else 'same_statistical_population',
                'event_at': self.event_at.isoformat() if self.event_at else None,
                'lag_days': self.lag_days, 'max_lag_days': self.max_lag_days,
                'target_count': len(self.outcome.cells),
                'unmatched_targets': list(self.unmatched_targets),
                'unused_indicators': list(self.unused_indicators),
                'pairs': [{'geography_id': p.geography_id,
                           'indicator': p.indicator.public() if p.indicator else None,
                           'outcome': p.outcome.public(), 'exclusion': p.exclusion}
                          for p in self.pairs],
                'synthetic': self.indicator.synthetic, 'causal_claim': False}

    @property
    def digest(self) -> str:
        """Bind source vintages, policy, full rows and missingness in one identity."""
        return sha256(json.dumps(self.public(), sort_keys=True, ensure_ascii=False,
                                 separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def join_exact(indicator: Series, outcome: Series, *, as_of: datetime,
               population_relation: str = 'same_population',
               predictor_cutoff: datetime | None = None,
               max_lag_days: int | None = None, allow_synthetic: bool = False,
               event_at: datetime | None = None) -> Panel:
    """Return a validated exact join; any geography conversion must occur upstream."""
    return Panel(indicator, outcome, as_of, population_relation,
                 predictor_cutoff, max_lag_days, allow_synthetic, event_at)


def verify_panel_inputs(panel: Panel, *, indicator_sha256: str,
                        outcome_sha256: str) -> None:
    """Compare independently supplied input identities, not a re-sealed result's claim."""
    digest(indicator_sha256)
    digest(outcome_sha256)
    require(panel.indicator.digest == indicator_sha256
            and panel.outcome.digest == outcome_sha256, 'panel input digest mismatch')
