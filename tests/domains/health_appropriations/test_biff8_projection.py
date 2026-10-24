"""Consumers must resolve numeric lineage against immutable source bytes."""

from __future__ import annotations

import hashlib
from copy import deepcopy
from decimal import Decimal
from typing import Any

import pyarrow as pa
import pytest
from tests.domains.health_appropriations.biff8_fixture import grid_fixture

from archive_govt_nz.domains.health_appropriations import (
    biff8_projection,
    biff8_records,
)


def _inputs() -> tuple[
    biff8_records.BiffSheet, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]
]:
    payload = grid_fixture((("Raw Data", (("Amount", "Year"), (42, 2019))),))
    sheet = biff8_records.read_sheet(
        payload, hashlib.sha256(payload).hexdigest(), sheet="Raw Data"
    )
    witnesses = [sheet.integer_cell(2, column).to_record() for column in (1, 2)]
    fact = {
        "record_id": "fictional:record",
        "lineage_id": "fictional:lineage",
        "source_object_sha256": sheet.source_sha256,
        "source_row": 2,
        "value_basis": "biff8_stored_integer/v1",
        "amount": Decimal("42.000"),
        "year": 2019,
        "canonical_stored_integer": "42",
        "numeric_evidence_id": witnesses[0]["numeric_evidence_id"],
    }
    lineage = [
        {
            "record_id": fact["record_id"],
            "lineage_id": fact["lineage_id"],
            "field": field,
            "source_object_sha256": sheet.source_sha256,
            "source_row": 2,
            "source_column": column,
            "numeric_evidence_id": witness["numeric_evidence_id"],
            "value_basis": fact["value_basis"],
            "raw_value": None,
            "normalized_value": str(fact[field]),
        }
        for field, column, witness in zip(
            ("amount", "year"), (1, 2), witnesses, strict=True
        )
    ]
    return sheet, fact, witnesses, lineage


def test_projection_replays_typed_numeric_evidence_and_carries_basis() -> None:
    sheet, fact, witnesses, lineage = _inputs()
    table = pa.Table.from_pylist(witnesses, schema=biff8_projection.NUMERIC_SCHEMA)
    result = biff8_projection.replay_projection(
        sheet, fact, table.to_pylist(), lineage, columns={"amount": 1, "year": 2}
    )
    assert [item.canonical_stored_integer for item in result] == [42, 2019]
    assert [item.numeric_evidence_id for item in result] == [
        w["numeric_evidence_id"] for w in witnesses
    ]
    assert all(item.value_basis == fact["value_basis"] for item in result)
    assert [item.source_coordinate for item in result] == [
        "'Raw Data'!A2",
        "'Raw Data'!B2",
    ]
    assert "source_number_token" not in table.column_names
    assert "source_number_token" not in fact


@pytest.mark.parametrize(
    "failure",
    [
        "unknown_basis",
        "literal_token",
        "amount",
        "dimension",
        "canonical",
        "fact_reference",
        "missing",
        "duplicate",
        "dangling",
        "wrong_cell",
        "raw_text",
        "source",
        "typed_alias",
    ],
)
def test_projection_refuses_unbound_or_fabricated_numeric_evidence(
    failure: str,
) -> None:
    sheet, fact, witnesses, lineage = _inputs()
    updates = {
        "unknown_basis": {"value_basis": "unqualified/v1"},
        "literal_token": {"source_number_token": str(42)},
        "amount": {"amount": Decimal(43)},
        "dimension": {"year": 2019.0},
        "canonical": {"canonical_stored_integer": "042"},
        "fact_reference": {"numeric_evidence_id": witnesses[1]["numeric_evidence_id"]},
        "source": {"source_object_sha256": "0" * 64},
    }
    if failure in updates:
        fact.update(updates[failure])
    elif failure == "missing":
        witnesses.pop()
    elif failure == "duplicate":
        witnesses.append(deepcopy(witnesses[0]))
    elif failure == "dangling":
        lineage[1]["numeric_evidence_id"] = "absent"
    elif failure == "wrong_cell":
        lineage[0]["source_column"] = 2
    elif failure == "raw_text":
        lineage[0]["raw_value"] = "42"
    elif failure == "typed_alias":
        witnesses[0]["source_column"] = True
    with pytest.raises(ValueError, match="invalid_biff8_numeric_projection"):
        biff8_projection.replay_projection(
            sheet, fact, witnesses, lineage, columns={"amount": 1, "year": 2}
        )
