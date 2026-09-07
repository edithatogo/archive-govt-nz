"""Linked synthetic Bronze fixtures and approved adapter transport contracts."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import asdict, replace
from datetime import date
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_budget_classification import inputs
from tests.domains.health_appropriations.test_cpi import HEADER, META
from tests.domains.health_appropriations.test_historical_projection import (
    _inputs,
    _reconcile_links,
    _replace_fact,
)
from tests.domains.health_appropriations.test_pharmac import fixture_source, run
from tests.schemas.test_health_recordset_fixture_acceptance import (
    FIXTURE,
    NAMES,
    rows_for,
)

from archive_govt_nz.domains.health_appropriations.budget_projection import (
    RULE,
    project_budget_appropriations,
)
from archive_govt_nz.domains.health_appropriations.cpi import normalize_cpi
from archive_govt_nz.domains.health_appropriations.historical_projection import (
    project_historical,
)
from archive_govt_nz.domains.health_appropriations.inventory import (
    Disposition,
    SourceInventoryRecord,
    validate_inventory,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import identity
from archive_govt_nz.schemas.health_recordset_normalization import (
    normalize_json,
    normalize_rows,
    validate_table,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_inventory_identity_and_predecessor_contract_survive_transport() -> None:
    """Carry approved census IDs; retain source predecessor evidence separately."""
    first = SourceInventoryRecord(
        source_id="synthetic:old",
        family="synthetic",
        title="Synthetic Health",
        url="https://example.invalid/health",
        observed_at="2026-09-07T00:00:00Z",
        cutoff="2026-09-07",
        disposition=Disposition.DISCOVERED,
        vintage="2025",
        reason="synthetic_fixture",
    )
    second = replace(
        first,
        source_id="synthetic:new",
        vintage="2026",
        disposition=Disposition.SUPERSEDED,
        predecessor_source_id=first.source_id,
    )
    validate_inventory([first, second])
    with pytest.raises(ValueError, match="unknown_predecessor"):
        validate_inventory([second])
    rows = []
    for record in (first, second):
        expected = (
            "sha256:"
            + hashlib.sha256(
                json.dumps(
                    asdict(record), sort_keys=True, separators=(",", ":"), default=str
                ).encode()
            ).hexdigest()
        )
        assert record.record_id == expected
        row = rows_for("source_inventory")[0]
        row.update(
            record_id=record.record_id,
            source_record_id=record.source_id,
            source_vintage=record.vintage,
            disposition=record.disposition.value,
            reason=record.reason,
        )
        rows.append(row)
    tables = _transport({"source_inventory": normalize_rows("source_inventory", rows)})
    assert tables["source_inventory"]["record_id"].to_pylist() == [
        first.record_id,
        second.record_id,
    ]
    assert first.record_id != second.record_id
    assert replace(first).record_id == first.record_id


def _json_value(value: object) -> str:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def _transport(tables: dict[str, pa.Table]) -> dict[str, pa.Table]:
    """Re-admit adapter output through JSON Schema, Arrow and Parquet."""
    restored = {}
    for name, table in tables.items():
        validate_table(name, table)
        payload = json.dumps(table.to_pylist(), default=_json_value).encode()
        admitted = normalize_json(name, payload)
        assert admitted.equals(table, check_metadata=True)
        stream = BytesIO()
        pq.write_table(admitted, stream)
        stream.seek(0)
        restored[name] = pq.read_table(stream)
        validate_table(name, restored[name])
        assert restored[name].equals(table, check_metadata=True)
    return restored


def _linked_fixture() -> tuple[bytes, dict[str, pa.Table]]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    # This compact JSON object is the synthetic original; no live source needed.
    bronze = json.dumps(fixture["source_cells"], sort_keys=True).encode()
    digest = hashlib.sha256(bronze).hexdigest()
    records = {name: rows_for(name) for name in NAMES[:-1]}
    links = []
    for name, rows in records.items():
        for row in rows:
            row["source_object_sha256"] = digest
            row["lineage_id"] = identity(row["record_id"], "lineage")
            if name == "appropriation_fact":
                suffix = row["record_id"].rsplit(":", 1)[1]
                row["classification_ids"] = [
                    f"fixture:classification_dimension:{suffix}"
                ]
            for field in fixture["source_cells"][name]:
                coordinate = f"/{name}/{field}"
                link = {key: row[key] for key in fixture["common"]}
                link.update(
                    record_id=identity(row["record_id"], field, coordinate),
                    recordset="field_lineage",
                    target_record_id=row["record_id"],
                    field=field,
                    source_coordinate=coordinate,
                    raw_value=fixture["source_cells"][name][field],
                    normalized_value=str(row[field]),
                    rule="synthetic-cell-copy/v1",
                )
                links.append(link)
    records["field_lineage"] = links
    return bronze, {name: normalize_rows(name, rows) for name, rows in records.items()}


def _assert_fixture_closure(bronze: bytes, tables: dict[str, pa.Table]) -> None:
    """Independent fixture oracle, not a new production admission policy."""
    cells = json.loads(bronze)
    digest = hashlib.sha256(bronze).hexdigest()
    targets = {
        row["record_id"]: row
        for name, table in tables.items()
        if name != "field_lineage"
        for row in table.to_pylist()
    }
    dimensions = set(tables["classification_dimension"]["record_id"].to_pylist())
    expected = {
        (row["record_id"], field)
        for row in targets.values()
        for field in cells[row["recordset"]]
    }
    actual = []
    for link in tables["field_lineage"].to_pylist():
        target = targets[link["target_record_id"]]
        field = link["field"]
        actual.append((target["record_id"], field))
        assert link["source_coordinate"] == f"/{target['recordset']}/{field}"
        raw = cells[target["recordset"]][field]
        assert link["raw_value"] == raw
        if field == "amount":
            assert Decimal(raw) == target[field] == Decimal(link["normalized_value"])
        else:
            assert raw == target[field] == link["normalized_value"]
        for key in (
            "source_object_sha256",
            "source_vintage",
            "rights_state",
            "lineage_id",
        ):
            assert link[key] == target[key]
        assert target["source_object_sha256"] == digest
        assert (
            link["record_id"]
            == "sha256:"
            + hashlib.sha256(
                "\x1f".join(
                    (target["record_id"], field, link["source_coordinate"])
                ).encode()
            ).hexdigest()
        )
    assert set(actual) == expected
    assert len(actual) == len(expected)
    for row in tables["appropriation_fact"].to_pylist():
        assert set(row["classification_ids"]) <= dimensions


def test_all_eight_linked_fixtures_resolve_to_synthetic_bronze() -> None:
    """Every declared source cell and classification survives typed transport."""
    bronze, tables = _linked_fixture()
    assert set(tables) == set(NAMES)
    _assert_fixture_closure(bronze, tables)
    _assert_fixture_closure(bronze, _transport(tables))
    second_bronze, second = _linked_fixture()
    assert second_bronze == bronze
    assert all(
        second[name].equals(table, check_metadata=True)
        for name, table in tables.items()
    )


@pytest.mark.parametrize(
    "fault",
    [
        "missing",
        "duplicate",
        "target",
        "coordinate",
        "hash",
        "value",
        "vintage",
        "rights",
        "classification",
    ],
)
def test_linked_fixture_oracle_detects_corruption(fault: str) -> None:
    """Prove the closure assertions detect each claimed fixture corruption."""
    bronze, tables = _linked_fixture()
    name = "appropriation_fact" if fault == "classification" else "field_lineage"
    rows = tables[name].to_pylist()
    if fault == "missing":
        rows.pop()
    elif fault == "duplicate":
        rows.append(deepcopy(rows[0]))
    else:
        key, value = {
            "target": ("target_record_id", "missing"),
            "coordinate": ("source_coordinate", "/wrong/cell"),
            "hash": ("source_object_sha256", "f" * 64),
            "value": ("raw_value", "wrong"),
            "vintage": ("source_vintage", "wrong"),
            "rights": ("rights_state", "cleared"),
            "classification": ("classification_ids", ["missing"]),
        }[fault]
        rows[0][key] = value
    tables[name] = pa.Table.from_pylist(rows, schema=tables[name].schema)
    with pytest.raises((AssertionError, KeyError)):
        _assert_fixture_closure(bronze, tables)


@pytest.mark.parametrize("profile", ["budget", "historical", "historical_gdp"])
def test_approved_adapter_identity_and_lineage_cross_all_formats(
    tmp_path: Path, profile: str
) -> None:
    """Existing approved adapters supply real contract IDs, not placeholder IDs."""
    source = inputs(tmp_path) if profile == "budget" else _inputs()
    if profile == "historical_gdp":
        _replace_fact(
            source,
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
            link
            for link in source["lineage"].to_pylist()
            if link["field"] not in {"accounting_basis", "footnotes"}
        ]
        for link in rows:
            if link["source_coordinate"].endswith("A5"):
                link["raw_value"] = "March Years"
        source["lineage"] = pa.Table.from_pylist(rows, schema=source["lineage"].schema)
        source["manifest"]["counts"]["lineage"] = len(rows)
        _reconcile_links(source, {"measure": "Nominal GDP"})
    project = (
        project_budget_appropriations if profile == "budget" else project_historical
    )
    result = project(**source)
    tables = _transport(result.tables)
    targets = {
        row["record_id"]: row
        for name, table in tables.items()
        if name != "field_lineage"
        for row in table.to_pylist()
    }
    source_links = source["lineage"].to_pylist()
    for link in tables["field_lineage"].to_pylist():
        target = targets[link["target_record_id"]]
        assert link["lineage_id"] == target["lineage_id"]
        assert any(
            original["record_id"] == link["source_record_id"]
            and original["source_coordinate"] == link["source_coordinate"]
            and original["source_object_sha256"] == link["source_object_sha256"]
            and original["raw_value"] == link["raw_value"]
            for original in source_links
        )
    accounted = {
        target
        for entry in result.receipt["lineage_accounting"]
        for target in entry["target_lineage_record_ids"]
    }
    assert accounted == set(tables["field_lineage"]["record_id"].to_pylist())
    assert result.receipt["publication_approval"] == "not_granted"
    # The approved canonical ID contracts include the manifest pin and vintage.
    for name in ("facts", "lineage", "dispositions"):
        source[name] = source[name].take(list(reversed(range(source[name].num_rows))))
    assert project(**source) == result
    source["manifest_sha256"] = "f" * 64
    changed = project(**source)
    for name, table in tables.items():
        assert not set(table["record_id"].to_pylist()) & set(
            changed.tables[name]["record_id"].to_pylist()
        )
    if profile == "budget":
        for row in tables["appropriation_fact"].to_pylist():
            parts = (
                RULE,
                result.receipt["input_manifest_sha256"],
                row["source_object_sha256"],
                row["source_vintage"],
                row["source_record_id"],
                "appropriation_fact",
            )
            digest = hashlib.sha256(
                json.dumps(
                    parts,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode()
            ).hexdigest()
            assert row["record_id"] == "sha256:" + digest


@pytest.mark.parametrize("profile", ["budget", "historical"])
@pytest.mark.parametrize(
    "field", ["record_id", "source_object_sha256", "source_coordinate", "raw_value"]
)
def test_approved_adapter_rejects_broken_lineage(
    tmp_path: Path, profile: str, field: str
) -> None:
    """Semantic rejection occurs at the approved source adapter boundary."""
    source = inputs(tmp_path) if profile == "budget" else _inputs()
    rows = source["lineage"].to_pylist()
    rows[0][field] = "broken"
    source["lineage"] = pa.Table.from_pylist(rows, schema=source["lineage"].schema)
    project = (
        project_budget_appropriations if profile == "budget" else project_historical
    )
    with pytest.raises(ValueError, match=r"(budget|historical)_.*contract"):
        project(**source)


@pytest.mark.parametrize("profile", ["cpi", "pharmac"])
def test_source_adapter_ids_and_amount_lineage_fit_fixture_contract(
    tmp_path: Path, profile: str
) -> None:
    """Test-only field mapping retains approved source IDs without promotion."""
    output = tmp_path / "output"
    if profile == "cpi":
        path = tmp_path / "source.csv"
        path.write_text(HEADER + "CPIQ.SE9A,2026.06,123.450" + META)
        pin = hashlib.sha256(path.read_bytes()).hexdigest()
        normalize_cpi(
            path,
            output,
            expected_sha256=pin,
            source_locator="https://example.invalid/cpi.csv",
            source_vintage="2026-Q2",
            observed_at="2026-09-07T00:00:00Z",
            dry_run=False,
        )
        filename, name = "cpi_facts.parquet", "price_population_fact"
    else:
        path, pin = fixture_source(tmp_path)
        run(path, pin, output, dry_run=False)
        filename, name = (
            "pharmaceutical_budget_facts.parquet",
            "pharmaceutical_budget_fact",
        )
    original = path.read_bytes()
    source_facts = pq.read_table(output / filename).to_pylist()
    source_links = pq.read_table(output / "field_lineage.parquet").to_pylist()
    rows, links = [], []
    for source in source_facts:
        parts = [source["transformation_id"], pin]
        if profile == "cpi":
            parts.append(source["series_reference"])
        parts.append(str(source["source_row"]))
        expected = "sha256:" + hashlib.sha256("\x1f".join(parts).encode()).hexdigest()
        assert source["record_id"] == expected
        assert source["lineage_id"] == identity(expected, "lineage")
        row = rows_for(name)[0]
        for key in (
            "record_id",
            "source_object_sha256",
            "source_observation_id",
            "source_locator",
            "source_vintage",
            "observed_at",
            "rights_state",
            "quality_flags",
            "transformation_id",
            "lineage_id",
            "unit",
            "period_token",
        ):
            row[key] = source[key]
        row.update(
            source_record_id=source["record_id"],
            source_schema_version=source["schema_version"],
            amount=format(source["amount"], "f"),
            source_decimal_precision=38,
            source_decimal_scale=18,
            valid_time_start=source.get("period_start"),
            valid_time_end=source["period_end"],
            valid_time_status="fixture_adapter_dates",
        )
        match = [
            link
            for link in source_links
            if link["record_id"] == expected and link["field"] == "amount"
        ]
        assert len(match) == 1
        source_link = match[0]
        row["value_token"] = source_link["raw_value"]
        assert Decimal(source_link["raw_value"].replace(",", "")) == source["amount"]
        rows.append(row)
        link = rows_for("field_lineage")[0]
        for key in (
            "source_object_sha256",
            "source_locator",
            "source_vintage",
            "observed_at",
            "rights_state",
            "lineage_id",
            "source_record_id",
        ):
            link[key] = row[key]
        link.update(
            record_id=identity(expected, "amount", source_link["source_coordinate"]),
            target_record_id=expected,
            field="amount",
            source_coordinate=source_link["source_coordinate"],
            raw_value=source_link["raw_value"],
            normalized_value=str(source["amount"]),
            rule=source_link["rule"],
        )
        links.append(link)
    tables = {
        key: normalize_json(key, json.dumps(values, default=_json_value).encode())
        for key, values in ((name, rows), ("field_lineage", links))
    }
    restored = _transport(tables)
    assert set(restored[name]["record_id"].to_pylist()) == set(
        restored["field_lineage"]["target_record_id"].to_pylist()
    )
    assert path.read_bytes() == original
    assert hashlib.sha256(original).hexdigest() == pin
