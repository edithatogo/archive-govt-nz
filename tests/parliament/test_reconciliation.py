"""Synthetic Parliament index reconciliation without submission payloads."""

import pytest

from archive_govt_nz.parliament.reconciliation import (
    IndexSlice,
    IndexView,
    reconcile_indexes,
)


def view(
    name: IndexView,
    *ids: str,
    scope: str = "all-47-54",
    total: int = 100,
    terminal: bool = False,
    snapshot: str = "observed-20261117",
) -> IndexSlice:
    """Provide a synthetic source listing with explicit scope and exhaustion."""
    return IndexSlice(name, scope, snapshot, total, tuple(ids), terminal)


def test_exact_source_ids_match_without_summing_overlapping_indexes() -> None:
    """Combined view overlaps specialist views by ID, not index totals."""
    evidence = view("evidence", "54SC_EVI_A", "54SC_EVI_B")
    advice = view("advice", "54SC_ADV_C")
    combined = view("combined", "54SC_EVI_A", "54SC_ADV_C", "54SC_OTHER_D")
    result = reconcile_indexes(evidence, advice, combined)
    assert result.matched_evidence == ("54SC_EVI_A",)
    assert result.matched_advice == ("54SC_ADV_C",)
    assert result.evidence_only == ("54SC_EVI_B",)
    assert result.advice_only == ()
    assert result.combined_only == ("54SC_OTHER_D",)
    assert result.observed_unique == 4
    assert result.full_coverage is False


def test_duplicates_remain_explicit_and_are_not_new_source_identities() -> None:
    """Overlapping page or desktop/mobile rows cannot inflate identity coverage."""
    evidence = view("evidence", "54SC_EVI_A", "54SC_EVI_A")
    advice = view("advice", "54SC_ADV_C")
    combined = view("combined", "54SC_EVI_A", "54SC_ADV_C", "54SC_ADV_C")
    result = reconcile_indexes(evidence, advice, combined)
    assert result.duplicate_rows == (("combined", 1), ("evidence", 1))
    assert result.observed_unique == 2
    assert result.full_coverage is False


def test_specialist_overlap_is_ambiguous_not_falsely_classified() -> None:
    """Same source ID in evidence and advice demands explicit adjudication."""
    result = reconcile_indexes(
        view("evidence", "54SC_OVERLAP"),
        view("advice", "54SC_OVERLAP"),
        view("combined", "54SC_OVERLAP"),
    )
    assert result.ambiguous == ("54SC_OVERLAP",)
    assert result.matched_evidence == ()
    assert result.matched_advice == ()
    assert result.full_coverage is False


def test_scope_mismatch_fails_closed() -> None:
    """All-Parliaments and current-Parliament filters are not comparable."""
    with pytest.raises(ValueError, match="index_scope_mismatch"):
        reconcile_indexes(
            view("evidence", "54SC_EVI_A"),
            view("advice", "54SC_ADV_C", scope="current"),
            view("combined", "54SC_EVI_A"),
        )


def test_complete_requires_same_snapshot_terminal_and_exhausted_row_counts() -> None:
    """Do not promote a partial first-page anti-join into an all-index census."""
    full = reconcile_indexes(
        view("evidence", "E", total=1, terminal=True),
        view("advice", "A", total=1, terminal=True),
        view("combined", "E", "A", total=2, terminal=True),
    )
    assert full.full_coverage is True
    partial = reconcile_indexes(
        view("evidence", "E", total=1, terminal=True),
        view("advice", "A", total=1, terminal=True, snapshot="different"),
        view("combined", "E", "A", total=2, terminal=True),
    )
    assert partial.full_coverage is False
    unproven = reconcile_indexes(
        view("evidence", "E", total=1),
        view("advice", "A", total=1, terminal=True),
        view("combined", "E", "A", total=2, terminal=True),
    )
    assert unproven.full_coverage is False


def test_invalid_identity_or_count_rejected_without_dropping_rows() -> None:
    """Empty IDs, negative counts or swapped view labels fail without loss."""
    with pytest.raises(ValueError, match="invalid_index_slice"):
        view("evidence", "", total=1)
    with pytest.raises(ValueError, match="invalid_index_slice"):
        view("evidence", "E", total=-1)
    with pytest.raises(ValueError, match="invalid_index_slice"):
        view("evidence", "E", "A", total=1)
    with pytest.raises(ValueError, match="index_view_mismatch"):
        reconcile_indexes(
            view("advice", "E"), view("advice", "A"), view("combined", "E")
        )
