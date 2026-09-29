"""Source-bound canonical projection for QES ordinary-time earnings."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import qes
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
    verified_snapshot,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from pathlib import Path

SOURCE_SHA256 = "1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97"
SOURCE_LOCATOR = (
    "https://www.stats.govt.nz/assets/Uploads/Labour-market-statistics/"
    "Labour-market-statistics-June-2026-quarter/Download-data/"
    "quarterly-employment-survey-june-2026-quarter.xlsx"
)
SOURCE_VINTAGE = "QES-2026-Q2"
OBSERVED_AT = "2026-08-29T09:00:17Z"
SOURCE_MANIFEST_SHA256 = (
    "0bf89bd6c10a0458ef4c578b209c3252292961976d2f50b3c27fe92907c3cb04"
)
TRANSFORMATION = "qes-canonical-source-faithful/v1"
_MANIFEST_SCHEMA = "archive-govt-nz.qes-extraction/v1"
_PRODUCTS = {"qes_facts.parquet", "field_lineage.parquet", "cell_dispositions.parquet"}
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_MAX_MANIFEST_BYTES = 2 * 1024 * 1024
_MAX_PRODUCT_BYTES = 64 * 1024 * 1024
_ERROR = "qes_canonical_projection_invalid"
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


def _period_bounds(period_end: date) -> tuple[date, date]:
    quarter_start_month = ((period_end.month - 1) // 3) * 3 + 1
    return date(period_end.year, quarter_start_month, 1), period_end


def _source_tables(
    silver_root: Path,
    manifest_sha256: str,
    cas_root: Path,
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
        and manifest.get("transformation_id") == qes.TRANSFORMATION
        and manifest.get("status") == "passed"
        and manifest.get("rights_state") == "not_evaluated"
        and manifest.get("source_object_sha256") == SOURCE_SHA256
        and manifest.get("source_locator") == SOURCE_LOCATOR
        and manifest.get("source_vintage") == SOURCE_VINTAGE
    )
    _require(
        {path.name for path in silver_root.iterdir()} == _PRODUCTS | {"MANIFEST.json"}
    )
    _require(not cas_root.is_symlink() and cas_root.is_dir())
    original = cas_root / SOURCE_SHA256[:2] / SOURCE_SHA256
    _require(not original.parent.is_symlink() and not original.is_symlink())
    bronze = verified_snapshot(original, SOURCE_SHA256, max_bytes=qes.MAX_BYTES)
    context = source_context(
        SOURCE_SHA256,
        SOURCE_LOCATOR,
        SOURCE_VINTAGE,
        OBSERVED_AT,
    )
    facts, lineage, dispositions = qes.inspect_bronze_payload(bronze, context)
    expected = (
        pa.Table.from_pylist(facts, schema=qes.FACT_SCHEMA),
        pa.Table.from_pylist(lineage, schema=qes.LINEAGE_SCHEMA),
        pa.Table.from_pylist(dispositions, schema=qes.DISPOSITION_SCHEMA),
    )
    counts = manifest.get("counts")
    _require(
        counts
        == {
            "normalized": expected[0].num_rows,
            "field_lineage": expected[1].num_rows,
            "inventoried_cells": expected[2].num_rows,
        }
    )
    declared_hashes = manifest.get("output_sha256")
    _require(isinstance(declared_hashes, dict) and set(declared_hashes) == _PRODUCTS)
    hashes = cast("dict[str, str]", declared_hashes)
    expected_by_name: dict[str, pa.Table] = dict(
        zip(
            ("qes_facts.parquet", "field_lineage.parquet", "cell_dispositions.parquet"),
            expected,
            strict=True,
        )
    )
    tables: dict[str, pa.Table] = {}
    for name in sorted(_PRODUCTS):
        expected_table = expected_by_name[name]
        path = silver_root / name
        _require(not path.is_symlink() and path.is_file())
        raw = path.read_bytes()
        _require(0 < len(raw) <= _MAX_PRODUCT_BYTES)
        _require(hashlib.sha256(raw).hexdigest() == hashes[name])
        observed = pq.read_table(path)
        _require(observed.schema.equals(expected_table.schema))
        _require(observed.to_pylist() == expected_table.to_pylist())
        tables[name] = expected_table
    return (
        tables["qes_facts.parquet"],
        tables["field_lineage.parquet"],
        tables["cell_dispositions.parquet"],
    )


def project_qes_earnings(
    silver_root: Path,
    manifest_sha256: str,
    cas_root: Path,
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Verify pinned Silver against Bronze and produce v2 canonical earnings."""
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
        bounds = _period_bounds(source["period_end"])
        token = source["source_number_token"]
        original_amount = Decimal(token.replace(",", ""))
        _require(source["amount"] == original_amount)
        precision = len(original_amount.as_tuple().digits)
        exponent = cast("int", original_amount.as_tuple().exponent)
        scale = max(0, -exponent)
        _require(1 <= precision <= _MAX_PRECISION and scale <= precision)
        row = {
            "record_id": identifier,
            "schema_version": "archive-govt-nz.health-recordsets/v2",
            "recordset": "earnings_fact",
            "domain": "health_appropriations",
            "source_object_sha256": source["source_object_sha256"],
            "source_observation_id": source["source_observation_id"],
            "source_locator": source["source_locator"],
            "source_vintage": source["source_vintage"],
            "valid_time_start": bounds[0],
            "valid_time_end": bounds[1],
            "valid_time_status": "source_quarter_ended",
            "period_token": source["period_end"].strftime("%Y.%m"),
            "observed_at": source["observed_at"],
            "observation_context": (
                "published_total_sector_ordinary_time_average_hourly_earnings"
            ),
            "rights_state": "not_evaluated",
            "quality_flags": list(source["quality_flags"]),
            "transformation_id": TRANSFORMATION,
            "lineage_id": hashlib.sha256(f"{identifier}\0lineage".encode()).hexdigest(),
            "source_record_id": source_id,
            "source_schema_version": source["schema_version"],
            "measure": source["measure"],
            "amount": original_amount,
            "value_token": token,
            "null_reason": None,
            "source_decimal_precision": precision,
            "source_decimal_scale": scale,
            "unit": "($) per paid hour",
            "currency": None,
            "price_basis": None,
            "base_period": None,
            "denominator_definition": None,
            "amount_type": "average_hourly_earnings",
            "source_label": "Average hourly earnings; Total sector; Ordinary time",
            "series_id": source["series_id"],
            "geography": None,
            "sector": source["sector"],
            "sex": source["sex"],
            "adjustment": source["adjustment"],
            "earnings_basis": source["earnings_basis"],
        }
        facts.append(row)
        links = lineage_by_record[source_id]
        direct = {
            "measure": "header_A3",
            "amount": "amount",
            "series_id": "series_id",
            "sector": "header_P6",
            "earnings_basis": "earnings_basis",
        }
        for field, source_field in direct.items():
            item = links[source_field]
            lineage.append(
                {
                    "target_record_id": identifier,
                    "field": field,
                    "source_coordinate": item["source_coordinate"],
                    "raw_value": item["raw_value"],
                    "normalized_value": str(row[field]),
                    "rule": TRANSFORMATION,
                }
            )
        year_link = links["source_year_token"]
        quarter_link = links["source_quarter_token"]
        period_link = links["period_token"]
        lineage.append(
            {
                "target_record_id": identifier,
                "field": "period_token",
                "source_coordinate": period_link["source_coordinate"],
                "raw_value": period_link["raw_value"],
                "normalized_value": row["period_token"],
                "rule": TRANSFORMATION,
            }
        )
        for field, value in (
            ("valid_time_start", bounds[0]),
            ("valid_time_end", bounds[1]),
        ):
            lineage.append(
                {
                    "target_record_id": identifier,
                    "field": field,
                    "source_coordinate": (
                        year_link["source_coordinate"]
                        + ";"
                        + quarter_link["source_coordinate"]
                    ),
                    "raw_value": json.dumps(
                        [year_link["raw_value"], quarter_link["raw_value"]],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                    "normalized_value": value.isoformat(),
                    "rule": TRANSFORMATION + "/quarter_bounds",
                }
            )
        unit_label = links["unit_label"]
        explanation = links["header_B49"]
        lineage.append(
            {
                "target_record_id": identifier,
                "field": "unit",
                "source_coordinate": unit_label["source_coordinate"]
                + ";"
                + explanation["source_coordinate"],
                "raw_value": unit_label["raw_value"] + ";" + explanation["raw_value"],
                "normalized_value": row["unit"],
                "rule": TRANSFORMATION + "/unit_composition",
            }
        )
        label_sources = (
            links["header_A3"],
            links["header_P6"],
            links["earnings_basis"],
        )
        lineage.append(
            {
                "target_record_id": identifier,
                "field": "source_label",
                "source_coordinate": ";".join(
                    item["source_coordinate"] for item in label_sources
                ),
                "raw_value": ";".join(item["raw_value"] for item in label_sources),
                "normalized_value": row["source_label"],
                "rule": TRANSFORMATION + "/label_composition",
            }
        )
        _require(
            json.loads(links["amount"]["normalized_value"])
            == source["source_number_token"]
        )
    canonical = pa.Table.from_pylist(
        facts, schema=recordset_schema("earnings_fact", version="v2")
    )
    canonical_lineage = pa.Table.from_pylist(
        lineage, schema=recordset_schema("field_lineage", version="v2")
    )
    return (
        canonical,
        canonical_lineage,
        {
            "schema_version": "archive-govt-nz.health-qes-canonical-projection/v1",
            "status": "verified_source_faithful_projection",
            "source_manifest_sha256": manifest_sha256,
            "source_object_sha256": SOURCE_SHA256,
            "source_vintage": SOURCE_VINTAGE,
            "input_records": source_facts.num_rows,
            "output_records": canonical.num_rows,
            "output_lineage_rows": canonical_lineage.num_rows,
            "input_identity_closed": True,
            "source_package_unchanged": True,
            "currency": "unknown",
            "sex": "not_supplied",
            "adjustment": "not_supplied",
            "deflator_selection": "not_performed",
            "rights_state": "not_evaluated",
            "publication": "not_performed",
        },
    )
