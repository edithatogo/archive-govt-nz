"""SOC03 count-only population concordances and compatible count-derived rates.

A supplied concordance still requires independent source/rights qualification.
Allocation is always an estimate; direct source-published target tables take priority.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, localcontext
from hashlib import sha256

from archive_govt_nz.domains.elections.soc_contracts import (
    GEOGRAPHIES, Cell, Series, Source, decimal_text, require, text,
)


def _sources(*groups: tuple[Source, ...]) -> tuple[Source, ...]:
    result: dict[str, Source] = {}
    for group in groups:
        for source in group:
            require(source.source_id not in result or result[source.source_id] == source,
                    'conflicting source identity')
            result[source.source_id] = source
    return tuple(sorted(result.values(), key=lambda s: s.source_id))


@dataclass(frozen=True, slots=True)
class Weight:
    """A population-specific fraction of one source area assigned to one target."""

    source_id: str
    target_id: str
    fraction: Decimal

    def __post_init__(self) -> None:
        text(self.source_id, 'source area')
        text(self.target_id, 'target area')
        decimal_text(self.fraction)
        require(0 < self.fraction <= 1, 'invalid weight')


@dataclass(frozen=True, slots=True)
class Crosswalk:
    """A complete count allocation on declared boundary vintages and population."""

    source_system: str
    source_boundary: str
    target_system: str
    target_boundary: str
    universe: str
    basis: str
    source: Source
    weights: tuple[Weight, ...]

    def __post_init__(self) -> None:
        require(self.source_system in GEOGRAPHIES and self.target_system in GEOGRAPHIES,
                'invalid geography system')
        require(self.source_system not in {'national', 'region'},
                'national/regional disaggregation unsupported')
        require({self.source_system, self.target_system}
                != {'general_electorate', 'maori_electorate'},
                'overlapping electorate systems cannot be pooled')
        require(self.basis == 'population', 'population weights required')
        for name in ('source_boundary', 'target_boundary', 'universe'):
            text(getattr(self, name), name)
        require(bool(self.weights), 'empty weights')
        require(len({(w.source_id, w.target_id) for w in self.weights}) == len(self.weights),
                'duplicate concordance edges')
        totals: dict[str, Decimal] = {}
        with localcontext() as context:
            context.prec = 100
            for weight in self.weights:
                totals[weight.source_id] = totals.get(weight.source_id, Decimal(0)) + weight.fraction
        require(all(total == 1 for total in totals.values()), 'weights must sum to one')

    @property
    def digest(self) -> str:
        """Bind every weight and its statistical support, not just an external URL."""
        data = [self.source_system, self.source_boundary, self.target_system,
                self.target_boundary, self.universe, self.basis, self.source.public(),
                sorted((w.source_id, w.target_id, decimal_text(w.fraction)) for w in self.weights)]
        return sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class AllocationResult:
    """Expose conservation only when no contributor is confidential or missing."""

    series: Series
    source_total: Decimal | None
    target_total: Decimal | None
    conservation_error: Decimal | None


def allocate_counts(series: Series, crosswalk: Crosswalk) -> AllocationResult:
    """Allocate additive counts; propagate any confidential contributor to each target."""
    require(series.measure_kind == 'count', 'only counts are additive')
    require((series.geography_system, series.boundary_vintage, series.universe)
            == (crosswalk.source_system, crosswalk.source_boundary, crosswalk.universe),
            'source support mismatch')
    by_id = {c.geography_id: c for c in series.cells}
    require(set(by_id) == {w.source_id for w in crosswalk.weights},
            'source/concordance coverage mismatch')
    targets: dict[str, list[tuple[Cell, Decimal]]] = {}
    for weight in crosswalk.weights:
        targets.setdefault(weight.target_id, []).append((by_id[weight.source_id], weight.fraction))
    cells = []
    with localcontext() as context:
        context.prec = 100
        for target, components in sorted(targets.items()):
            statuses = {cell.status for cell, _ in components}
            flags = {'population_allocation_estimate'}
            flags.update(flag for cell, _ in components for flag in cell.flags)
            flags.update('input_' + status for status in statuses)
            missing = next((s for s in ('suppressed', 'missing', 'unavailable') if s in statuses), None)
            value = None if missing else sum((cell.value * weight for cell, weight in components
                                              if cell.value is not None), Decimal(0))
            cells.append(Cell(target, value, missing or 'estimated',
                              'crosswalk:' + crosswalk.digest, tuple(sorted(flags))))
        complete = all(cell.value is not None for cell in series.cells)
        source_total = sum((c.value for c in series.cells if c.value is not None), Decimal(0)) if complete else None
        target_total = sum((c.value for c in cells if c.value is not None), Decimal(0)) if complete else None
        error = target_total - source_total if target_total is not None and source_total is not None else None
    output = Series(series.metric, series.period_start, series.period_end,
                    crosswalk.target_system, crosswalk.target_boundary, series.universe,
                    'count', series.unit, _sources(series.sources, (crosswalk.source,)),
                    tuple(cells), 'population_weighted_count_estimate',
                    (series.digest, crosswalk.digest))
    return AllocationResult(output, source_total, target_total, error)


def derive_rate(numerator: Series, denominator: Series, *, metric: str,
                denominator_metric: str) -> Series:
    """Derive percentages from compatible counts; never infer a missing denominator."""
    require(denominator.metric == denominator_metric, 'wrong denominator metric')
    require(numerator.measure_kind == denominator.measure_kind == 'count',
            'rates require count inputs')
    dimensions = ('period_start', 'period_end', 'geography_system', 'boundary_vintage', 'universe', 'unit')
    require(all(getattr(numerator, key) == getattr(denominator, key) for key in dimensions),
            'incompatible rate support')
    n_by_id = {c.geography_id: c for c in numerator.cells}
    require(set(n_by_id) <= {c.geography_id for c in denominator.cells},
            'numerator without denominator geography')
    cells = []
    for den in sorted(denominator.cells, key=lambda c: c.geography_id):
        num = n_by_id.get(den.geography_id)
        statuses = {den.status, num.status if num else 'missing'}
        flags = set(den.flags) | (set(num.flags) if num else set())
        flags.update('input_' + status for status in statuses)
        missing = next((s for s in ('suppressed', 'missing', 'unavailable') if s in statuses), None)
        value = None
        status = missing or ('estimated' if 'estimated' in statuses else
                             'provisional' if 'provisional' in statuses else 'observed')
        if not missing and num is not None and num.value is not None and den.value is not None:
            if den.value == 0 or num.value > den.value:
                status = 'unavailable'
                flags.add('zero_denominator' if den.value == 0 else 'numerator_exceeds_denominator')
            else:
                with localcontext() as context:
                    context.prec = 50
                    value = 100 * num.value / den.value
        cells.append(Cell(den.geography_id, value, status, 'derived-rate', tuple(sorted(flags))))
    return Series(metric, numerator.period_start, numerator.period_end,
                  numerator.geography_system, numerator.boundary_vintage, numerator.universe,
                  'rate', 'percent', _sources(numerator.sources, denominator.sources),
                  tuple(cells), 'count_derived_percentage', (numerator.digest, denominator.digest))
