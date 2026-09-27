"""Focused contracts for Health Phase 4 repair decisions."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from archive_govt_nz.domains.health_appropriations.repair_ledger import (
    build_repair_ledger,
)


def _row(status: str = "value_difference") -> dict[str, object]:
    return {
        "measure": "health_spending",
        "year": 1976,
        "status": status,
        "reason": "source_numeric_value_differs_from_donor"
        if status == "value_difference"
        else "donor_year_absent_from_source"
        if status == "donor_only"
        else "source_year_absent_from_donor"
        if status == "source_only"
        else "exact_numeric_match",
        "source_record_id": "health:1976",
        "source_object_sha256": "a" * 64,
        "source_coordinate": "Sheet1!A1",
        "source_value": "605.7",
        "donor_value": "605.70000000000005",
    }


def test_ledger_requires_explicit_disposition_and_never_replaces_value() -> None:
    ledger = build_repair_ledger([_row()], {("health_spending", 1976): "blocked"})
    assert ledger[0]["replacement_value"] is None
    assert ledger[0]["publication_approved"] is False
    assert ledger[0]["rationale"] == "source_numeric_value_differs_from_donor"
    assert ledger[0]["source_coordinate"] == "Sheet1!A1"
    schema = json.loads(Path("schemas/health-repair-ledger-v1.schema.json").read_text())
    jsonschema.validate(ledger[0], schema)


def test_ledger_rejects_missing_or_extra_disposition() -> None:
    with pytest.raises(ValueError, match="missing_disposition"):
        build_repair_ledger([_row()], {})
    with pytest.raises(ValueError, match="extra_disposition"):
        build_repair_ledger(
            [_row()],
            {("health_spending", 1976): "blocked", ("nominal_gdp", 1976): "blocked"},
        )


def test_ledger_rejects_unknown_disposition() -> None:
    with pytest.raises(ValueError, match="missing_disposition"):
        build_repair_ledger(
            [_row("source_only")], {("health_spending", 1976): "repair"}
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"measure": "other"},
        {"measure": None},
        {"year": True},
        {"year": "1976"},
    ],
)
def test_ledger_rejects_malformed_keys(changes: dict[str, object]) -> None:
    row = _row()
    row.update(changes)
    with pytest.raises(ValueError, match="repair_ledger_key"):
        build_repair_ledger([row], {("health_spending", 1976): "blocked"})


def test_ledger_rejects_unknown_status_and_duplicate_key() -> None:
    with pytest.raises(ValueError, match="duplicate_or_status"):
        build_repair_ledger([_row("unknown")], {("health_spending", 1976): "blocked"})
    with pytest.raises(ValueError, match="duplicate_or_status"):
        build_repair_ledger([_row(), _row()], {("health_spending", 1976): "blocked"})


@pytest.mark.parametrize("disposition", ["accepted", "unsupported"])
def test_ledger_preserves_explicit_non_blocked_dispositions(
    disposition: str,
) -> None:
    ledger = build_repair_ledger(
        [_row("exact_match")], {("health_spending", 1976): disposition}
    )
    assert ledger[0]["disposition"] == disposition


@pytest.mark.parametrize(
    ("status", "field", "value"),
    [
        ("value_difference", "source_coordinate", None),
        ("source_only", "source_coordinate", ""),
        ("value_difference", "reason", None),
        ("donor_only", "reason", ""),
    ],
)
def test_deviations_require_coordinate_and_rationale(
    status: str, field: str, value: object
) -> None:
    row = _row(status)
    row[field] = value
    with pytest.raises(ValueError, match="repair_ledger_missing_evidence"):
        build_repair_ledger([row], {("health_spending", 1976): "blocked"})


def test_donor_only_deviation_records_rationale_with_null_source_coordinate() -> None:
    row = _row("donor_only")
    row["source_record_id"] = None
    row["source_object_sha256"] = None
    row["source_coordinate"] = None
    row["source_value"] = None
    ledger = build_repair_ledger([row], {("health_spending", 1976): "blocked"})
    assert ledger[0]["rationale"] == "donor_year_absent_from_source"
    assert ledger[0]["source_coordinate"] is None
    schema = json.loads(Path("schemas/health-repair-ledger-v1.schema.json").read_text())
    jsonschema.validate(ledger[0], schema)
