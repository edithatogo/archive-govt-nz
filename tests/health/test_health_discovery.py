"""Property, contract, metamorphic, and simulation tests for health discovery."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.health_discovery import (
    classify_dataset,
    normalize_scoped_records,
    reconcile_rerun,
    reconcile_transport_results,
)
from archive_govt_nz.health_scope import DEFAULT_SCOPES


def test_group_scope_uses_ckan_solr_filter_query() -> None:
    """CKAN rejects the legacy groups parameter on the live catalogue."""
    group_scope = next(
        scope for scope in DEFAULT_SCOPES if scope["id"] == "group-health"
    )
    assert group_scope["fq"] == "groups:health"
    assert "groups" not in group_scope


def _record(identifier: str, *, licence: str | None = "cc-by") -> dict[str, object]:
    return {
        "id": identifier,
        "name": identifier,
        "title": f"Health record {identifier}",
        "metadata_modified": "2026-08-11T00:00:00Z",
        "license_id": licence,
        "organization": {"id": "org", "name": "health-org", "title": "Health"},
        "resources": [],
    }


@given(st.lists(st.text(min_size=1), min_size=1, unique=True))
def test_deduplication_is_metamorphic_under_scope_order(ids: list[str]) -> None:
    """Reversing overlapping query order cannot change normalized content."""
    left = normalize_scoped_records({"keyword": [_record(item) for item in ids]})
    right = normalize_scoped_records(
        {"group": [_record(item) for item in reversed(ids)]}
    )
    assert [item["dataset_id"] for item in left] == sorted(ids)
    assert [item["dataset_id"] for item in right] == sorted(ids)


def test_transport_parity_and_mismatch_are_explicit() -> None:
    """GET fallback cannot hide a count or identifier conflict."""
    post = {"count": 2, "results": [_record("a"), _record("b")]}
    equivalent_get = {"count": 2, "results": [_record("b"), _record("a")]}
    mismatch = {"count": 2, "results": [_record("a"), _record("c")]}

    assert reconcile_transport_results(post, equivalent_get) == "equivalent"
    assert reconcile_transport_results(post, mismatch) == "conflict"
    assert reconcile_transport_results(None, equivalent_get) == "get-fallback"


def test_classification_fails_closed_on_rights_and_sensitivity() -> None:
    """A health label never grants payload eligibility or sensitivity clearance."""
    licensed = classify_dataset(_record("a"), scopes=("keyword",))
    unknown = classify_dataset(_record("b", licence=None), scopes=("group",))

    assert licensed["classification"] == "candidate-metadata-only"
    assert licensed["payload_eligible"] is False
    assert licensed["sensitivity"] == "decision-required"
    assert unknown["classification"] == "decision-required"


def test_deterministic_simulation_records_changed_withdrawn_and_unchanged() -> None:
    """Interrupted/repeated observations retain every state transition."""
    previous = [_record("same"), _record("changed"), _record("gone")]
    current = [_record("same"), _record("changed"), _record("new")]
    current[1]["metadata_modified"] = "2026-08-12T00:00:00Z"

    first = reconcile_rerun(previous, current)
    second = reconcile_rerun(previous, current)

    assert first == second
    assert first == {
        "changed": ["changed"],
        "new": ["new"],
        "unchanged": ["same"],
        "withdrawn": ["gone"],
    }
