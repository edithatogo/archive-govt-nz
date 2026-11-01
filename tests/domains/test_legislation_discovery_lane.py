"""Adversarial contracts for bounded legislation freshness discovery."""

# ruff: noqa: D103, PT011

from __future__ import annotations

import copy

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.domains.legislation.discovery_lane import (
    DiscoveryScope,
    acquisition_receipts,
    assert_same_query,
    discover,
)


def scope(**overrides: object) -> DiscoveryScope:
    values = {
        "scope_id": "freshness-001",
        "terms": ("amendment 2026",),
        "legislation_types": ("public",),
        "page_size": 2,
        "max_pages": 2,
        "max_candidates": 4,
    }
    values.update(overrides)
    return DiscoveryScope(**values)  # type: ignore[arg-type]


def test_pagination_deduplicates_rejects_and_resumes() -> None:
    pages = {
        1: {"results": [{"work_id": "act_2"}, {"work_id": "act_1"}]},
        2: {"results": [{"work_id": "act_1"}, {"work_id": "!"}]},
    }
    receipt = discover(scope(), lambda params: pages[params["page"]])
    assert [row["work_id"] for row in receipt["candidates"]] == ["act_1", "act_2"]
    assert receipt["duplicates"] == [{"work_id": "act_1", "page": 2}]
    assert receipt["rejected"][0]["reason"] == "malformed_work_id"
    assert receipt["next_page"] == 3
    assert receipt["authoritative_completeness"] is False
    assert receipt["custody_or_acquisition_proven"] is False


def test_non_object_result_is_recorded() -> None:
    """Keep a bounded rejection instead of dropping malformed rows silently."""
    receipt = discover(scope(), lambda _params: {"results": [None]})
    assert receipt["rejected"][0]["reason"] == "not_object"


@pytest.mark.parametrize("payload", [[], {}, {"results": None}, {"results": "x"}])
def test_partial_or_malformed_page_fails_closed(payload: object) -> None:
    with pytest.raises(ValueError, match="partial or malformed"):
        discover(scope(), lambda _params: payload)


@pytest.mark.parametrize("terms", [("Act",), ("Bill", "Regulation")])
def test_generic_terms_cannot_imply_coverage(terms: tuple[str, ...]) -> None:
    with pytest.raises(ValueError, match="generic terms"):
        scope(terms=terms).validate()


@given(st.permutations(["act_1", "act_2", "act_3"]))
def test_candidate_inventory_is_order_independent(ids: list[str]) -> None:
    def fetch(_params: object) -> dict[str, object]:
        return {"results": [{"work_id": value} for value in ids]}

    receipt = discover(scope(page_size=3, max_pages=1, max_candidates=3), fetch)
    assert [row["work_id"] for row in receipt["candidates"]] == sorted(ids)


def test_query_drift_requires_versioning() -> None:
    first = discover(scope(), lambda _params: {"results": []})
    same = copy.deepcopy(first)
    assert_same_query(first, same)
    changed = discover(scope(start_page=2), lambda _params: {"results": []})
    with pytest.raises(ValueError, match="query drift"):
        assert_same_query(first, changed)


def test_acquisition_outcomes_remain_pending_merge() -> None:
    candidate = discover(scope(), lambda _params: {"results": []})
    harvest = {
        "schema_version": "archive-govt-nz.legislation-harvest-receipt/v3",
        "accounting": {
            "works": [
                {"work_id": "act_1", "disposition": "newly_preserved"},
                {"work_id": "act_2", "disposition": "failed"},
                {"work_id": "act_3", "disposition": "already_processed_skipped"},
            ]
        },
    }
    receipts = acquisition_receipts(candidate, harvest)
    accepted = receipts["accepted-pending-merge"]
    assert accepted["canonical_state_changed"] is False
    assert accepted["admission_status"] == "pending_verified_state_merge"
    assert (
        receipts["rejected-duplicate-unavailable-partial-failed"]["rejected"][0][
            "work_id"
        ]
        == "act_2"
    )


@pytest.mark.parametrize(
    ("candidate", "harvest", "message"),
    [
        ({}, {}, "invalid candidate"),
        (
            {"schema_version": "archive-govt-nz.legislation-discovery-query/v1"},
            {},
            "requires a v3",
        ),
        (
            {"schema_version": "archive-govt-nz.legislation-discovery-query/v1"},
            {"schema_version": "archive-govt-nz.legislation-harvest-receipt/v3"},
            "accounting is incomplete",
        ),
        (
            {
                "schema_version": "archive-govt-nz.legislation-discovery-query/v1",
                "query": {"scope_id": "freshness-001"},
            },
            {
                "schema_version": "archive-govt-nz.legislation-harvest-receipt/v3",
                "accounting": {"works": [{"disposition": "invented"}]},
            },
            "disposition is malformed",
        ),
    ],
)
def test_acquisition_receipts_reject_malformed_inputs(
    candidate: dict[str, object], harvest: dict[str, object], message: str
) -> None:
    """Refuse weak or invented acquisition accounting."""
    with pytest.raises(ValueError, match=message):
        acquisition_receipts(candidate, harvest)


def test_bounds_and_concurrency_inputs_fail_closed() -> None:
    for invalid in (
        scope(page_size=0),
        scope(max_pages=0),
        scope(max_candidates=5),
        scope(start_page=0),
        scope(sort="title"),
        scope(endpoint="https://example.invalid/"),
        scope(terms=("specific", "specific")),
        scope(legislation_types=()),
        scope(scope_id="!"),
        scope(terms=("",)),
    ):
        with pytest.raises(ValueError):
            invalid.validate()
