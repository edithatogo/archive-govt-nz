"""Pinned metadata joins never turn extraction receipts into source approval."""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.domains.health_appropriations import direct_coverage
from archive_govt_nz.domains.health_appropriations.direct_coverage import (
    Pinned,
    coverage_report,
)


def pin(value: object) -> Pinned:
    payload = json.dumps(value).encode()
    return Pinned(payload, hashlib.sha256(payload).hexdigest())


def inputs() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    target = {
        "schema_version": "archive-govt-nz.health-direct-targets/v1",
        "cutoff": "2026-08-29",
        "targets": [
            {
                "target_id": "budget-2026-expenditure",
                "family": "budget",
                "vintage": "Budget-2026",
                "source_id": "budget_2026-000",
                "url": "https://example.govt.nz/budget.xlsx",
                "discovery_state": "discovered",
            }
        ],
    }
    capture = {
        "schema_version": "archive-govt-nz.health-capture-manifest/v1",
        "cutoff": "2026-08-29",
        "results": [
            {
                "source_id": "budget_2026-000",
                "url": "https://example.govt.nz/budget.xlsx",
                "state": "captured",
                "sha256": "a" * 64,
                "object_id": "sha256:" + "a" * 64,
                "bytes": 10,
                "rights": {
                    "state": "eligible",
                    "license": "CC-BY-4.0",
                    "evidence": "https://example.govt.nz/rights",
                },
            }
        ],
    }
    extraction = {
        "schema_version": "archive-govt-nz.health-budget-extraction/v1",
        "source_object_sha256": "a" * 64,
        "source_locator": "https://example.govt.nz/budget.xlsx",
        "source_vintage": "Budget-2026",
        "status": "passed",
        "rights_state": "not_evaluated",
        "counts": {"normalized": 2, "rejected": 0},
        "output_sha256": {"budget_facts.parquet": "b" * 64},
    }
    return target, capture, extraction


def test_independent_states_and_missing_evidence() -> None:
    target, capture, extraction = inputs()
    receipt = coverage_report(
        pin(target), pin(capture), {"budget-2026-expenditure": pin(extraction)}
    )
    row = receipt["rows"][0]
    assert row["discovery_state"] == "discovered"
    assert row["capture_state"] == "captured"
    assert row["capture_rights"]["state"] == "eligible"
    assert row["extraction_state"] == "passed"
    assert row["extraction_rights_state"] == "not_evaluated"
    assert row["counts"] == {"normalized": 2, "rejected": 0}
    assert receipt["payload_verification"] == "not_performed"
    absent = coverage_report(pin(target), pin({**capture, "results": []}), {})["rows"][
        0
    ]
    assert absent["capture_state"] is None
    assert absent["extraction_state"] is None
    assert absent["capture_rights"] is None
    assert absent["gaps"] == [
        "capture_receipt_not_supplied",
        "extraction_receipt_not_supplied",
    ]


@pytest.mark.parametrize(
    "fault",
    [
        "hash",
        "url",
        "vintage",
        "schema",
        "passed_rejected",
        "negative_count",
        "bool_count",
        "duplicate_target",
        "duplicate_capture",
        "orphan",
        "uncaptured",
        "excluded_family",
    ],
)
def test_contradictions_fail_closed(fault: str) -> None:
    target, capture, extraction = inputs()
    receipts = {"budget-2026-expenditure": pin(extraction)}
    replacements = {
        "hash": (extraction, "source_object_sha256", "c" * 64),
        "vintage": (extraction, "source_vintage", "Budget-2025"),
        "schema": (extraction, "schema_version", "other/v1"),
        "passed_rejected": (extraction["counts"], "rejected", 1),
        "negative_count": (extraction["counts"], "normalized", -1),
        "bool_count": (extraction["counts"], "normalized", True),
    }
    if fault in replacements:
        row, key, value = replacements[fault]
        row[key] = value
    elif fault == "url":
        capture["results"][0]["url"] += "?changed"
    elif fault == "duplicate_target":
        target["targets"] *= 2
    elif fault == "duplicate_capture":
        capture["results"] *= 2
    elif fault == "orphan":
        receipts["unknown"] = pin(extraction)
    elif fault == "uncaptured":
        capture["results"] = []
    else:
        target["targets"][0]["family"] = "cpi"
    receipts["budget-2026-expenditure"] = pin(extraction)
    with pytest.raises(ValueError, match="direct_coverage_contract"):
        coverage_report(pin(target), pin(capture), receipts)


@pytest.mark.parametrize(
    "state",
    [
        "unavailable",
        "withdrawn",
        "restricted",
        "corrupt",
        "retryable",
        "superseded",
        "out_of_scope",
    ],
)
def test_no_object_states_are_not_invented(state: str) -> None:
    target, capture, _ = inputs()
    row = capture["results"][0]
    row["state"] = state
    for key in ("sha256", "object_id", "bytes", "rights"):
        del row[key]
    target["targets"][0]["vintage"] = None
    result = coverage_report(pin(target), pin(capture), {})["rows"][0]
    assert result["capture_state"] == state
    assert result["source_object_sha256"] is None
    assert result["vintage"] is None
    assert result["capture_rights"] is None
    assert result["extraction_state"] is None


def test_restriction_does_not_erase_retained_extraction() -> None:
    target, capture, extraction = inputs()
    capture["results"][0]["state"] = "restricted"
    capture["results"][0]["rights"] = {"state": "restricted", "license": None}
    extraction["status"] = "partial"
    extraction["counts"]["rejected"] = 1
    result = coverage_report(
        pin(target), pin(capture), {"budget-2026-expenditure": pin(extraction)}
    )["rows"][0]
    assert result["capture_state"] == "restricted"
    assert result["capture_rights"] == {"state": "restricted", "license": None}
    assert result["extraction_state"] == "partial"
    assert result["extraction_rights_state"] == "not_evaluated"
    assert result["counts"]["rejected"] == 1


@pytest.mark.parametrize(
    "payload",
    [
        b"{}",
        b"[]",
        b"null",
        b"{",
        b"\xff",
        b'{"targets":[],"targets":[]}',
        b'{"schema_version":NaN}',
    ],
)
def test_malformed_metadata_redacted(payload: bytes) -> None:
    _, capture, _ = inputs()
    with pytest.raises(ValueError, match=r"^direct_coverage_contract$"):
        coverage_report(
            Pinned(payload, hashlib.sha256(payload).hexdigest()), pin(capture), {}
        )


def test_pins_and_payload_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    target, capture, _ = inputs()
    item = pin(target)
    with pytest.raises(ValueError, match="direct_coverage_contract"):
        coverage_report(Pinned(item.payload, "0" * 64), pin(capture), {})
    largest = max(len(item.payload), len(pin(capture).payload))
    monkeypatch.setattr(direct_coverage, "MAX_BYTES", largest)
    assert coverage_report(item, pin(capture), {})["rows"]
    monkeypatch.setattr(direct_coverage, "MAX_BYTES", largest - 1)
    with pytest.raises(ValueError, match="direct_coverage_contract"):
        coverage_report(item, pin(capture), {})


@given(st.permutations(["a", "b", "c"]))
def test_target_order_and_missing_vintages(order: list[str]) -> None:
    target, capture, _ = inputs()
    template = target["targets"][0]
    target["targets"] = [
        {**template, "target_id": key, "source_id": key, "vintage": None}
        for key in order
    ]
    capture["results"] = []
    result = coverage_report(pin(target), pin(capture), {})
    assert [row["target_id"] for row in result["rows"]] == ["a", "b", "c"]
    assert all(
        row["vintage"] is None and row["capture_state"] is None
        for row in result["rows"]
    )
    assert result["target_register_sha256"] == pin(target).sha256
    assert result["capture_manifest_sha256"] == pin(capture).sha256
    assert result["scope"] == "explicit_targets_only"
    assert (
        result["normalization_approval"]
        == result["publication_approval"]
        == "not_granted"
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("sha256", "x" * 64),
        ("object_id", "sha256:wrong"),
        ("bytes", 0),
        ("bytes", True),
        ("state", "invented"),
        ("rights", []),
        ("source_id", ""),
        ("source_id", "bad\n"),
    ],
)
def test_bad_capture_fields(key: str, value: object) -> None:
    target, capture, _ = inputs()
    capture["results"][0][key] = value
    with pytest.raises(ValueError, match="direct_coverage_contract"):
        coverage_report(pin(target), pin(capture), {})


def test_aggregate_limits(monkeypatch: pytest.MonkeyPatch) -> None:
    target, capture, _ = inputs()
    total = len(pin(target).payload) + len(pin(capture).payload)
    monkeypatch.setattr(direct_coverage, "MAX_TOTAL_BYTES", total)
    assert coverage_report(pin(target), pin(capture), {})["rows"]
    monkeypatch.setattr(direct_coverage, "MAX_TOTAL_BYTES", total - 1)
    with pytest.raises(ValueError, match="direct_coverage_contract"):
        coverage_report(pin(target), pin(capture), {})


@pytest.mark.parametrize(
    "fault",
    [
        "object_without_hash",
        "cutoff",
        "nonfinite_rights",
        "row_cap",
        "extraction_cap",
        "wrong_locator",
        "bad_output_pin",
        "unsupported_vote",
        "null_vintage",
    ],
)
def test_review_boundaries(fault: str, monkeypatch: pytest.MonkeyPatch) -> None:
    target, capture, extraction = inputs()
    receipts = {"budget-2026-expenditure": pin(extraction)}
    if fault == "object_without_hash":
        capture["results"][0]["sha256"] = None
    elif fault == "cutoff":
        target["cutoff"] = capture["cutoff"] = "yesterday"
    elif fault == "nonfinite_rights":
        capture["results"][0]["rights"]["extra"] = float("nan")
    elif fault in {"row_cap", "extraction_cap"}:
        monkeypatch.setattr(direct_coverage, "MAX_ROWS", 0)
        if fault == "row_cap":
            receipts = {}
    elif fault == "wrong_locator":
        extraction["source_locator"] = "other"
    elif fault == "bad_output_pin":
        extraction["output_sha256"] = {"facts": "bad"}
    elif fault == "unsupported_vote":
        target["targets"][0]["family"] = "vote_health"
    else:
        target["targets"][0]["vintage"] = None
    if receipts:
        receipts["budget-2026-expenditure"] = pin(extraction)
    with pytest.raises(ValueError, match="direct_coverage_contract"):
        coverage_report(pin(target), pin(capture), receipts)


@pytest.mark.parametrize(
    "family", ["budget", "befu", "hyefu", "fiscal", "ministry", "pharmac"]
)
def test_explicit_family_schema_and_failed_state(family: str) -> None:
    target, capture, extraction = inputs()
    target["targets"][0]["family"] = family
    extraction["schema_version"] = direct_coverage.PROFILES[family]
    extraction["status"] = "failed"
    result = coverage_report(
        pin(target), pin(capture), {"budget-2026-expenditure": pin(extraction)}
    )
    assert result["rows"][0]["extraction_state"] == "failed"
    assert result["rows"][0]["extraction_manifest_sha256"] == pin(extraction).sha256


def test_retained_scope_and_decision_packet_remain_explicit() -> None:
    track = (
        Path(__file__).resolve().parents[3]
        / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
    )
    evidence = track / "direct-coverage-20260907"
    target = json.loads((evidence / "targets.json").read_bytes())
    census = {
        r["source_id"]: r
        for r in json.loads((track / "source-census.json").read_bytes())["records"]
    }
    assert len(target["targets"]) == 11
    for row in target["targets"]:
        assert row["url"] == census[row["source_id"]]["url"]
        assert row["family"] not in {"cpi", "qes", "classification"}
    report = json.loads((evidence / "retained-report.json").read_bytes())
    assert (
        report["target_register_sha256"]
        == hashlib.sha256((evidence / "targets.json").read_bytes()).hexdigest()
    )
    assert {r["target_id"] for r in report["rows"]} == {
        r["target_id"] for r in target["targets"]
    }
    assert sum(r["extraction_state"] == "passed" for r in report["rows"]) == 7
    assert sum(r["extraction_state"] is None for r in report["rows"]) == 4
    packet = json.loads((evidence / "repair-decision.json").read_bytes())
    assert packet["approval"] == "pending_human_decision"
    assert {r["year"] for r in packet["rows"] if r["status"] == "source_only"} == set(
        range(1987, 1997)
    ) | set(range(2001, 2020))
    differences = [r for r in packet["rows"] if r["status"] == "value_difference"]
    assert len(differences) == 1
    assert (
        differences[0]["year"],
        differences[0]["source_coordinate"],
        differences[0]["source_value"],
        differences[0]["donor_value"],
    ) == (1976, "'Spending'!H9", "605.70000000000005000", "605.7")
    prior = json.loads((track / "donor-parity-observed-20260907.json").read_bytes())
    assert {r["source_record_id"] for r in packet["rows"]} == {
        r["source_record_id"] for r in prior["exact_decimal_deviations"]
    }
    prior_rows = {r["source_record_id"]: r for r in prior["exact_decimal_deviations"]}
    for row in packet["rows"]:
        previous = prior_rows[row["source_record_id"]]
        for field in (
            "source_coordinate",
            "source_object_sha256",
            "reason",
            "status",
            "resolution",
        ):
            assert row[field] == previous[field]
        for field in ("source_value", "donor_value"):
            assert (
                hashlib.sha256(str(row[field]).encode()).hexdigest()
                == previous[field + "_sha256"]
            )
