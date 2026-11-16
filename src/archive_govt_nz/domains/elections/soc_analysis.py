"""SOC05 descriptive ecological association and sensitivity, never causal inference."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext

from archive_govt_nz.domains.elections.soc_contracts import decimal_text, require
from archive_govt_nz.domains.elections.soc_joins import Panel


def _moments(xs: list[Decimal], ys: list[Decimal]
             ) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal]:
    n = Decimal(len(xs))
    mx, my = sum(xs, Decimal(0)) / n, sum(ys, Decimal(0)) / n
    dx, dy = [x - mx for x in xs], [y - my for y in ys]
    return (mx, my, sum((x * x for x in dx), Decimal(0)),
            sum((y * y for y in dy), Decimal(0)),
            sum((x * y for x, y in zip(dx, dy, strict=True)), Decimal(0)))


def _correlation(xx: Decimal, yy: Decimal, xy: Decimal) -> Decimal | None:
    if xx <= 0 or yy <= 0:
        return None
    result = max(Decimal(-1), min(Decimal(1), xy / (xx * yy).sqrt()))
    with localcontext() as context:
        context.prec = 34
        return +result


def _ranks(values: list[Decimal]) -> list[Decimal]:
    ranks = [Decimal(0)] * len(values)
    ordered = sorted(range(len(values)), key=values.__getitem__)
    start = 0
    while start < len(ordered):
        end = start + 1
        while end < len(ordered) and values[ordered[end]] == values[ordered[start]]:
            end += 1
        rank = Decimal(start + 1 + end) / 2
        for index in ordered[start:end]:
            ranks[index] = rank
        start = end
    return ranks


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """A result bound to its complete panel, sample policy and exclusions."""

    panel_digest: str
    target_count: int
    n_pairs: int
    excluded: tuple[tuple[str, str], ...]
    status: str
    pearson: Decimal | None
    spearman: Decimal | None
    leave_one_out_min: Decimal | None
    leave_one_out_max: Decimal | None
    include_estimated: bool
    include_provisional: bool
    synthetic: bool
    minimum_pairs: int

    @property
    def coverage_fraction(self) -> Decimal:
        """Report the actual analysed fraction, not only raw geographic matches."""
        with localcontext() as context:
            context.prec = 34
            return Decimal(self.n_pairs) / self.target_count if self.target_count else Decimal(0)

    def public(self) -> dict[str, object]:
        """Publish descriptive values with explicit inference and sensitivity limits."""
        return {'panel_digest': self.panel_digest, 'status': self.status,
                'target_count': self.target_count, 'n_pairs': self.n_pairs,
                'excluded': [{'geography_id': geo, 'reason': reason} for geo, reason in self.excluded],
                'coverage_fraction': decimal_text(self.coverage_fraction),
                'pearson': None if self.pearson is None else decimal_text(self.pearson),
                'spearman': None if self.spearman is None else decimal_text(self.spearman),
                'leave_one_out_min': None if self.leave_one_out_min is None else decimal_text(self.leave_one_out_min),
                'leave_one_out_max': None if self.leave_one_out_max is None else decimal_text(self.leave_one_out_max),
                'minimum_pairs': self.minimum_pairs,
                'include_estimated': self.include_estimated,
                'include_provisional': self.include_provisional,
                'method': 'unweighted_area_level_descriptive_association',
                'sensitivity_method': 'leave_one_area_out_not_confidence_interval',
                'synthetic': self.synthetic, 'p_value': None, 'causal_effect': None,
                'limitation': 'Area-level association, not individual voter behaviour; not causal. '
                              'Missingness, confidentiality, spatial dependence and measurement error remain.'}


def analyse(panel: Panel, *, minimum_pairs: int = 3, include_estimated: bool = False,
            include_provisional: bool = True) -> AnalysisResult:
    """Compute stable Pearson/Spearman and O(n) leave-one-area-out sensitivity."""
    require(type(minimum_pairs) is int and minimum_pairs >= 3, 'invalid minimum sample')
    require(type(include_estimated) is bool and type(include_provisional) is bool,
            'explicit quality policy required')
    xs: list[Decimal] = []
    ys: list[Decimal] = []
    excluded = []
    for pair in panel.pairs:
        reason = pair.exclusion
        if not reason and pair.indicator is not None:
            cells = (pair.indicator, pair.outcome)
            estimated = any(c.status == 'estimated' or 'population_allocation_estimate' in c.flags for c in cells)
            provisional = any(c.status == 'provisional' or 'input_provisional' in c.flags for c in cells)
            if estimated and not include_estimated:
                reason = 'estimated_excluded'
            elif provisional and not include_provisional:
                reason = 'provisional_excluded'
        if reason:
            excluded.append((pair.geography_id, reason))
        elif pair.indicator is not None and pair.indicator.value is not None and pair.outcome.value is not None:
            xs.append(pair.indicator.value)
            ys.append(pair.outcome.value)
    pearson = spearman = lower = upper = None
    status = 'insufficient_data'
    if len(xs) >= minimum_pairs:
        with localcontext() as context:
            context.prec = 100
            mx, my, xx, yy, xy = _moments(xs, ys)
            pearson = _correlation(xx, yy, xy)
            _, _, rx, ry, rxy = _moments(_ranks(xs), _ranks(ys))
            spearman = _correlation(rx, ry, rxy)
            status = 'ok' if pearson is not None else 'zero_variance'
            if len(xs) - 1 >= minimum_pairs:
                factor = Decimal(len(xs)) / (len(xs) - 1)
                leave_one_out = []
                for x, y in zip(xs, ys, strict=True):
                    dx, dy = x - mx, y - my
                    score = _correlation(xx - factor * dx * dx,
                                         yy - factor * dy * dy, xy - factor * dx * dy)
                    if score is not None:
                        leave_one_out.append(score)
                if leave_one_out:
                    lower, upper = min(leave_one_out), max(leave_one_out)
    return AnalysisResult(panel.digest, len(panel.outcome.cells), len(xs), tuple(excluded),
                          status, pearson, spearman, lower, upper,
                          include_estimated, include_provisional, panel.indicator.synthetic, minimum_pairs)
