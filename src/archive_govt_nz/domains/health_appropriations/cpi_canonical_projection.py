"""Bronze-bound canonical projection for the pinned Stats NZ CPI series."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import cpi
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
    verified_snapshot,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from pathlib import Path

SOURCE_SHA256 = "f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d"
SOURCE_LOCATOR = (
    "https://www.stats.govt.nz/assets/Uploads/Consumers-price-index/"
    "Consumers-price-index-June-2026-quarter/Download-data/"
    "consumers-price-index-june-2026-quarter-index-numbers.csv"
)
SOURCE_VINTAGE = "Stats-NZ-CPI-2026-Q2"
OBSERVED_AT = "2026-08-29T09:00:17Z"
SOURCE_MANIFEST_SHA256 = (
    "edb62f4b106948502e717f5f6c5e3da00efc0a64bb10b5dcbafc48cd1a6c257e"
)
TRANSFORMATION = "cpi-canonical-source-faithful/v1"
_MANIFEST_SCHEMA = "archive-govt-nz.health-cpi-extraction/v1"
_PRODUCTS = {"cpi_facts.parquet", "field_lineage.parquet", "row_dispositions.parquet"}
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_MAX_MANIFEST_BYTES = 2 * 1024 * 1024
_MAX_PRODUCT_BYTES = 64 * 1024 * 1024
_MAX_DECIMAL_PRECISION = 38
_MAX_DECIMAL_SCALE = 18
_ERROR = "cpi_canonical_projection_invalid"


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
) -> tuple[pa.Table, pa.Table]:
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
        and manifest.get("transformation_id") == cpi.TRANSFORMATION
        and manifest.get("status") == "passed"
        and manifest.get("rights_state") == "not_evaluated"
        and manifest.get("source_object_sha256") == SOURCE_SHA256
        and manifest.get("source_locator") == SOURCE_LOCATOR
        and manifest.get("source_vintage") == SOURCE_VINTAGE
        and {path.name for path in silver_root.iterdir()}
        == _PRODUCTS | {"MANIFEST.json"}
    )
    _require(not cas_root.is_symlink() and cas_root.is_dir())
    original = cas_root / SOURCE_SHA256[:2] / SOURCE_SHA256
    _require(not original.parent.is_symlink() and not original.is_symlink())
    bronze = verified_snapshot(original, SOURCE_SHA256, max_bytes=cpi.MAX_BYTES)
    context = source_context(SOURCE_SHA256, SOURCE_LOCATOR, SOURCE_VINTAGE, OBSERVED_AT)
    facts, lineage, dispositions = cpi.inspect_bronze_payload(bronze, context)
    expected = {
        "cpi_facts.parquet": pa.Table.from_pylist(facts, schema=cpi.FACT_SCHEMA),
        "field_lineage.parquet": pa.Table.from_pylist(
            lineage, schema=cpi.LINEAGE_SCHEMA
        ),
        "row_dispositions.parquet": pa.Table.from_pylist(
            dispositions, schema=cpi.DISPOSITION_SCHEMA
        ),
    }
    _require(
        manifest.get("counts")
        == {
            "input": len(dispositions),
            "selected": len(facts),
            "numeric": sum(row["amount"] is not None for row in facts),
            "missing": sum(row["amount"] is None for row in facts),
            "unselected": len(dispositions) - len(facts),
        }
    )
    hashes = manifest.get("output_sha256")
    _require(isinstance(hashes, dict) and set(hashes) == _PRODUCTS)
    hashes = cast("dict[str, str]", hashes)
    for name, expected_table in expected.items():
        path = silver_root / name
        _require(not path.is_symlink() and path.is_file())
        raw = path.read_bytes()
        _require(0 < len(raw) <= _MAX_PRODUCT_BYTES)
        _require(hashlib.sha256(raw).hexdigest() == hashes[name])
        observed = pq.read_table(path)
        _require(observed.schema.equals(expected_table.schema))
        _require(observed.to_pylist() == expected_table.to_pylist())
    return expected["cpi_facts.parquet"], expected["field_lineage.parquet"]


def project_cpi(
    silver_root: Path, manifest_sha256: str, cas_root: Path
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Verify CPI Silver against Bronze and retain its unresolved index semantics."""
    source_facts, source_lineage = _source_tables(
        silver_root, manifest_sha256, cas_root
    )
    links: dict[str, dict[str, dict[str, Any]]] = {}
    for item in source_lineage.to_pylist():
        links.setdefault(item["record_id"], {})[item["field"]] = item
    facts: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    for source in source_facts.to_pylist():
        source_id = source["record_id"]
        identifier = (
            "sha256:"
            + hashlib.sha256(f"{TRANSFORMATION}\0{source_id}".encode()).hexdigest()
        )
        amount = source["amount"]
        precision = scale = None
        if amount is not None:
            amount = Decimal(source["value_token"])
            precision = len(amount.as_tuple().digits)
            scale = max(0, -cast("int", amount.as_tuple().exponent))
            _require(
                source["amount"] == amount
                and precision <= _MAX_DECIMAL_PRECISION
                and scale <= _MAX_DECIMAL_SCALE
            )
        period_end = source["period_end"]
        quarter_start_month = ((period_end.month - 1) // 3) * 3 + 1
        row = {
            "record_id": identifier,
            "schema_version": "archive-govt-nz.health-recordsets/v1",
            "recordset": "price_population_fact",
            "domain": "health_appropriations",
            "source_object_sha256": source["source_object_sha256"],
            "source_observation_id": source["source_observation_id"],
            "source_locator": source["source_locator"],
            "source_vintage": source["source_vintage"],
            "valid_time_start": date(period_end.year, quarter_start_month, 1),
            "valid_time_end": period_end,
            "valid_time_status": "source_quarter_ended",
            "period_token": source["period_token"],
            "observed_at": source["observed_at"],
            "observation_context": "CPI All Groups for New Zealand; household prices",
            "rights_state": "not_evaluated",
            "quality_flags": list(source["quality_flags"]),
            "transformation_id": TRANSFORMATION,
            "lineage_id": hashlib.sha256(f"{identifier}\0lineage".encode()).hexdigest(),
            "source_record_id": source_id,
            "source_schema_version": source["schema_version"],
            "measure": "consumer_price_index_all_groups",
            "amount": amount,
            "value_token": source["value_token"],
            "null_reason": source["missing_reason"],
            "source_decimal_precision": precision,
            "source_decimal_scale": scale,
            "unit": "Index",
            "currency": None,
            "price_basis": None,
            "base_period": source["index_base"],
            "denominator_definition": None,
            "amount_type": "price_index",
            "source_label": "CPI All Groups for New Zealand; All groups",
            "series_id": source["series_reference"],
            "geography": "New Zealand",
            "population_definition": None,
            "seasonal_adjustment": None,
        }
        facts.append(row)
        for field, source_field in (
            ("period_token", "period_end"),
            ("amount", "amount"),
            ("measure", "series_reference"),
            ("series_id", "series_reference"),
            ("unit", "unit"),
        ):
            item = links[source_id][source_field]
            value = row[field]
            lineage.append(
                {
                    "target_record_id": identifier,
                    "field": field,
                    "source_coordinate": item["source_coordinate"],
                    "raw_value": item["raw_value"],
                    "normalized_value": str(value) if value is not None else None,
                    "rule": TRANSFORMATION,
                }
            )
        for field, value in (
            ("valid_time_start", row["valid_time_start"]),
            ("valid_time_end", row["valid_time_end"]),
        ):
            item = links[source_id]["period_end"]
            lineage.append(
                {
                    "target_record_id": identifier,
                    "field": field,
                    "source_coordinate": item["source_coordinate"],
                    "raw_value": item["raw_value"],
                    "normalized_value": value.isoformat(),
                    "rule": "calendar_quarter_bounds_from_source_period",
                }
            )
    fact_table = pa.Table.from_pylist(
        facts, schema=recordset_schema("price_population_fact")
    )
    lineage_table = pa.Table.from_pylist(
        lineage, schema=recordset_schema("field_lineage")
    )
    receipt = {
        "schema_version": "archive-govt-nz.health-cpi-canonical-projection/v1",
        "status": "verified_source_faithful_projection",
        "source_object_sha256": SOURCE_SHA256,
        "source_manifest_sha256": manifest_sha256,
        "source_records": source_facts.num_rows,
        "output_records": fact_table.num_rows,
        "lineage_records": lineage_table.num_rows,
        "rights_state": "not_evaluated",
        "index_base": "unverified",
        "inflation_adjustment": "not_performed",
    }
    return fact_table, lineage_table, receipt
