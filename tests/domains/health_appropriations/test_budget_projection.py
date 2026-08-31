"""Canonical appropriation fields preserve the reviewed extraction boundary."""

from __future__ import annotations

import json
from copy import deepcopy
from decimal import Decimal, getcontext, localcontext
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest
from tests.domains.health_appropriations.test_budget_classification import inputs

from archive_govt_nz.domains.health_appropriations.budget_classification import (
    project_budget_classification,
)
from archive_govt_nz.domains.health_appropriations.budget_projection import (
    RULE,
    _amount,
    project_budget_appropriations,
)
from archive_govt_nz.domains.health_appropriations.silver import SILVER_SCHEMA
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def test_source_facts_and_unmapped_occurrences_are_retained(tmp_path: Path) -> None:
    source = inputs(tmp_path)
    result = project_budget_appropriations(**source)
    assert result.tables["appropriation_fact"].num_rows == 2
    assert result.tables["classification_dimension"].num_rows == 2
    assert result.receipt["input_fixity"] == "not_performed"
    assert result.receipt["publication_approval"] == "not_granted"


def test_fields_lineage_and_complete_source_accounting(tmp_path: Path) -> None:
    source = inputs(tmp_path)
    parent = project_budget_classification(**source)
    result = project_budget_appropriations(**source)
    assert set(result.tables) == {
        "appropriation_fact",
        "classification_dimension",
        "field_lineage",
    }
    assert result.tables["classification_dimension"].equals(
        parent.tables["classification_dimension"]
    )
    rows = result.tables["appropriation_fact"].to_pylist()
    dimensions = {
        row["source_record_id"]: row
        for row in result.tables["classification_dimension"].to_pylist()
    }
    for table_name, table in result.tables.items():
        assert table.schema.equals(recordset_schema(table_name), check_metadata=True)
        assert len({row["record_id"] for row in table.to_pylist()}) == table.num_rows
    for row in rows:
        assert row["recordset"] == "appropriation_fact"
        assert row["domain"] == "health_appropriations"
        assert (
            row["source_schema_version"]
            == "archive-govt-nz.health-appropriations-silver/v1"
        )
        assert row["transformation_id"] == RULE
        assert row["amount"] == Decimal("123.000000000000000000")
        assert row["value_token"] == "123"  # noqa: S105 - source numeric text.
        assert row["source_decimal_precision"] == 20
        assert row["source_decimal_scale"] == 3
        assert row["vote"] == row["department"] == row["portfolio"] == "Health"
        assert row["appropriation"] == row["source_label"] == "Care"
        assert row["unit"] == "NZD_thousands"
        assert row["measure"] == "appropriation_amount"
        assert row["amount_type"] == "Main Estimates"
        assert row["period_token"] == "2025"  # noqa: S105 - source year text.
        assert row["classification_ids"] == [
            dimensions[row["source_record_id"]]["record_id"]
        ]
        assert row["valid_time_status"] == "not_established"
        assert row["observation_context"] == "caller_supplied_extraction_observation"
        assert row["quality_flags"] == [
            "financial_year_basis_unverified",
            "value_token_from_extraction_lineage",
            "source_classification_label_unmapped",
            "unit_inherited_from_source_adapter",
            "currency_not_independently_established",
        ]
        assert row["rights_state"] == "not_evaluated"
        assert all(
            row[name] is None
            for name in (
                "valid_time_start",
                "valid_time_end",
                "currency",
                "price_basis",
                "base_period",
                "denominator_definition",
                "null_reason",
            )
        )
    links = result.tables["field_lineage"].to_pylist()
    assert len(links) == 22
    indexed = {row["record_id"]: row for row in rows}
    for link in links:
        if link["rule"] == RULE:
            target = indexed[link["target_record_id"]]
            value = target[link["field"]]
            expected = (
                json.dumps(value, ensure_ascii=False)
                if isinstance(value, list)
                else str(value)
            )
            assert link["normalized_value"] == expected
            assert link["lineage_id"] == target["lineage_id"]
            assert link["source_record_id"] == target["source_record_id"]
    accounting = result.receipt["lineage_accounting"]
    assert len(accounting) == source["lineage"].num_rows == 18
    assert {entry["source_lineage_id"] for entry in accounting} == {
        entry["source_lineage_id"] for entry in parent.receipt["lineage_accounting"]
    }
    assert sum(entry["state"] == "mapped" for entry in accounting) == 16
    assert {
        target for entry in accounting for target in entry["target_lineage_record_ids"]
    } == {link["record_id"] for link in links}
    assert [
        entry["field"] for entry in result.receipt["source_field_accounting"]
    ] == SILVER_SCHEMA.names
    assert result.receipt["retained_source_fields"] == [
        "transformation_id",
        "lineage_id",
        "donor_table",
        "donor_row_number",
        "raw_values_json",
    ]
    assert result.receipt["authoritative_mapping"] == "not_performed"
    assert result.receipt["inherited_field_scope"] == {
        "unit": "source_adapter_assertion_not_independently_established",
        "measure": "source_adapter_assertion",
        "source_decimal_precision": "physical_source_arrow_schema",
        "source_decimal_scale": "physical_source_arrow_schema",
        "source_observation_id": "caller_extraction_context_format_checked_not_preimage_verified",
        "observed_at": "caller_supplied_extraction_observation_not_capture_attestation",
    }
    assert (
        result.receipt["value_token_scope"]
        == "source_extraction_lineage_not_original_ooxml_token"  # noqa: S105
    )


def test_input_order_and_objects_are_preserved(tmp_path: Path) -> None:
    source = inputs(tmp_path)
    before = deepcopy(source)
    expected = project_budget_appropriations(**source)
    assert source == before
    for name in ("facts", "lineage", "dispositions"):
        source[name] = source[name].take(list(reversed(range(source[name].num_rows))))
    assert project_budget_appropriations(**source) == expected


def test_inherited_metadata_scope_is_explicit(tmp_path: Path) -> None:
    result = project_budget_appropriations(**inputs(tmp_path))
    assert "inherited_field_scope" in result.receipt


def _amounts(source: dict[str, Any], token: str) -> None:
    for name in ("facts", "dispositions", "lineage"):
        table = source[name]
        rows = table.to_pylist()
        for row in rows:
            if name in {"facts", "dispositions"}:
                raw = json.loads(row["raw_values_json"])
                raw["Amount $000"] = token
                row["raw_values_json"] = json.dumps(
                    raw, sort_keys=True, ensure_ascii=False
                )
            if name == "facts":
                row["amount"] = Decimal(token)
            elif name == "lineage" and row["field"] == "amount":
                row["raw_value"] = token
                row["normalized_value"] = format(Decimal(token), ".3f")
        source[name] = pa.Table.from_pylist(rows, schema=table.schema)


@pytest.mark.parametrize(
    "token",
    [
        "0.000",
        "-0.001",
        "-99999999999999999.999",
        "99999999999999999.999",
        "1.230",
        "1.2300",
    ],
)
def test_exact_source_decimals_ignore_ambient_context(
    tmp_path: Path, token: str
) -> None:
    source = inputs(tmp_path)
    _amounts(source, token)
    normal = project_budget_appropriations(**source)
    original_precision = getcontext().prec
    with localcontext() as context:
        context.prec = 2
        limited = project_budget_appropriations(**source)
        assert context.prec == 2
    assert getcontext().prec == original_precision
    assert limited == normal
    assert all(
        row["amount"] == Decimal(token) and row["value_token"] == token
        for row in limited.tables["appropriation_fact"].to_pylist()
    )


def test_pin_and_vintage_keep_separate_identity_spaces(tmp_path: Path) -> None:
    source = inputs(tmp_path)
    first = project_budget_appropriations(**source)
    source["manifest_sha256"] = "a" * 64
    second = project_budget_appropriations(**source)
    source["manifest"]["source_vintage"] = "Budget-2026"
    rows = source["facts"].to_pylist()
    for row in rows:
        row["source_vintage"] = "Budget-2026"
    source["facts"] = pa.Table.from_pylist(rows, schema=source["facts"].schema)
    third = project_budget_appropriations(**source)
    for name in first.tables:
        sets = [
            {row["record_id"] for row in result.tables[name].to_pylist()}
            for result in (first, second, third)
        ]
        assert not sets[0] & sets[1]
        assert not sets[1] & sets[2]


@pytest.mark.parametrize(
    ("value", "token"),
    [
        (None, "1"),
        (1, "1"),
        (Decimal("NaN"), "NaN"),
        (Decimal("Infinity"), "Infinity"),
        (Decimal("1.000"), None),
        (Decimal("1.000"), ""),
        (Decimal("1.000"), "2"),
        (Decimal("1.000"), "NaN"),
        (Decimal("1.000"), "Infinity"),
        (Decimal("1.000"), "0" * 256 + "1"),
        (Decimal("1.0000"), "1"),
        (Decimal("100000000000000000.000"), "100000000000000000"),
    ],
)
def test_numeric_carrier_guard_fails_closed(value: object, token: object) -> None:
    with pytest.raises(ValueError, match="budget_projection_contract"):
        _amount(value, token)


def test_exact_numeric_token_boundary() -> None:
    assert _amount(Decimal("1.000"), "0" * 255 + "1") == Decimal("1.000")


def test_source_token_value_divergence_is_never_repaired(tmp_path: Path) -> None:
    source = inputs(tmp_path)
    _amounts(source, "1.234")
    for name in ("facts", "dispositions", "lineage"):
        table = source[name]
        rows = table.to_pylist()
        for row in rows:
            if name in {"facts", "dispositions"}:
                raw = json.loads(row["raw_values_json"])
                raw["Amount $000"] = "1.2345"
                row["raw_values_json"] = json.dumps(
                    raw, sort_keys=True, ensure_ascii=False
                )
            elif row["field"] == "amount":
                row["raw_value"] = "1.2345"
        source[name] = pa.Table.from_pylist(rows, schema=table.schema)
    with pytest.raises(ValueError, match="budget_package_contract"):
        project_budget_appropriations(**source)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("rights_state", "cleared"),
        ("status", "partial"),
        ("source_vintage", "unknown"),
        ("transformation_id", "unknown"),
        ("schema_version", "unknown"),
    ],
)
def test_parent_validation_is_mandatory(tmp_path: Path, field: str, value: str) -> None:
    source = inputs(tmp_path)
    source["manifest"][field] = value
    with pytest.raises(ValueError, match="budget_classification_contract"):
        project_budget_appropriations(**source)


@pytest.mark.parametrize(
    "kind",
    [
        "missing_link",
        "duplicate_link",
        "wrong_label",
        "unverified_vote",
        "wrong_amount",
        "wrong_schema",
        "duplicate_fact",
    ],
)
def test_inconsistent_source_tables_never_project(tmp_path: Path, kind: str) -> None:
    source = inputs(tmp_path)
    if kind in {"missing_link", "duplicate_link"}:
        table = source["lineage"]
        rows = table.to_pylist()
        if kind == "missing_link":
            rows.pop()
        else:
            rows.append(rows[0])
        source["lineage"] = pa.Table.from_pylist(rows, schema=table.schema)
    elif kind == "wrong_schema":
        source["facts"] = source["facts"].replace_schema_metadata({"wrong": "metadata"})
    elif kind == "unverified_vote":
        rows = source["lineage"].to_pylist()
        next(row for row in rows if row["field"] == "raw:Vote")["raw_value"] = "Other"
        source["lineage"] = pa.Table.from_pylist(rows, schema=source["lineage"].schema)
    else:
        rows = source["facts"].to_pylist()
        if kind == "duplicate_fact":
            rows.append(rows[0])
        else:
            rows[0]["appropriation_name" if kind == "wrong_label" else "amount"] = (
                "wrong" if kind == "wrong_label" else Decimal("9.000")
            )
        source["facts"] = pa.Table.from_pylist(rows, schema=source["facts"].schema)
    with pytest.raises(ValueError, match=r"budget_(classification|package)_contract"):
        project_budget_appropriations(**source)
