"""Explicit selections do not replace direct targets or qualify whole sources."""

import hashlib
import json
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations.direct_coverage import Pinned
from archive_govt_nz.domains.health_appropriations.expanded_coverage import (
    selection_report,
)


def pin(value: object) -> Pinned:
    payload = json.dumps(value, sort_keys=True).encode()
    return Pinned(payload, hashlib.sha256(payload).hexdigest())


def fixture() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    receipt = {
        "schema_version": "archive-govt-nz.health-budget-extraction/v1",
        "source_object_sha256": "a" * 64,
        "source_locator": "data/raw/b25.xlsx",
        "source_vintage": "Budget-2025",
        "status": "passed",
        "rights_state": "not_evaluated",
        "counts": {"normalized": 2, "rejected": 0},
        "output_sha256": {"facts.parquet": "b" * 64},
    }
    register = {
        "schema_version": "archive-govt-nz.health-coverage-selections/v1",
        "selections": [
            {
                "selection_id": "budget-summary-2025",
                "profile": "budget",
                "family": "budget",
                "vintage": "Budget-2025",
                "source_locator": "data/raw/b25.xlsx",
                "source_object_sha256": "a" * 64,
                "receipt_sha256": pin(receipt).sha256,
            }
        ],
    }
    completion = {
        "schema_version": "archive-govt-nz.health-raw-rebuild/v2",
        "status": "passed",
        "stages": {"budget": pin(receipt).sha256},
        "coverage": [
            {
                "stage": "budget",
                "manifest_sha256": pin(receipt).sha256,
                "source_object_sha256": "a" * 64,
                "source_locator": "data/raw/b25.xlsx",
                "facts": 2,
                "scope": "adapter_selection_not_whole_source_closure",
                "reason_counts": {"normalized": 2, "outside_selection": 3},
            }
        ],
    }
    return register, receipt, completion


def test_scoped_selection_and_missing_receipt() -> None:
    register, receipt, completion = fixture()
    report = selection_report(
        pin(register), {"budget-summary-2025": pin(receipt)}, pin(completion)
    )
    assert report["rows"][0]["selection_state"] == "receipt_reported_passed_selection"
    assert report["rows"][0]["record_count"] == 2
    assert report["rows"][0]["reason_counts"] == {
        "normalized": 2,
        "outside_selection": 3,
    }
    assert report["payload_verification"] == "not_performed"
    assert report["source_rights"] == report["gold_selection"] == "not_assessed"
    absent = selection_report(pin(register), {}, None)["rows"][0]
    assert absent["selection_state"] == "receipt_not_supplied"
    assert absent["implementation_state"] == "existing_profile"
    assert absent["record_count"] is None
    assert absent["receipt_counts"] is None
    assert absent["whole_source_qualification"] == "not_established"
    assert selection_report(pin(register), {}, None) == selection_report(
        pin(register), {}, None
    )


@pytest.mark.parametrize(
    "field",
    [
        "source_object_sha256",
        "source_locator",
        "source_vintage",
        "schema_version",
        "status",
        "rights_state",
    ],
)
def test_repinned_receipt_identity_contradiction(field: str) -> None:
    register, receipt, completion = fixture()
    receipt[field] = "wrong"
    register["selections"][0]["receipt_sha256"] = pin(receipt).sha256
    completion["stages"]["budget"] = pin(receipt).sha256
    completion["coverage"][0]["manifest_sha256"] = pin(receipt).sha256
    with pytest.raises(ValueError, match=r"^expanded_coverage_contract$"):
        selection_report(
            pin(register), {"budget-summary-2025": pin(receipt)}, pin(completion)
        )


@pytest.mark.parametrize(
    "fault",
    [
        "duplicate",
        "family",
        "profile",
        "orphan",
        "hash",
        "completion",
        "count",
        "bool",
        "coverage",
        "missing_completion",
    ],
)
def test_fail_closed(fault: str) -> None:
    register, receipt, completion = fixture()
    receipts = {"budget-summary-2025": pin(receipt)}
    if fault == "duplicate":
        register["selections"] *= 2
    elif fault in {"family", "profile"}:
        register["selections"][0][fault] = "unknown"
    elif fault == "orphan":
        receipts["other"] = pin(receipt)
    elif fault == "hash":
        receipts["budget-summary-2025"] = Pinned(b"{}", "a" * 64)
    elif fault == "completion":
        completion["stages"]["budget"] = "c" * 64
    elif fault in {"count", "bool"}:
        completion["coverage"][0]["facts"] = -1 if fault == "count" else True
    elif fault == "coverage":
        completion["coverage"] *= 2
    with pytest.raises(ValueError, match=r"^expanded_coverage_contract$"):
        selection_report(
            pin(register),
            receipts,
            None if fault == "missing_completion" else pin(completion),
        )


def test_chart_literal_is_not_packaged_or_whole_source() -> None:
    register, _, _ = fixture()
    row = register["selections"][0]
    row.update(profile="befu-chart", family="befu", vintage="BEFU-2025")
    receipt = {
        "schema_version": "befu-chart-literal-context/v1",
        "status": "raw_context_only",
        "rights_state": "not_evaluated",
        "records": [
            {
                "source_sha256": "a" * 64,
                "source_locator": row["source_locator"],
                "source_vintage": "BEFU-2025",
                "sheet": "Table 2.4",
                "coordinate": "C8",
            }
        ],
    }
    row["receipt_sha256"] = pin(receipt).sha256
    report = selection_report(pin(register), {row["selection_id"]: pin(receipt)}, None)
    assert report["rows"][0]["selection_state"] == "receipt_reported_raw_context_only"
    assert report["rows"][0]["reason_counts"] is None
    assert report["rows"][0]["record_count"] == 1
    receipt["records"] *= 2
    row["receipt_sha256"] = pin(receipt).sha256
    with pytest.raises(ValueError, match=r"^expanded_coverage_contract$"):
        selection_report(pin(register), {row["selection_id"]: pin(receipt)}, None)


@pytest.mark.parametrize("profile", ["befu-detail", "hyefu-detail", "crown"])
def test_literal_package_profile_is_bound(profile: str) -> None:
    register, receipt, completion = fixture()
    row = register["selections"][0]
    row.update(
        profile=profile,
        family={"befu-detail": "befu", "hyefu-detail": "hyefu", "crown": "fiscal"}[
            profile
        ],
    )
    receipt.update(
        schema_version="archive-govt-nz.health-literal-package/v1",
        profile=profile,
        counts={"facts": 2},
    )
    row["receipt_sha256"] = pin(receipt).sha256
    completion["stages"] = {profile: pin(receipt).sha256}
    completion["coverage"][0].update(stage=profile, manifest_sha256=pin(receipt).sha256)
    assert (
        selection_report(
            pin(register), {row["selection_id"]: pin(receipt)}, pin(completion)
        )["rows"][0]["record_count"]
        == 2
    )
    receipt["profile"] = "other"
    row["receipt_sha256"] = pin(receipt).sha256
    completion["stages"][profile] = pin(receipt).sha256
    completion["coverage"][0]["manifest_sha256"] = pin(receipt).sha256
    with pytest.raises(ValueError, match=r"^expanded_coverage_contract$"):
        selection_report(
            pin(register), {row["selection_id"]: pin(receipt)}, pin(completion)
        )


@pytest.mark.parametrize(
    "payload", [b"[]", b'{"a":1,"a":2}', b'{"a":NaN}', b"\xff", b"{}", b"{"]
)
def test_malformed_register_redacted(payload: bytes) -> None:
    with pytest.raises(ValueError, match=r"^expanded_coverage_contract$"):
        selection_report(Pinned(payload, hashlib.sha256(payload).hexdigest()), {}, None)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("facts", 3),
        ("scope", "whole_source"),
        ("source_locator", "other"),
        ("source_object_sha256", "b" * 64),
        ("reason_counts", {}),
        ("reason_counts", {"reason": True}),
        ("manifest_sha256", "b" * 64),
    ],
)
def test_completion_contradictions(field: str, value: object) -> None:
    register, receipt, completion = fixture()
    completion["coverage"][0][field] = value
    with pytest.raises(ValueError, match=r"^expanded_coverage_contract$"):
        selection_report(
            pin(register), {"budget-summary-2025": pin(receipt)}, pin(completion)
        )


def test_duplicate_selection_alias_rejected() -> None:
    register, _, _ = fixture()
    register["selections"].append(
        {**register["selections"][0], "selection_id": "alias"}
    )
    with pytest.raises(ValueError, match=r"^expanded_coverage_contract$"):
        selection_report(pin(register), {}, None)


def test_historical_uses_native_facts_count() -> None:
    register, receipt, completion = fixture()
    row = register["selections"][0]
    row.update(profile="historical", family="fiscal")
    receipt.update(
        schema_version="archive-govt-nz.health-historical-extraction/v1",
        counts={"facts": 2, "rejected": 0},
    )
    row["receipt_sha256"] = pin(receipt).sha256
    completion["stages"] = {"historical": pin(receipt).sha256}
    completion["coverage"][0].update(
        stage="historical", manifest_sha256=pin(receipt).sha256
    )
    assert (
        selection_report(
            pin(register), {row["selection_id"]: pin(receipt)}, pin(completion)
        )["rows"][0]["record_count"]
        == 2
    )


def test_preserved_only_is_not_selected_count() -> None:
    register, receipt, completion = fixture()
    receipt["counts"]["preserved_only"] = 100
    row = register["selections"][0]
    row["receipt_sha256"] = pin(receipt).sha256
    completion["stages"]["budget"] = pin(receipt).sha256
    completion["coverage"][0]["manifest_sha256"] = pin(receipt).sha256
    observed = selection_report(
        pin(register), {row["selection_id"]: pin(receipt)}, pin(completion)
    )["rows"][0]
    assert observed["record_count"] == 2
    assert observed["receipt_counts"]["preserved_only"] == 100
    assert observed["whole_source_qualification"] == "not_established"


def test_validly_repinned_receipt_cannot_replace_registered_bytes() -> None:
    register, receipt, completion = fixture()
    receipt["additional_metadata"] = "changed bytes, unchanged selected values"
    with pytest.raises(ValueError, match=r"^expanded_coverage_contract$"):
        selection_report(
            pin(register), {"budget-summary-2025": pin(receipt)}, pin(completion)
        )


def test_register_and_inputs_are_not_mutated() -> None:
    register, receipt, completion = fixture()
    before = json.dumps([register, receipt, completion], sort_keys=True)
    report = selection_report(
        pin(register), {"budget-summary-2025": pin(receipt)}, pin(completion)
    )
    report["rows"][0]["reason_counts"].clear()
    report["rows"][0]["receipt_counts"].clear()
    assert json.dumps([register, receipt, completion], sort_keys=True) == before


def test_register_payload_bound() -> None:
    payload = b" " * (4 * 1024 * 1024 + 1)
    with pytest.raises(ValueError, match=r"^expanded_coverage_contract$"):
        selection_report(Pinned(payload, hashlib.sha256(payload).hexdigest()), {}, None)
