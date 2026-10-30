"""Adversarial contracts for bounded legislation freshness discovery."""

# ruff: noqa: D103, PT011

from __future__ import annotations

import copy

import pytest
from hypothesis import given
from hypothesis import strategies as st
from tests.domains.test_legislation_accounting import accounting

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
        "legislation_types": ("act",),
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
    harvest = accounting().to_receipt()
    receipts = acquisition_receipts(candidate, harvest)
    accepted = receipts["accepted-pending-merge"]
    assert {row["work_id"] for row in accepted["works"]} == {"new", "changed"}
    assert accepted["canonical_state_changed"] is False
    assert accepted["admission_status"] == "pending_verified_state_merge"
    assert {
        row["work_id"]
        for row in receipts["rejected-duplicate-unavailable-partial-failed"]["rejected"]
    } == {"missing", "partial", "failed"}


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
            "accounting is incomplete",
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


def test_official_parameters_and_nested_title() -> None:
    """Subtype values and unsupported sort keys never reach the official API."""

    def fetch(params: dict[str, object]) -> dict[str, object]:
        assert params["legislation_type"] == "act"
        assert params["sort_by"] == "most_recently_updated"
        assert "sort" not in params
        return {
            "results": [
                {
                    "work_id": "act_public_1990_109",
                    "legislation_type": "act",
                    "latest_matching_version": {
                        "title": "New Zealand Bill of Rights Act 1990"
                    },
                }
            ]
        }

    receipt = discover(scope(), fetch)
    assert receipt["candidates"][0]["title"] == "New Zealand Bill of Rights Act 1990"
    for invalid in (scope(legislation_types=("public",)), scope(sort="work_id")):
        with pytest.raises(ValueError):
            invalid.validate()


def test_cap_resumes_inside_page_without_skipping_other_queries() -> None:
    """A candidate cap keeps the unconsumed offset and unvisited query intact."""
    selected = scope(
        page_size=3, max_pages=1, max_candidates=2, legislation_types=("act", "bill")
    )

    def fetch(params: dict[str, object]) -> dict[str, object]:
        prefix = params["legislation_type"]
        return {
            "results": [{"work_id": f"{prefix}_{i}"} for i in range(3)]
            if params["page"] == 1
            else []
        }

    first = discover(selected, fetch)
    assert first["continuations"][0]["offset"] == 2
    assert first["continuations"][1]["page"] == 1
    second = discover(selected, fetch, first)
    assert {r["work_id"] for r in second["candidates"]} == {"act_2", "bill_0"}
    third = discover(selected, fetch, second)
    assert {r["work_id"] for r in third["candidates"]} == {"bill_1", "bill_2"}
    final = discover(selected, fetch, third)
    assert final["queries_exhausted"] is True
    assert final["authoritative_completeness"] is False


def test_exhausted_first_query_does_not_hide_unfinished_second_query() -> None:
    """Short-page exhaustion belongs to that query, never to the entire scope."""
    receipt = discover(
        scope(legislation_types=("act", "bill")),
        lambda p: {
            "results": []
            if p["legislation_type"] == "act"
            else [{"work_id": "bill_1"}, {"work_id": "bill_2"}]
        },
    )
    assert receipt["continuations"][0]["exhausted"] is True
    assert receipt["continuations"][1]["page"] == 3
    assert receipt["queries_exhausted"] is False
    assert receipt["next_page"] is None


@pytest.mark.parametrize(
    "change",
    [
        {"page": 0},
        {"offset": -1},
        {"exhausted": "yes"},
        {"legislation_type": "private"},
    ],
)
def test_invalid_resume_cursor_fails_closed(change: dict[str, object]) -> None:
    receipt = discover(scope(), lambda _p: {"results": []})
    receipt["continuations"][0].update(change)
    with pytest.raises(ValueError, match="continuation"):
        discover(
            scope(),
            lambda _p: pytest.fail("no request before cursor validation"),
            receipt,
        )


def test_api_filter_and_page_contract_fail_closed() -> None:
    for payload in (
        {"results": [{"work_id": "bill_1", "legislation_type": "bill"}]},
        {"page": 2, "results": []},
        {"results": [None, None, None]},
    ):
        with pytest.raises(ValueError):
            discover(scope(), lambda _p, payload=payload: payload)


def test_ephemeral_and_split_bill_identifiers_are_retained() -> None:
    ids = [
        "bill_government_2022_96-B",
        "secondary-legislation_agency-drafted_~2026_~123",
    ]
    receipt = discover(
        scope(max_pages=1, max_candidates=2),
        lambda _p: {"results": [{"work_id": work} for work in ids]},
    )
    assert {r["work_id"] for r in receipt["candidates"]} == set(ids)
