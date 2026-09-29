"""Bronze-bound canonical projection for retained BEFU Crown expense facts."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import crown_expense
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

SOURCE_SHA256 = crown_expense.SOURCE_SHA256
SOURCE_MANIFEST_SHA256 = (
    "23ddc3fb0a3d4d6dc55a4731694f7d9e26f5ace1324d4a76456f1ad761abe651"
)
TRANSFORMATION = "befu-core-crown-canonical-source-faithful/v1"
OBSERVED_AT = "2026-08-29T09:00:17Z"
_MANIFEST_SCHEMA = "archive-govt-nz.health-crown-expense-extraction/v1"
_PRODUCTS = {
    "crown_expense_facts.parquet",
    "field_lineage.parquet",
    "cell_dispositions.parquet",
}
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_MAX_MANIFEST_BYTES = 2 * 1024 * 1024
_MAX_PRODUCT_BYTES = 64 * 1024 * 1024
_MAX_SOURCE_BYTES = 64 * 1024 * 1024
_EXPECTED_FACTS = 10
_EXPECTED_SOURCE_LINEAGE = 60
_ERROR = "crown_expense_canonical_projection_invalid"
_MAX_PRECISION = 38


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _source_tables(
    silver_root: Path, manifest_sha256: str, cas_root: Path
) -> tuple[pa.Table, pa.Table, pa.Table]:
    _require(_DIGEST.fullmatch(manifest_sha256) is not None)
    _require(not silver_root.is_symlink() and silver_root.is_dir())
    marker = silver_root / "MANIFEST.json"
    _require(not marker.is_symlink() and marker.is_file())
    with marker.open("rb") as stream:
        payload = stream.read(_MAX_MANIFEST_BYTES + 1)
    _require(
        len(payload) <= _MAX_MANIFEST_BYTES
        and hashlib.sha256(payload).hexdigest() == manifest_sha256
        and manifest_sha256 == SOURCE_MANIFEST_SHA256
    )
    manifest = json.loads(payload, object_pairs_hook=_pairs)
    _require(
        isinstance(manifest, dict)
        and manifest.get("schema_version") == _MANIFEST_SCHEMA
        and manifest.get("transformation_id") == crown_expense.TRANSFORMATION
        and manifest.get("profile") == crown_expense.PROFILE
        and manifest.get("status") == "passed"
        and manifest.get("rights_state") == "not_evaluated"
        and manifest.get("source_object_sha256") == SOURCE_SHA256
        and manifest.get("source_locator") == crown_expense.SOURCE_LOCATOR
        and manifest.get("source_vintage") == crown_expense.SOURCE_VINTAGE
    )
    _require(
        {path.name for path in silver_root.iterdir()} == _PRODUCTS | {"MANIFEST.json"}
    )
    _require(not cas_root.is_symlink() and cas_root.is_dir())
    original = cas_root / SOURCE_SHA256[:2] / SOURCE_SHA256
    _require(not original.parent.is_symlink() and not original.is_symlink())
    bronze = verified_snapshot(original, SOURCE_SHA256, max_bytes=_MAX_SOURCE_BYTES)
    _require(hashlib.sha256(bronze).hexdigest() == SOURCE_SHA256)
    with tempfile.TemporaryDirectory(prefix="crown-canonical-bronze-") as temporary:
        expected_root = Path(temporary) / "silver"
        expected_receipt = crown_expense.normalize_befu_core_expense(
            original,
            expected_root,
            expected_sha256=SOURCE_SHA256,
            source_locator=crown_expense.SOURCE_LOCATOR,
            source_vintage=crown_expense.SOURCE_VINTAGE,
            observed_at=OBSERVED_AT,
            dry_run=False,
        )
        _require(expected_receipt["source_object_sha256"] == SOURCE_SHA256)
        expected_tables = {
            name: pq.read_table(expected_root / name) for name in sorted(_PRODUCTS)
        }
    _require(manifest.get("counts") == expected_receipt["counts"])
    declared_hashes = manifest.get("output_sha256")
    _require(isinstance(declared_hashes, dict) and set(declared_hashes) == _PRODUCTS)
    hashes = cast("dict[str, str]", declared_hashes)
    tables = {}
    for name in sorted(_PRODUCTS):
        expected_table = expected_tables[name]
        path = silver_root / name
        _require(not path.is_symlink() and path.is_file())
        raw = path.read_bytes()
        _require(0 < len(raw) <= _MAX_PRODUCT_BYTES)
        _require(hashlib.sha256(raw).hexdigest() == hashes[name])
        table = pq.read_table(path)
        _require(table.schema.equals(expected_table.schema))
        _require(table.to_pylist() == expected_table.to_pylist())
        tables[name] = table
    facts = tables["crown_expense_facts.parquet"]
    lineage = tables["field_lineage.parquet"]
    dispositions = tables["cell_dispositions.parquet"]
    _require(
        facts.num_rows == _EXPECTED_FACTS
        and lineage.num_rows == _EXPECTED_SOURCE_LINEAGE
    )
    _require(
        sum(row["disposition"] == "normalized" for row in dispositions.to_pylist())
        == facts.num_rows
    )
    _require(
        all(
            row["source_object_sha256"] == SOURCE_SHA256
            and row["source_vintage"] == crown_expense.SOURCE_VINTAGE
            and row["transformation_id"] == crown_expense.TRANSFORMATION
            for row in facts.to_pylist()
        )
    )
    return facts, lineage, dispositions


def project_befu_core_expense(
    silver_root: Path, manifest_sha256: str, cas_root: Path
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Verify the retained BEFU Silver package and produce unqualified context facts."""
    source_facts, source_lineage, _ = _source_tables(
        silver_root, manifest_sha256, cas_root
    )
    lineage_by_record: dict[str, dict[str, dict[str, Any]]] = {}
    for item in source_lineage.to_pylist():
        lineage_by_record.setdefault(item["record_id"], {})[item["field"]] = item

    facts = []
    lineage = []
    for source in source_facts.to_pylist():
        source_id = source["record_id"]
        identifier = (
            "sha256:"
            + hashlib.sha256(f"{TRANSFORMATION}\0{source_id}".encode()).hexdigest()
        )
        raw = json.loads(source["raw_values_json"])
        cached_token = raw["cached_value"]
        amount = Decimal(cached_token)
        _require(amount == source["amount"])
        amount_parts = amount.as_tuple()
        precision = len(amount_parts.digits)
        scale = max(0, -cast("int", amount_parts.exponent))
        _require(1 <= precision <= _MAX_PRECISION and scale <= precision)
        year = source["year"]
        period_token = f"year_label:{year}"
        fact = {
            "record_id": identifier,
            "schema_version": "archive-govt-nz.health-recordsets/v1",
            "recordset": "fiscal_context_fact",
            "domain": "health_appropriations",
            "source_object_sha256": source["source_object_sha256"],
            "source_observation_id": source["source_observation_id"],
            "source_locator": source["source_locator"],
            "source_vintage": source["source_vintage"],
            "valid_time_start": None,
            "valid_time_end": None,
            "valid_time_status": "financial_year_boundaries_unqualified",
            "period_token": period_token,
            "observed_at": source["observed_at"],
            "observation_context": "treasury_befu_core_crown_expense_formula_cache",
            "rights_state": "not_evaluated",
            "quality_flags": sorted(
                set(source["quality_flags"])
                | {"canonical_projection_preserves_source_uncertainty"}
            ),
            "transformation_id": TRANSFORMATION,
            "lineage_id": hashlib.sha256(f"{identifier}\0lineage".encode()).hexdigest(),
            "source_record_id": source_id,
            "source_schema_version": source["schema_version"],
            "measure": source["measure"],
            "amount": amount,
            "value_token": cached_token,
            "null_reason": None,
            "source_decimal_precision": precision,
            "source_decimal_scale": scale,
            "unit": raw["unit"],
            "currency": None,
            "price_basis": None,
            "base_period": None,
            "denominator_definition": None,
            "amount_type": source["amount_type"].lower(),
            "source_label": raw["label"],
            "institutional_coverage": "core_crown",
            "accounting_basis": None,
            "seasonal_adjustment": None,
        }
        facts.append(fact)
        links = lineage_by_record[source_id]
        mappings = (
            ("measure", "measure", "measure"),
            ("amount", "amount_cache", "amount"),
            ("amount_type", "amount_type", "amount_type"),
            ("unit", "unit", "unit"),
            ("period_token", "year", "period_token"),
            ("source_label", "measure", "source_label"),
        )
        for target_field, source_field, normalized_field in mappings:
            item = links[source_field]
            normalized = str(fact[normalized_field])
            lineage.append(
                {
                    "target_record_id": identifier,
                    "field": target_field,
                    "source_coordinate": item["source_coordinate"],
                    "raw_value": item["raw_value"],
                    "normalized_value": normalized,
                    "rule": TRANSFORMATION,
                }
            )
        year_link = links["year"]
        lineage.append(
            {
                "target_record_id": identifier,
                "field": "valid_time_status",
                "source_coordinate": year_link["source_coordinate"],
                "raw_value": year_link["raw_value"],
                "normalized_value": fact["valid_time_status"],
                "rule": TRANSFORMATION + "/unqualified-year-label",
            }
        )
        label = links["measure"]
        lineage.append(
            {
                "target_record_id": identifier,
                "field": "institutional_coverage",
                "source_coordinate": label["source_coordinate"],
                "raw_value": label["raw_value"],
                "normalized_value": fact["institutional_coverage"],
                "rule": TRANSFORMATION + "/source-label-classification",
            }
        )

    canonical = pa.Table.from_pylist(
        facts, schema=recordset_schema("fiscal_context_fact")
    )
    canonical_lineage = pa.Table.from_pylist(
        lineage, schema=recordset_schema("field_lineage")
    )
    return (
        canonical,
        canonical_lineage,
        {
            "schema_version": "archive-govt-nz.health-crown-canonical-projection/v1",
            "status": "verified_source_faithful_projection",
            "source_manifest_sha256": manifest_sha256,
            "source_object_sha256": SOURCE_SHA256,
            "source_vintage": crown_expense.SOURCE_VINTAGE,
            "input_records": source_facts.num_rows,
            "output_records": canonical.num_rows,
            "output_lineage_rows": canonical_lineage.num_rows,
            "input_identity_closed": True,
            "currency": "unknown",
            "financial_year_boundaries": "unqualified",
            "formula_cache_freshness": "unverified",
            "accounting_basis": "unknown",
            "rights_state": "not_evaluated",
            "denominator_selection": "not_performed",
            "publication": "not_performed",
        },
    )
