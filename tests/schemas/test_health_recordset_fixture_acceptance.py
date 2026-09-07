"""Phase 3.1 fixture acceptance, including explicit semantic admission limits."""

import json
from copy import deepcopy
from datetime import UTC, date, datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
from typing import Any

import jsonschema
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz.schemas.health_recordset_json import recordset_json_schema
from archive_govt_nz.schemas.health_recordset_normalization import (
    normalize_json,
    normalize_rows,
    validate_table,
)
from archive_govt_nz.schemas.health_recordsets import RECORDSETS, recordset_schema

FIXTURE = Path(__file__).parents[1] / "fixtures/health-eight-recordsets-v1.json"
NAMES = (
    "source_inventory",
    "appropriation_fact",
    "health_spending_fact",
    "fiscal_context_fact",
    "pharmaceutical_budget_fact",
    "price_population_fact",
    "classification_dimension",
    "field_lineage",
)
FACTS = NAMES[1:6]


def rows_for(name: str) -> list[dict[str, Any]]:
    """Expand reviewed fixture fields independently of production schemas."""
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    base = {**fixture["common"], **fixture["recordsets"][name], "recordset": name}
    if name in FACTS:
        base = {**fixture["fact"], **base}
    return [
        {**deepcopy(base), **scenario, "record_id": f"fixture:{name}:{index}"}
        for index, scenario in enumerate(fixture["observations"])
    ]


def test_fixture_covers_exactly_the_planned_recordsets() -> None:
    """A schema addition or fixture omission requires explicit review."""
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert set(fixture["recordsets"]) == set(NAMES) == set(RECORDSETS)
    assert fixture["synthetic"] is True


@pytest.mark.parametrize("name", NAMES)
def test_all_fields_survive_json_arrow_parquet(name: str) -> None:
    """Compare every field to an independent typed oracle across both vintages."""
    rows = rows_for(name)
    before = deepcopy(rows)
    validator = jsonschema.Draft202012Validator(
        recordset_json_schema(name), format_checker=jsonschema.FormatChecker()
    )
    for row in rows:
        validator.validate(row)
    expected = deepcopy(rows)
    for row in expected:
        row["observed_at"] = datetime.fromisoformat(row["observed_at"]).astimezone(UTC)
        for key in ("valid_time_start", "valid_time_end"):
            row[key] = date.fromisoformat(row[key]) if row[key] else None
        if name in FACTS:
            row["amount"] = Decimal(row["amount"])
    table = normalize_json(name, json.dumps(rows).encode())
    assert table.to_pylist() == expected
    assert rows == before
    assert table.schema.equals(recordset_schema(name), check_metadata=True)
    outputs = []
    for _ in range(2):
        stream = BytesIO()
        pq.write_table(normalize_rows(name, rows), stream)
        outputs.append(stream.getvalue())
        stream.seek(0)
        restored = pq.read_table(stream)
        validate_table(name, restored)
        assert restored.equals(table, check_metadata=True)
        assert restored.to_pylist() == expected
    assert outputs[0] == outputs[1]
    reversed_table = normalize_rows(name, list(reversed(rows)))
    assert reversed_table.to_pylist() == list(reversed(expected))


@pytest.mark.parametrize("name", FACTS)
@pytest.mark.parametrize(
    "reason", ["source_blank", "not_applicable", "suppressed", "unparseable", "absent"]
)
def test_reason_coded_nulls_survive_all_formats(name: str, reason: str) -> None:
    """All planned missing-value categories stay distinct from numeric zero."""
    row = rows_for(name)[0]
    row.update(amount=None, null_reason=reason, value_token=None)
    table = normalize_json(name, json.dumps([row]).encode())
    stream = BytesIO()
    pq.write_table(table, stream)
    stream.seek(0)
    restored = pq.read_table(stream)
    validate_table(name, restored)
    assert restored["amount"].to_pylist() == [None]
    assert restored["null_reason"].to_pylist() == [reason]


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize(
    "field", ["schema_version", "record_id", "valid_time_end", "lineage_id"]
)
def test_invalid_context_rejected_at_admission_and_readback(
    name: str, field: str
) -> None:
    """Typed Arrow/Parquet cannot bypass local row validation."""
    row = rows_for(name)[0]
    value = {
        "schema_version": "v999",
        "record_id": " ",
        "valid_time_end": "2024-01-01",
        "lineage_id": None,
    }[field]
    bad = {**row, field: value}
    with pytest.raises(ValueError, match=r"^health_recordset_normalization$"):
        normalize_json(name, json.dumps([bad]).encode())
    table = normalize_rows(name, [row])
    arrow_value = date.fromisoformat(value) if field == "valid_time_end" else value
    column = table.schema.field(field)
    table = table.set_column(
        table.schema.get_field_index(field),
        column,
        pa.array([arrow_value], type=column.type),
    )
    with pytest.raises(ValueError, match=r"^health_recordset_normalization$"):
        validate_table(name, table)
    # Parquet itself rejects nulls in a required column; other invalid values
    # survive encoding and must be rejected by the existing readback boundary.
    if field != "lineage_id":
        stream = BytesIO()
        pq.write_table(table, stream)
        stream.seek(0)
        with pytest.raises(ValueError, match=r"^health_recordset_normalization$"):
            validate_table(name, pq.read_table(stream))


@pytest.mark.parametrize("name", FACTS)
@pytest.mark.parametrize(
    "changes",
    [
        {"amount": "1.2345"},
        {"amount": None},
        {"null_reason": "absent"},
        {"amount": "100000000000000000000"},
    ],
)
def test_money_contradictions_fail_for_each_fact(
    name: str, changes: dict[str, Any]
) -> None:
    """No fact family silently rounds or accepts unexplained missing amounts."""
    row = {**rows_for(name)[0], **changes}
    with pytest.raises(ValueError, match=r"^health_recordset_normalization$"):
        normalize_json(name, json.dumps([row]).encode())


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize(
    "changes",
    [
        {"record_id": "arbitrary-not-derived"},
        {"source_object_sha256": "not-a-bronze-hash"},
        {"lineage_id": "dangling-lineage"},
        {"rights_state": "unsupported-rights-claim"},
        {"valid_time_status": "not_established"},
    ],
)
def test_semantic_gaps_are_characterized_not_approved(
    name: str, changes: dict[str, Any]
) -> None:
    """Transport is permissive; approved adapters enforce source semantics."""
    row = {**rows_for(name)[0], **changes}
    table = normalize_rows(name, [row])
    validate_table(name, table)
    for key, value in changes.items():
        assert table[key].to_pylist() == [value]


@pytest.mark.parametrize("name", FACTS)
def test_unit_interpretation_is_not_inferred(name: str) -> None:
    """Unknown units and inconsistent price context are retained, not qualified."""
    row = rows_for(name)[0]
    row.update(
        unit=None, price_basis="real", base_period=None, denominator_definition=None
    )
    table = normalize_rows(name, [row])
    validate_table(name, table)
    assert table["unit"].to_pylist() == [None]
    assert table["base_period"].to_pylist() == [None]


@pytest.mark.parametrize("name", NAMES)
def test_duplicate_identity_and_unknown_version_fail(name: str) -> None:
    """Stable supplied IDs replay unchanged but collisions and versions fail."""
    row = rows_for(name)[0]
    with pytest.raises(ValueError, match=r"^health_recordset_normalization$"):
        normalize_rows(name, [row, deepcopy(row)])
    with pytest.raises(KeyError):
        normalize_json(name, json.dumps([row]).encode(), version="v999")


@pytest.mark.parametrize(
    ("name", "changes"),
    [
        ("appropriation_fact", {"classification_ids": ["dangling-classification"]}),
        (
            "classification_dimension",
            {"mapping_state": "mapped", "mapping_evidence": None},
        ),
        (
            "field_lineage",
            {"target_record_id": "missing-target", "source_coordinate": "missing-cell"},
        ),
    ],
)
def test_cross_record_semantics_remain_unverified(
    name: str, changes: dict[str, Any]
) -> None:
    """Transport accepts unproved mappings and broken lineage targets."""
    row = {**rows_for(name)[0], **changes}
    table = normalize_rows(name, [row])
    validate_table(name, table)
    for key, value in changes.items():
        assert table[key].to_pylist() == [value]
