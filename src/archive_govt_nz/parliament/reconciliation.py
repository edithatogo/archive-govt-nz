"""Reconcile legacy Parliament listing *identities*, never payloads or rights."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

IndexView = Literal["evidence", "advice", "combined"]


@dataclass(frozen=True)
class IndexSlice:
    """Scope-bound observed source IDs from one listing view.

    The exhausted flag is established only by a caller's durable terminal-page
    accounting, never by a count displayed on a mutable index page.
    """

    view: IndexView
    scope: str
    snapshot: str
    reported_total: int
    ids: tuple[str, ...]
    exhausted: bool = False

    def __post_init__(self) -> None:
        """Reject missing scope, ambiguous identity, and invalid source counts."""
        if (
            self.view not in {"evidence", "advice", "combined"}
            or not self.scope.strip()
            or not self.snapshot.strip()
            or type(self.reported_total) is not int
            or self.reported_total < 0
            or not isinstance(self.ids, tuple)
            or any(not isinstance(item, str) or not item.strip() for item in self.ids)
            or len(self.ids) > self.reported_total
        ):
            message = "invalid_index_slice"
            raise ValueError(message)


@dataclass(frozen=True)
class IndexReconciliation:
    """Scope-labelled, exact-ID anti-join, with separate census claim flag."""

    scope: str
    matched_evidence: tuple[str, ...]
    matched_advice: tuple[str, ...]
    evidence_only: tuple[str, ...]
    advice_only: tuple[str, ...]
    combined_only: tuple[str, ...]
    ambiguous: tuple[str, ...]
    duplicate_rows: tuple[tuple[str, int], ...]
    observed_unique: int
    full_coverage: bool


def reconcile_indexes(
    evidence: IndexSlice, advice: IndexSlice, combined: IndexSlice
) -> IndexReconciliation:
    """Match exact IDs across specialist and combined indexes, without title joins.

    The *observed* union is not a historical coverage denominator unless every
    view carries complete row counts, matching snapshot and terminal proof.
    """
    if (
        evidence.view != "evidence"
        or advice.view != "advice"
        or combined.view != "combined"
    ):
        message = "index_view_mismatch"
        raise ValueError(message)
    if evidence.scope != advice.scope or evidence.scope != combined.scope:
        message = "index_scope_mismatch"
        raise ValueError(message)

    e, a, c = set(evidence.ids), set(advice.ids), set(combined.ids)
    ambiguous = e & a
    duplicates = tuple(
        (snapshot.view, len(snapshot.ids) - len(set(snapshot.ids)))
        for snapshot in sorted((evidence, advice, combined), key=lambda item: item.view)
        if len(snapshot.ids) != len(set(snapshot.ids))
    )
    return IndexReconciliation(
        scope=evidence.scope,
        matched_evidence=tuple(sorted((e & c) - ambiguous)),
        matched_advice=tuple(sorted((a & c) - ambiguous)),
        evidence_only=tuple(sorted((e - c) - ambiguous)),
        advice_only=tuple(sorted((a - c) - ambiguous)),
        combined_only=tuple(sorted(c - e - a)),
        ambiguous=tuple(sorted(ambiguous)),
        duplicate_rows=duplicates,
        observed_unique=len(e | a | c),
        full_coverage=(
            not ambiguous
            and all(
                item.exhausted and len(item.ids) == item.reported_total
                for item in (evidence, advice, combined)
            )
            and len({evidence.snapshot, advice.snapshot, combined.snapshot}) == 1
        ),
    )
