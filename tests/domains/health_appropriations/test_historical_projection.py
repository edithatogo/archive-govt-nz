"""Pure canonical historical projection keeps exact values and provenance."""

from __future__ import annotations

import json
from datetime import UTC, date, datetime
from decimal import Decimal, localcontext
from io import BytesIO
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.domains.health_appropriations.historical import (
    _DISPOSITIONS,
    _SCHEMA,
)
from archive_govt_nz.domains.health_appropriations.historical_projection import (
    _amount,
    _id,
    project_historical,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA


def _inputs() -> dict[str, Any]:
    number_text = "12.34567890123456"
    fact = dict.fromkeys(_SCHEMA.names)
    fact.update(
        record_id="sha256:" + "a" * 64,
        schema_version="archive-govt-nz.health-historical-silver/v1",
        recordset="health_spending_fact",
        domain="health_appropriations",
        source_object_sha256="b" * 64,
        source_observation_id="sha256:" + "c" * 64,
        source_locator="https://example.test/history.xlsx",
        source_vintage="historical-2025",
        observed_at=datetime(2026, 8, 31, tzinfo=UTC),
        rights_state="not_evaluated",
        quality_flags=[
            "period_start_not_provided",
            "cross_basis_comparability_not_asserted",
        ],
        transformation_id="treasury-historical-health-gdp/v1",
        lineage_id="sha256:" + "d" * 64,
        year=2025,
        year_label="2025†",
        amount=Decimal("12.34567890123456"),
        source_number_token=number_text,
        source_number_format="0.0",
        period_end_month=6,
        accounting_basis="PBE Standards",
        valid_time_end=date(2025, 6, 30),
        unit="NZD_millions",
        measure="health_spending",
        footnotes=["Synthetic note"],
        raw_values_json="{}",
    )
    fact = pa.Table.from_pylist([fact], schema=_SCHEMA).to_pylist()[0]
    fields = [
        ("amount", "H5", fact["source_number_token"]),
        ("source_number_token", "H5", fact["source_number_token"]),
        ("source_number_format", "H5", "0.0"),
        ("year", "B5", "2025†"),
        ("year_label", "B5", "2025†"),
        ("period_end_month", "A5", "PBE Standards, June Years"),
        ("valid_time_end", "A5", "PBE Standards, June Years"),
        ("valid_time_end", "B5", "2025†"),
        ("unit", "A3", "$ millions"),
        ("measure", "H4", "Health"),
        ("accounting_basis", "A5", "PBE Standards, June Years"),
        ("footnotes", "A9", "Synthetic note"),
    ]
    lineage = [
        {
            "lineage_id": fact["lineage_id"],
            "record_id": fact["record_id"],
            "field": field,
            "source_object_sha256": fact["source_object_sha256"],
            "source_locator": fact["source_locator"],
            "source_coordinate": f"'Spending'!{coordinate}",
            "raw_value": raw,
            "normalized_value": str(fact[field]),
            "rule": fact["transformation_id"],
        }
        for field, coordinate, raw in fields
    ]
    dispositions = [
        {
            "source_object_sha256": fact["source_object_sha256"],
            "source_coordinate": coordinate,
            "raw_value_json": json.dumps(
                next(
                    r["raw_value"]
                    for r in lineage
                    if r["source_coordinate"] == coordinate
                    and r["field"] != "source_number_format"
                )
            ),
            "disposition": "normalized" if coordinate.endswith("H5") else "context",
            "reason": "literal_historical_observation"
            if coordinate.endswith("H5")
            else "historical_context",
            "record_id": fact["record_id"] if coordinate.endswith("H5") else None,
        }
        for coordinate in sorted({r["source_coordinate"] for r in lineage})
    ]
    manifest = {
        key: fact[key]
        for key in (
            "source_object_sha256",
            "source_locator",
            "source_vintage",
            "rights_state",
            "transformation_id",
        )
    }
    manifest.update(
        schema_version="archive-govt-nz.health-historical-extraction/v1",
        status="passed",
        observed_at=fact["observed_at"].isoformat(),
        counts={
            "facts": 1,
            "lineage": len(lineage),
            "dispositions": len(dispositions),
            "rejected": 0,
        },
    )
    return {
        "manifest": manifest,
        "manifest_sha256": "e" * 64,
        "facts": pa.Table.from_pylist([fact], schema=_SCHEMA),
        "lineage": pa.Table.from_pylist(lineage, schema=LINEAGE_SCHEMA),
        "dispositions": pa.Table.from_pylist(dispositions, schema=_DISPOSITIONS),
    }


def test_projection_preserves_amount_period_and_accounting() -> None:
    inputs = _inputs()
    result = project_historical(**inputs)
    fact = result.tables["health_spending_fact"].to_pylist()[0]
    assert fact["amount"] == Decimal("12.34567890123456")
    assert fact["valid_time_start"] is None
    assert fact["valid_time_end"] == date(2025, 6, 30)
    expected_period = "2025†"
    assert fact["period_token"] == expected_period
    assert fact["rights_state"] == "not_evaluated"
    assert fact["source_label"] == "Health"
    assert result.receipt["input_fixity"] == "not_performed"
    assert len(result.receipt["lineage_accounting"]) == inputs["lineage"].num_rows
    assert result == project_historical(**inputs)


def test_missing_period_dependency_fails() -> None:
    inputs = _inputs()
    rows = inputs["lineage"].to_pylist()
    rows = [
        row
        for row in rows
        if not (
            row["field"] == "valid_time_end" and row["source_coordinate"].endswith("B5")
        )
    ]
    inputs["lineage"] = pa.Table.from_pylist(rows, schema=LINEAGE_SCHEMA)
    inputs["manifest"]["counts"]["lineage"] = len(rows)
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


@pytest.mark.parametrize(
    "field",
    [
        "unit",
        "year",
        "year_label",
        "valid_time_end",
        "period_end_month",
        "accounting_basis",
        "source_number_format",
    ],
)
def test_inconsistent_raw_dependency_fails(field: str) -> None:
    inputs = _inputs()
    rows = inputs["lineage"].to_pylist()
    next(row for row in rows if row["field"] == field)["raw_value"] = (
        "wrong raw context"
    )
    inputs["lineage"] = pa.Table.from_pylist(rows, schema=LINEAGE_SCHEMA)
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


def test_unaccounted_normalized_cell_fails() -> None:
    inputs = _inputs()
    cells = inputs["dispositions"].to_pylist()
    duplicate = dict(next(row for row in cells if row["disposition"] == "normalized"))
    duplicate["source_coordinate"] = "'Spending'!H99"
    cells.append(duplicate)
    inputs["dispositions"] = pa.Table.from_pylist(cells, schema=_DISPOSITIONS)
    inputs["manifest"]["counts"]["dispositions"] = len(cells)
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


def _replace_fact(inputs: dict[str, Any], changes: dict[str, Any]) -> None:
    rows = inputs["facts"].to_pylist()
    rows[0].update(changes)
    inputs["facts"] = pa.Table.from_pylist(rows, schema=_SCHEMA)


def _reconcile_links(inputs: dict[str, Any], raw: dict[str, str] | None = None) -> None:
    fact = inputs["facts"].to_pylist()[0]
    rows = inputs["lineage"].to_pylist()
    for row in rows:
        row["normalized_value"] = str(fact[row["field"]])
        if raw and row["field"] in raw:
            row["raw_value"] = raw[row["field"]]
    inputs["lineage"] = pa.Table.from_pylist(rows, schema=LINEAGE_SCHEMA)
    cells = inputs["dispositions"].to_pylist()
    literals = {
        row["source_coordinate"]: row["raw_value"]
        for row in rows
        if row["field"] != "source_number_format"
    }
    for cell in cells:
        if cell["source_coordinate"] in literals:
            cell["raw_value_json"] = json.dumps(literals[cell["source_coordinate"]])
    inputs["dispositions"] = pa.Table.from_pylist(cells, schema=_DISPOSITIONS)


@pytest.mark.parametrize(
    "text",
    ["0", "-12.25", "99999999999999999999.99999999999999999", "1.0000000000000000000"],
)
def test_exact_values_ignore_ambient_decimal_context(text: str) -> None:
    inputs = _inputs()
    _replace_fact(inputs, {"amount": Decimal(text), "source_number_token": text})
    _reconcile_links(inputs, {"amount": text, "source_number_token": text})
    with localcontext() as context:
        context.prec = 2
        result = project_historical(**inputs)
    row = result.tables["health_spending_fact"].to_pylist()[0]
    assert row["amount"] == Decimal(text)
    assert row["value_token"] == text
    assert (row["source_decimal_precision"], row["source_decimal_scale"]) == (38, 17)


@pytest.mark.parametrize("text", ["100000000000000000000", "-100000000000000000000"])
def test_source_carrier_wider_than_canonical_fails(text: str) -> None:
    inputs = _inputs()
    _replace_fact(inputs, {"amount": Decimal(text), "source_number_token": text})
    _reconcile_links(inputs, {"amount": text, "source_number_token": text})
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (1, "1"),
        (1.0, "1"),
        (True, "1"),
        (None, "0"),
        (Decimal("NaN"), "NaN"),
        (Decimal("Infinity"), "Infinity"),
        (Decimal(1), None),
        (Decimal(1), ""),
        (Decimal(1), "1" * 129),
        (Decimal(1), "1e+"),
        (Decimal(1), "2"),
        (Decimal(0), "0e111"),
        (Decimal(0), "0e-147"),
        (Decimal("0.0000000000000000001"), "0.0000000000000000001"),
    ],
)
def test_amount_guard_rejects_unsupported_values(value: object, text: object) -> None:
    with pytest.raises(ValueError, match="historical_projection_contract"):
        _amount(value, text)


@pytest.mark.parametrize("text", ["0e110", "0e-146", "0.000000000000000001"])
def test_amount_guard_exact_boundaries(text: str) -> None:
    assert _amount(Decimal(text), text) == Decimal(text)


def test_full_vintage_and_manifest_identity_are_not_pooled() -> None:
    inputs = _inputs()
    original = project_historical(**inputs)
    inputs["manifest"]["source_vintage"] = "historical-2026"
    _replace_fact(inputs, {"source_vintage": "historical-2026"})
    changed = project_historical(**inputs)
    inputs["manifest_sha256"] = "f" * 64
    revised = project_historical(**inputs)
    sets = [
        {row["record_id"] for row in result.tables["health_spending_fact"].to_pylist()}
        for result in (original, changed, revised)
    ]
    assert len(set.union(*sets)) == 3
    assert _id("a\x1fb", "c") != _id("a", "b\x1fc")
    assert _id({"a": 1, "b": 2}) == _id({"b": 2, "a": 1})


@pytest.mark.parametrize("period_label", ["March Years", " March Years"])
def test_gdp_march_and_null_semantics(period_label: str) -> None:
    inputs = _inputs()
    _replace_fact(
        inputs,
        {
            "recordset": "fiscal_context_fact",
            "measure": "nominal_gdp",
            "accounting_basis": None,
            "period_end_month": 3,
            "valid_time_end": date(2025, 3, 31),
            "footnotes": [],
        },
    )
    rows = [
        row
        for row in inputs["lineage"].to_pylist()
        if row["field"] not in {"accounting_basis", "footnotes"}
    ]
    for row in rows:
        if row["source_coordinate"].endswith("A5"):
            row["raw_value"] = period_label
    inputs["lineage"] = pa.Table.from_pylist(rows, schema=LINEAGE_SCHEMA)
    inputs["manifest"]["counts"]["lineage"] = len(rows)
    _reconcile_links(inputs, {"measure": "Nominal GDP"})
    result = project_historical(**inputs)
    assert result.tables["health_spending_fact"].num_rows == 0
    row = result.tables["fiscal_context_fact"].to_pylist()[0]
    assert row["source_label"] == "Nominal GDP"
    for key in (
        "valid_time_start",
        "accounting_basis",
        "amount_type",
        "price_basis",
        "seasonal_adjustment",
        "base_period",
        "denominator_definition",
        "institutional_coverage",
        "null_reason",
    ):
        assert row[key] is None
    assert row["valid_time_status"] == "end_known_start_unknown"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("domain", "wrong"),
        ("schema_version", "wrong"),
        ("recordset", "appropriation_fact"),
        ("record_id", "wrong"),
        ("lineage_id", "wrong"),
        ("source_observation_id", None),
        ("source_object_sha256", "f" * 64),
        ("source_locator", "wrong"),
        ("source_vintage", "wrong"),
        ("rights_state", "eligible"),
        ("observed_at", None),
        ("transformation_id", "wrong"),
        ("measure", "wrong"),
        ("unit", "NZD_thousands"),
        ("amount_type", "Actual"),
        ("accounting_basis", "unknown"),
        ("valid_time_start", date(2024, 7, 1)),
        ("valid_time_end", date(2025, 3, 31)),
        ("period_end_month", 12),
        ("year", 0),
        ("year", 10000),
        ("year_label", "2025-26"),
        ("quality_flags", []),
        ("quality_flags", [None]),
        ("footnotes", [None]),
        ("source_number_token", "12.34"),
    ],
)
def test_fact_semantic_failures(field: str, value: object) -> None:
    inputs = _inputs()
    _replace_fact(inputs, {field: value})
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "wrong"),
        ("status", "failed"),
        ("rights_state", "eligible"),
        ("transformation_id", "wrong"),
        ("source_object_sha256", "wrong"),
        ("source_locator", ""),
        ("source_vintage", " "),
        ("observed_at", "2026-08-31"),
    ],
)
def test_manifest_semantic_failures(field: str, value: object) -> None:
    inputs = _inputs()
    inputs["manifest"][field] = value
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


@pytest.mark.parametrize("field", ["facts", "lineage", "dispositions", "rejected"])
@pytest.mark.parametrize("value", [True, -1])
def test_count_contracts(field: str, value: object) -> None:
    inputs = _inputs()
    inputs["manifest"]["counts"][field] = value
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


@pytest.mark.parametrize("table", ["facts", "lineage", "dispositions"])
def test_unknown_or_empty_table_schema_fails(table: str) -> None:
    inputs = _inputs()
    inputs[table] = pa.table({"wrong": ["shape"]})
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)
    inputs = _inputs()
    inputs[table] = inputs[table].slice(0, 0)
    inputs["manifest"]["counts"][table] = 0
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


def test_canonical_lineage_targets_and_normalized_values_close() -> None:
    inputs = _inputs()
    result = project_historical(**inputs)
    fact = result.tables["health_spending_fact"].to_pylist()[0]
    rows = result.tables["field_lineage"].to_pylist()
    assert len({row["record_id"] for row in rows}) == len(rows)
    for row in rows:
        assert row["target_record_id"] == fact["record_id"]
        assert row["lineage_id"] == fact["lineage_id"]
        assert row["normalized_value"] == str(fact[row["field"]])
        assert row["source_record_id"] == fact["source_record_id"]


def test_parquet_transport_child_names_are_explicitly_supported() -> None:
    inputs = _inputs()
    expected = project_historical(**inputs)
    for name in ("facts", "lineage", "dispositions"):
        payload = BytesIO()
        pq.write_table(inputs[name], payload)
        payload.seek(0)
        inputs[name] = pq.read_table(payload)
    assert (
        inputs["facts"].schema.field("quality_flags").type.value_field.name == "element"
    )
    assert project_historical(**inputs) == expected


@pytest.mark.parametrize("change", ["child_name", "child_nullable", "metadata"])
def test_unreviewed_transport_schema_drift_fails(change: str) -> None:
    inputs = _inputs()
    schema = inputs["facts"].schema
    position = schema.get_field_index("quality_flags")
    if change == "metadata":
        schema = schema.with_metadata({"unexpected": "metadata"})
    else:
        child = pa.field(
            "alien" if change == "child_name" else "element",
            pa.string(),
            nullable=change != "child_nullable",
        )
        schema = schema.set(position, schema.field(position).with_type(pa.list_(child)))
    inputs["facts"] = pa.Table.from_pylist(inputs["facts"].to_pylist(), schema=schema)
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("record_id", "sha256:" + "f" * 64),
        ("field", "unknown"),
        ("lineage_id", "sha256:" + "f" * 64),
        ("source_object_sha256", "f" * 64),
        ("source_locator", "other"),
        ("rule", "other"),
        ("source_coordinate", "unknown"),
        ("normalized_value", "different"),
    ],
)
def test_lineage_identity_or_join_drift_fails(field: str, value: str) -> None:
    inputs = _inputs()
    rows = inputs["lineage"].to_pylist()
    rows[0][field] = value
    inputs["lineage"] = pa.Table.from_pylist(rows, schema=LINEAGE_SCHEMA)
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


@pytest.mark.parametrize("table", ["facts", "lineage", "dispositions"])
def test_duplicate_source_rows_fail(table: str) -> None:
    inputs = _inputs()
    inputs[table] = pa.concat_tables([inputs[table], inputs[table].slice(0, 1)])
    inputs["manifest"]["counts"][table] += 1
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_object_sha256", "f" * 64),
        ("source_coordinate", ""),
        ("disposition", "unknown"),
        ("record_id", "sha256:" + "a" * 64),
    ],
)
def test_context_disposition_drift_fails(field: str, value: str) -> None:
    inputs = _inputs()
    rows = inputs["dispositions"].to_pylist()
    row = next(row for row in rows if row["disposition"] == "context")
    row[field] = value
    inputs["dispositions"] = pa.Table.from_pylist(rows, schema=_DISPOSITIONS)
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


def test_source_order_does_not_change_projection_or_mutate_inputs() -> None:
    inputs = _inputs()
    original = dict(inputs)
    expected = project_historical(**inputs)
    for name in ("facts", "lineage", "dispositions"):
        inputs[name] = inputs[name].take(list(reversed(range(inputs[name].num_rows))))
    assert project_historical(**inputs) == expected
    assert project_historical(**original) == expected


@pytest.mark.parametrize("pin", [None, 7, "A" * 64, "e" * 63, "sha256:" + "e" * 64])
def test_invalid_caller_manifest_identity_fails(pin: object) -> None:
    inputs = _inputs()
    inputs["manifest_sha256"] = pin
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


@given(st.integers(min_value=-(10**38 - 1), max_value=10**38 - 1))
def test_exact_decimal_representability_does_not_depend_on_context(
    coefficient: int,
) -> None:
    sign = "-" if coefficient < 0 else ""
    digits = str(abs(coefficient)).zfill(19)
    token = sign + digits[:-18] + "." + digits[-18:]
    expected = Decimal(token)
    with localcontext() as context:
        context.prec = 2
        assert _amount(expected, token) == expected


def test_semantic_duplicate_with_distinct_source_id_is_rejected() -> None:
    inputs = _inputs()
    rows = inputs["facts"].to_pylist()
    rows.append({**rows[0], "record_id": "sha256:" + "f" * 64})
    inputs["facts"] = pa.Table.from_pylist(rows, schema=_SCHEMA)
    inputs["manifest"]["counts"]["facts"] = len(rows)
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


def test_row_limit_rejects_input_without_constructing_large_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "archive_govt_nz.domains.health_appropriations.historical_projection._MAX_ROWS",
        1,
    )
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**_inputs())


@pytest.mark.parametrize("year", [1, 9999])
def test_exact_supported_year_boundaries(year: int) -> None:
    inputs = _inputs()
    _replace_fact(
        inputs,
        {"year": year, "year_label": str(year), "valid_time_end": date(year, 6, 30)},
    )
    _reconcile_links(inputs, {"year": str(year), "year_label": str(year)})
    rows = inputs["lineage"].to_pylist()
    for row in rows:
        if row["field"] == "valid_time_end" and row["source_coordinate"].endswith("B5"):
            row["raw_value"] = str(year)
    inputs["lineage"] = pa.Table.from_pylist(rows, schema=LINEAGE_SCHEMA)
    _reconcile_links(inputs)
    result = project_historical(**inputs)
    assert result.tables["health_spending_fact"]["valid_time_end"].to_pylist() == [
        date(year, 6, 30)
    ]


@pytest.mark.parametrize("coordinate", ["H5", "A5", "A3"])
def test_contradictory_disposition_literal_fails(coordinate: str) -> None:
    inputs = _inputs()
    rows = inputs["dispositions"].to_pylist()
    next(row for row in rows if row["source_coordinate"].endswith(coordinate))[
        "raw_value_json"
    ] = '"999"'
    inputs["dispositions"] = pa.Table.from_pylist(rows, schema=_DISPOSITIONS)
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("donor_table", "unexpected"),
        ("donor_row_number", 1),
        ("department", "unexpected"),
        ("appropriation_name", "unexpected"),
        ("functional_classification", "unexpected"),
        ("portfolio_name", "unexpected"),
    ],
)
def test_unknown_historical_profile_fields_are_not_silently_lost(
    field: str, value: object
) -> None:
    inputs = _inputs()
    _replace_fact(inputs, {field: value})
    with pytest.raises(ValueError, match="historical_projection_contract"):
        project_historical(**inputs)
