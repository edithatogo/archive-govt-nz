"""Pure source-label dimensions remain unmapped and preserve occurrences."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from hypothesis import given
from hypothesis import strategies as st
from tests.domains.health_appropriations.test_budget import ROW, _run, _source

from archive_govt_nz.domains.health_appropriations import budget_classification
from archive_govt_nz.domains.health_appropriations.budget_classification import (
    LABELS,
    SCHEME,
    _id,
    project_budget_classification,
)
from archive_govt_nz.domains.health_appropriations.silver import SILVER_SCHEMA
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def inputs(
    tmp_path: Path, labels: list[str] | None = None, *, amount: int = 123
) -> dict[str, Any]:
    source, package = tmp_path / "source.xlsx", tmp_path / "package"
    rows = []
    for label in labels or ["Health", "Health"]:
        row = list(ROW)
        row[4] = label
        row[5] = amount
        rows.append(row)
    digest = _source(source, rows)
    _run(source, package, digest)
    return {
        "manifest": json.loads((package / "MANIFEST.json").read_text()),
        "manifest_sha256": hashlib.sha256(
            (package / "MANIFEST.json").read_bytes()
        ).hexdigest(),
        "facts": pq.read_table(package / "budget_facts.parquet"),
        "lineage": pq.read_table(package / "field_lineage.parquet"),
        "dispositions": pq.read_table(package / "row_dispositions.parquet"),
    }


def test_unmapped_occurrences_are_not_pooled(tmp_path: Path) -> None:
    result = project_budget_classification(**inputs(tmp_path))
    rows = result.tables["classification_dimension"].to_pylist()
    assert len(rows) == len({row["record_id"] for row in rows}) == 2
    assert all(row["source_label"] == "Health" for row in rows)
    assert all(row["mapping_state"] == "unmapped" for row in rows)
    assert all(row["normalized_identifier"] is None for row in rows)
    assert all(row["scheme_version"] is None for row in rows)
    assert result.receipt["input_fixity"] == "not_performed"


def test_all_labels_and_complete_accounting(tmp_path: Path) -> None:
    source = inputs(tmp_path, sorted(LABELS))
    before = deepcopy(source)
    result = project_budget_classification(**source)
    dimensions = result.tables["classification_dimension"].to_pylist()
    links = result.tables["field_lineage"].to_pylist()
    indexed = {row["record_id"]: row for row in dimensions}
    assert {row["source_label"] for row in dimensions} == LABELS
    assert len(dimensions) == len(links) == 4
    for row in dimensions:
        assert row["scheme"] == SCHEME
        assert row["mapping_method"] == "source_label_retention_only"
        assert row["mapping_state"] == "unmapped"
        assert row["scheme_version"] is row["normalized_identifier"] is None
        assert (
            row["valid_time_start"]
            is row["valid_time_end"]
            is row["period_token"]
            is None
        )
        assert row["valid_time_status"] == "not_established"
        assert row["rights_state"] == "not_evaluated"
        assert row["source_vintage"] == "Budget-2025"
        evidence = json.loads(row["mapping_evidence"])
        assert evidence["input_manifest_sha256"] == source["manifest_sha256"]
        expected = next(
            item
            for item in source["lineage"].to_pylist()
            if item["record_id"] == row["source_record_id"]
            and item["field"] == "functional_classification"
        )
        assert evidence["source_coordinate"] == expected["source_coordinate"]
    for link in links:
        target = indexed[link["target_record_id"]]
        assert link["field"] == "source_label"
        assert link["raw_value"] == link["normalized_value"] == target["source_label"]
        assert link["source_record_id"] == target["source_record_id"]
        assert link["lineage_id"] == target["lineage_id"]
    accounting = result.receipt["lineage_accounting"]
    assert len(accounting) == source["lineage"].num_rows == 36
    assert len({row["source_lineage_id"] for row in accounting}) == len(accounting)
    assert sum(row["state"] == "mapped" for row in accounting) == 4
    assert sum(row["state"] == "retained_only" for row in accounting) == 32
    assert {
        target for row in accounting for target in row["target_lineage_record_ids"]
    } == {row["record_id"] for row in links}
    assert result.receipt["authoritative_mapping"] == "not_performed"
    assert result.receipt["publication_approval"] == "not_granted"
    assert source == before
    for name in ("facts", "lineage", "dispositions"):
        source[name] = source[name].take(list(reversed(range(source[name].num_rows))))
    assert project_budget_classification(**source) == result


@pytest.mark.parametrize("label", ["Unknown", "health", "Health ", "", "None"])
def test_unreviewed_labels_rejected(tmp_path: Path, label: str) -> None:
    source = inputs(tmp_path, [label])
    with pytest.raises(ValueError, match="budget_classification_contract"):
        project_budget_classification(**source)


def replace_row(source: dict[str, Any], name: str, key: str, value: object) -> None:
    table = source[name]
    rows = table.to_pylist()
    rows[0][key] = value
    source[name] = pa.Table.from_pylist(rows, schema=table.schema)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "wrong"),
        ("status", "failed"),
        ("transformation_id", "wrong"),
        ("rights_state", "eligible"),
        ("source_vintage", "Budget-2027"),
        ("source_object_sha256", "bad"),
    ],
)
def test_manifest_drift(tmp_path: Path, field: str, value: str) -> None:
    source = inputs(tmp_path)
    source["manifest"][field] = value
    with pytest.raises(
        ValueError, match=r"budget_classification_contract|budget_package_contract"
    ):
        project_budget_classification(**source)


@pytest.mark.parametrize(
    ("table", "field", "value"),
    [
        ("facts", "rights_state", "eligible"),
        ("facts", "functional_classification", "No Functional Classification"),
        ("facts", "source_vintage", "Budget-2026"),
        ("facts", "record_id", "sha256:" + "f" * 64),
        ("lineage", "raw_value", "contradiction"),
        ("lineage", "source_coordinate", "'Raw Data'!Z99"),
        ("lineage", "field", "unknown"),
        ("dispositions", "raw_values_json", "{}"),
    ],
)
def test_source_consistency(tmp_path: Path, table: str, field: str, value: str) -> None:
    source = inputs(tmp_path)
    replace_row(source, table, field, value)
    with pytest.raises(ValueError, match="budget_package_contract"):
        project_budget_classification(**source)


@pytest.mark.parametrize("table", ["facts", "lineage", "dispositions"])
@pytest.mark.parametrize("change", ["schema", "metadata", "empty", "duplicate"])
def test_table_contracts(tmp_path: Path, table: str, change: str) -> None:
    source = inputs(tmp_path)
    original = source[table]
    if change == "schema":
        source[table] = pa.table({"wrong": [1]})
    elif change == "metadata":
        source[table] = original.replace_schema_metadata({"wrong": "metadata"})
    elif change == "empty":
        source[table] = original.slice(0, 0)
    else:
        source[table] = pa.concat_tables([original, original.slice(0, 1)])
    with pytest.raises(
        ValueError, match=r"budget_classification_contract|budget_package_contract"
    ):
        project_budget_classification(**source)


@pytest.mark.parametrize("pin", [None, 1, "x" * 64, "a" * 63])
def test_invalid_pin(tmp_path: Path, pin: object) -> None:
    source = inputs(tmp_path)
    source["manifest_sha256"] = pin
    with pytest.raises(ValueError, match="budget_classification_contract"):
        project_budget_classification(**source)


def test_in_memory_schema_and_max_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    source["facts"] = pa.Table.from_pylist(
        source["facts"].to_pylist(), schema=SILVER_SCHEMA
    )
    assert (
        project_budget_classification(**source)
        .tables["classification_dimension"]
        .num_rows
        == 2
    )
    monkeypatch.setattr(budget_classification, "_MAX_ROWS", 1)
    with pytest.raises(ValueError, match="budget_classification_contract"):
        project_budget_classification(**source)


def test_vintage_and_pin_identity(tmp_path: Path) -> None:
    source = inputs(tmp_path)
    first = project_budget_classification(**source)
    source["manifest"]["source_vintage"] = "Budget-2026"
    rows = source["facts"].to_pylist()
    for row in rows:
        row["source_vintage"] = "Budget-2026"
    source["facts"] = pa.Table.from_pylist(rows, schema=source["facts"].schema)
    second = project_budget_classification(**source)
    source["manifest_sha256"] = "f" * 64
    third = project_budget_classification(**source)
    ids = [
        set(result.tables["classification_dimension"]["record_id"].to_pylist())
        for result in (first, second, third)
    ]
    assert len(set.union(*ids)) == 6


@given(st.text(), st.text())
def test_identity_encoding_is_unambiguous(left: str, right: str) -> None:
    assert _id(left, right) == _id(left, right)
    assert _id(left, right) != _id([left, right])


def test_exact_canonical_parquet_roundtrip(tmp_path: Path) -> None:
    result = project_budget_classification(**inputs(tmp_path))
    for name, table in result.tables.items():
        expected = recordset_schema(name)
        assert table.schema.equals(expected, check_metadata=True)
        stream = pa.BufferOutputStream()
        pq.write_table(table, stream)
        restored = pq.read_table(pa.BufferReader(stream.getvalue()))
        assert restored.schema.equals(expected, check_metadata=True)
        assert restored.equals(table, check_metadata=True)
        assert all(
            field.nullable == expected.field(field.name).nullable
            for field in restored.schema
        )


def test_source_object_identity_is_distinct(tmp_path: Path) -> None:
    first_root, second_root = tmp_path / "first", tmp_path / "second"
    first_root.mkdir()
    second_root.mkdir()
    first, second = inputs(first_root), inputs(second_root, amount=124)
    assert (
        first["manifest"]["source_object_sha256"]
        != second["manifest"]["source_object_sha256"]
    )
    second["manifest_sha256"] = first["manifest_sha256"]
    # Pure projection does not verify the caller's pin; hold it equal to isolate
    # source identity, while both internally consistent source snapshots differ.
    left, right = (
        project_budget_classification(**source).tables["classification_dimension"]
        for source in (first, second)
    )
    assert left["source_label"].to_pylist() == right["source_label"].to_pylist()
    assert set(left["record_id"].to_pylist()).isdisjoint(right["record_id"].to_pylist())
