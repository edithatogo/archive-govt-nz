"""Source-faithful canonical projection for Pharmac's published CPB table."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import TYPE_CHECKING, Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import pharmac
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
    verified_snapshot,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from decimal import Decimal
    from pathlib import Path

MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_PRODUCT_BYTES = 64 * 1024 * 1024
MAX_PACKAGE_BYTES = 128 * 1024 * 1024
SOURCE_LOCATOR = (
    "https://www.pharmac.govt.nz/medicine-funding-and-supply/"
    "the-funding-process/setting-and-managing-the-combined-pharmaceutical-"
    "budget-cpb/budget-bid-information"
)
SOURCE_VINTAGE = "Pharmac-CPB-2026-08-07"
PROJECTION_RULE = "pharmac-cpb-canonical-source-faithful/v1"
PRODUCTS = {
    "pharmaceutical_budget_facts.parquet",
    "field_lineage.parquet",
    "cell_dispositions.parquet",
}
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_SCHEMA_VERSION = "archive-govt-nz.health-recordsets/v1"
_EXPECTED_MANIFEST_SCHEMA = "archive-govt-nz.health-pharmac-extraction/v1"
_CUTOFF = date(2022, 7, 1)
_EXPECTED_FACTS = pharmac.TABLE_ROWS - 1
_EXPECTED_CELL_DISPOSITIONS = 64
_SOURCE_AMOUNT_SCALE = pharmac.FACT_SCHEMA.field("amount").type.scale


def _require(condition: object) -> None:
    if not condition:
        message = "pharmac_canonical_projection_invalid"
        raise ValueError(message)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _schema_signature(schema: pa.Schema) -> tuple[tuple[str, str, bool], ...]:
    """Ignore Parquet's inconsequential list child name while checking fields."""
    return tuple(
        (
            field.name,
            str(pa.list_(field.type.value_type))
            if pa.types.is_list(field.type)
            else str(field.type),
            field.nullable,
        )
        for field in schema
    )


def _read_manifest(root: Path, manifest_sha256: str) -> tuple[dict[str, Any], bytes]:
    _require(not root.is_symlink() and root.is_dir())
    marker = root / "MANIFEST.json"
    _require(not marker.is_symlink() and marker.is_file())
    with marker.open("rb") as stream:
        payload = stream.read(MAX_MANIFEST_BYTES + 1)
    _require(
        len(payload) <= MAX_MANIFEST_BYTES
        and hashlib.sha256(payload).hexdigest() == manifest_sha256
    )
    manifest = json.loads(payload, object_pairs_hook=_pairs)
    _require(isinstance(manifest, dict))
    _require(
        manifest.get("schema_version") == _EXPECTED_MANIFEST_SCHEMA
        and manifest.get("transformation_id") == pharmac.TRANSFORMATION
        and manifest.get("status") == "passed"
        and manifest.get("rights_state") == "not_evaluated"
        and manifest.get("source_locator") == SOURCE_LOCATOR
        and manifest.get("source_vintage") == SOURCE_VINTAGE
    )
    _require({path.name for path in root.iterdir()} == PRODUCTS | {"MANIFEST.json"})
    return cast("dict[str, Any]", manifest), payload


def _source_tables(
    root: Path,
    manifest: dict[str, Any],
    source_cas_root: Path,
    source_sha256: str,
) -> tuple[pa.Table, pa.Table, pa.Table]:
    _require(_DIGEST.fullmatch(source_sha256) is not None)
    _require(manifest.get("source_object_sha256") == source_sha256)
    _require(not source_cas_root.is_symlink() and source_cas_root.is_dir())
    source = source_cas_root / source_sha256[:2] / source_sha256
    _require(
        not source.parent.is_symlink() and not source.is_symlink() and source.is_file()
    )
    bronze = verified_snapshot(source, source_sha256, max_bytes=pharmac.MAX_BYTES)
    _require(source_cas_root == source.parent.parent)
    fact_path = root / "pharmaceutical_budget_facts.parquet"
    _require(not fact_path.is_symlink() and fact_path.is_file())
    _require(fact_path.stat().st_size <= MAX_PRODUCT_BYTES)
    declared_hashes = manifest.get("output_sha256")
    _require(isinstance(declared_hashes, dict))
    hashes = cast("dict[str, str]", declared_hashes)
    _require(set(hashes) == PRODUCTS)
    package_bytes = len(bronze)
    for name in sorted(PRODUCTS):
        product_path = root / name
        _require(not product_path.is_symlink() and product_path.is_file())
        size = product_path.stat().st_size
        _require(0 < size <= MAX_PRODUCT_BYTES)
        package_bytes += size
    _require(package_bytes <= MAX_PACKAGE_BYTES)
    _require(
        hashlib.sha256(fact_path.read_bytes()).hexdigest()
        == hashes.get("pharmaceutical_budget_facts.parquet")
    )
    retained_facts = pq.read_table(fact_path)
    retained_rows = retained_facts.to_pylist()
    _require(bool(retained_rows))
    source_observation_ids = {row.get("source_observation_id") for row in retained_rows}
    _require(
        len(source_observation_ids) == 1
        and all(
            row.get("source_object_sha256") == source_sha256
            and row.get("source_locator") == SOURCE_LOCATOR
            and row.get("source_vintage") == SOURCE_VINTAGE
            for row in retained_rows
        )
    )
    context = source_context(
        source_sha256,
        SOURCE_LOCATOR,
        SOURCE_VINTAGE,
        cast("str", manifest["observed_at"]),
    )
    context["source_observation_id"] = next(iter(source_observation_ids))
    parser = pharmac._parse(bronze)  # noqa: SLF001 - preserve the reviewed extractor
    facts, lineage, dispositions = pharmac._extract(  # noqa: SLF001
        parser, context
    )
    tables = (
        pa.Table.from_pylist(facts, schema=pharmac.FACT_SCHEMA),
        pa.Table.from_pylist(lineage, schema=pharmac.LINEAGE_SCHEMA),
        pa.Table.from_pylist(dispositions, schema=pharmac.DISPOSITION_SCHEMA),
    )
    counts = manifest.get("counts")
    _require(
        counts
        == {
            "facts": tables[0].num_rows,
            "lineage": tables[1].num_rows,
            "table_cells": tables[2].num_rows,
        }
    )
    for name in sorted(PRODUCTS):
        path = root / name
        _require(not path.is_symlink() and path.is_file())
        size = path.stat().st_size
        _require(0 < size <= MAX_PRODUCT_BYTES)
        raw = path.read_bytes()
        _require(hashlib.sha256(raw).hexdigest() == hashes[name])
        index = {
            "pharmaceutical_budget_facts.parquet": 0,
            "field_lineage.parquet": 1,
            "cell_dispositions.parquet": 2,
        }[name]
        observed_table = pq.read_table(path)
        _require(
            _schema_signature(observed_table.schema)
            == _schema_signature(tables[index].schema)
        )
        _require(observed_table.to_pylist() == tables[index].to_pylist())
    return tables


def _canonical_id(source_record_id: str) -> str:
    payload = f"{PROJECTION_RULE}\0{source_record_id}".encode()
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _canonical_lineage(
    row: dict[str, Any],
    source_lineage: dict[str, list[dict[str, Any]]],
    canonical_id: str,
) -> list[dict[str, Any]]:
    direct_fields = {
        "period_token": "period_token",
        "amount": "amount",
        "unit": "unit",
        "source_label": "series_caption",
        "valid_time_start": "period_start",
        "valid_time_end": "period_end",
        "budget_scope": "series_caption",
        "funding_regime": "policy_scope_note",
    }
    result = []
    for field, source_field in direct_fields.items():
        candidates = source_lineage[source_field]
        if field.startswith("valid_time_"):
            coordinate = f"html:table=1;row={row['source_row']};cell=1"
            source = next(
                item for item in candidates if item["source_coordinate"] == coordinate
            )
        else:
            source = candidates[0]
        if field == "funding_regime":
            raw = source["raw_value"]
            value = (
                "government_appropriation_allocated_to_pharmac"
                if row["period_start"] >= _CUTOFF
                else "district_health_board_budget_holder"
            )
            rule = PROJECTION_RULE + "/policy_cutover_2022-07-01"
        elif field in {"budget_scope", "source_label"}:
            raw, value, rule = (
                source["raw_value"],
                row["series_caption"],
                PROJECTION_RULE,
            )
        elif field.startswith("valid_time_"):
            source_value = row[field.replace("valid_time_", "period_")]
            raw, value, rule = (
                source["raw_value"],
                source_value.isoformat(),
                PROJECTION_RULE,
            )
        elif field == "amount":
            raw, value, rule = source["raw_value"], str(row[field]), PROJECTION_RULE
        else:
            raw, value, rule = source["raw_value"], str(row[field]), PROJECTION_RULE
        result.append(
            {
                "target_record_id": canonical_id,
                "field": field,
                "source_coordinate": source["source_coordinate"],
                "raw_value": raw,
                "normalized_value": value,
                "rule": rule,
            }
        )
    return result


def project_pharmac_cpb(
    root: Path,
    manifest_sha256: str,
    source_cas_root: Path,
    source_sha256: str,
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Verify the retained Silver package and Bronze original, then project it.

    The source package remains unchanged. Published budget allocations remain
    separate from actual-expenditure facts; published changes are never
    recalculated, price basis remains unknown, and rights remain unevaluated.
    """
    _require(type(manifest_sha256) is str and _DIGEST.fullmatch(manifest_sha256))
    manifest, _ = _read_manifest(root, manifest_sha256)
    facts, lineage, dispositions = _source_tables(
        root, manifest, source_cas_root, source_sha256
    )
    fact_rows = facts.to_pylist()
    lineage_index: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for item in lineage.to_pylist():
        fields = lineage_index.setdefault(item["record_id"], {})
        fields.setdefault(item["field"], []).append(item)
    rows = []
    lineage_rows = []
    canonical_ids = set()
    for fact in fact_rows:
        source_record_id = fact["record_id"]
        canonical_id = _canonical_id(source_record_id)
        _require(canonical_id not in canonical_ids)
        canonical_ids.add(canonical_id)
        source_fields = lineage_index[source_record_id]
        _require(
            {
                "period_token",
                "amount",
                "unit",
                "series_caption",
                "period_start",
                "period_end",
                "policy_scope_note",
            }
            <= set(source_fields)
        )
        amount = cast("Decimal", fact["amount"])
        _require(amount.as_tuple().exponent == -_SOURCE_AMOUNT_SCALE)
        raw_amount = json.loads(fact["raw_values_json"])[1]
        row = {
            "record_id": canonical_id,
            "schema_version": _SCHEMA_VERSION,
            "recordset": "pharmaceutical_budget_fact",
            "domain": "health_appropriations",
            "source_object_sha256": fact["source_object_sha256"],
            "source_observation_id": fact["source_observation_id"],
            "source_locator": fact["source_locator"],
            "source_vintage": fact["source_vintage"],
            "valid_time_start": fact["period_start"],
            "valid_time_end": fact["period_end"],
            "valid_time_status": "source_defined_financial_year",
            "period_token": fact["period_token"],
            "observed_at": fact["observed_at"],
            "observation_context": "published_pharmaceutical_budget_allocation",
            "rights_state": "not_evaluated",
            "quality_flags": fact["quality_flags"],
            "transformation_id": PROJECTION_RULE,
            "lineage_id": hashlib.sha256(
                f"{canonical_id}\0lineage".encode()
            ).hexdigest(),
            "source_record_id": source_record_id,
            "source_schema_version": fact["schema_version"],
            "measure": "pharmaceutical_budget_allocation",
            "amount": amount,
            "value_token": raw_amount,
            "null_reason": None,
            "source_decimal_precision": 20,
            "source_decimal_scale": 3,
            "unit": fact["unit"],
            "currency": "NZD",
            "price_basis": None,
            "base_period": None,
            "denominator_definition": None,
            "amount_type": fact["amount_type"],
            "source_label": fact["series_caption"],
            "budget_scope": fact["series_caption"],
            "funding_regime": (
                "government_appropriation_allocated_to_pharmac"
                if fact["period_start"] >= _CUTOFF
                else "district_health_board_budget_holder"
            ),
        }
        lineage_rows.extend(_canonical_lineage(fact, source_fields, canonical_id))
        rows.append(row)
    _require(
        len(fact_rows) == _EXPECTED_FACTS
        and len(dispositions) == _EXPECTED_CELL_DISPOSITIONS
    )
    _require(len(canonical_ids) == len(fact_rows))
    canonical = pa.Table.from_pylist(
        rows, schema=recordset_schema("pharmaceutical_budget_fact")
    )
    canonical_lineage = pa.Table.from_pylist(
        lineage_rows, schema=recordset_schema("field_lineage")
    )
    receipt = {
        "schema_version": "archive-govt-nz.health-pharmac-canonical-projection/v1",
        "status": "verified_source_faithful_projection",
        "source_manifest_sha256": manifest_sha256,
        "source_object_sha256": source_sha256,
        "source_vintage": SOURCE_VINTAGE,
        "input_records": len(fact_rows),
        "output_records": canonical.num_rows,
        "output_lineage_rows": canonical_lineage.num_rows,
        "source_cell_dispositions": dispositions.num_rows,
        "input_identity_closed": True,
        "source_package_unchanged": True,
        "actual_expenditure": "not_asserted",
        "published_change_recalculation": "not_performed",
        "price_basis": "unknown",
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
    return canonical, canonical_lineage, receipt
