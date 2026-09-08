from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from archive_govt_nz.domains.health_appropriations.repair_ledger import build_repair_ledger


def _row(status: str = "value_difference") -> dict[str, object]:
    return {
        "measure": "health_spending", "year": 1976, "status": status,
        "source_record_id": "health:1976", "source_object_sha256": "a" * 64,
        "source_coordinate": "Sheet1!A1", "source_value": "605.7", "donor_value": "605.70000000000005",
    }


def test_ledger_requires_explicit_disposition_and_never_replaces_value() -> None:
    ledger = build_repair_ledger([_row()], {("health_spending", 1976): "blocked"})
    assert ledger[0]["replacement_value"] is None
    assert ledger[0]["publication_approved"] is False
    schema = json.loads(Path("schemas/health-repair-ledger-v1.schema.json").read_text())
    jsonschema.validate(ledger[0], schema)


def test_ledger_rejects_missing_or_extra_disposition() -> None:
    with pytest.raises(ValueError, match="missing_disposition"):
        build_repair_ledger([_row()], {})
    with pytest.raises(ValueError, match="extra_disposition"):
        build_repair_ledger([_row()], {("health_spending", 1976): "blocked", ("nominal_gdp", 1976): "blocked"})


def test_ledger_rejects_unknown_disposition() -> None:
    with pytest.raises(ValueError, match="missing_disposition"):
        build_repair_ledger([_row("source_only")], {("health_spending", 1976): "repair"})
