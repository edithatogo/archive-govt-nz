"""Bronze-bound canonical context projection for Stats NZ quarterly GDP."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import gdp
from archive_govt_nz.schemas.health_recordset_normalization import validate_table
from archive_govt_nz.schemas.health_recordsets import recordset_schema

SOURCE_SHA256 = "a7326e84e7704446a18e5c8942f99901a452b2170af4228e8a5c242a5532ed21"
SOURCE_LOCATOR = (
    "https://www.stats.govt.nz/assets/Uploads/Gross-domestic-product/"
    "Gross-domestic-product-March-2026-quarter/Download-data/"
    "gross-domestic-product-march-2026-quarter-current-price-income-and-expenditure.xlsx"
)
SOURCE_VINTAGE = "StatsNZ-GDP-2026Q1"
OBSERVED_AT = "2026-08-29T09:00:17Z"
SOURCE_MANIFEST_SHA256 = (
    "639b3c7da60f2afa1b860c5f6c8f1c4c0ae24bf17aa7af63bf8a06a1f6471b35"
)
TRANSFORMATION = "stats-nz-gdp-canonical-current-price-context/v1"
JUNE_SOURCE_SHA256 = "b6d2fe15b4656143f600abeb1849432f60d769570667eb90d07ddacd3498e22d"
JUNE_SOURCE_LOCATOR = (
    "https://www.stats.govt.nz/assets/Uploads/Gross-domestic-product/"
    "Gross-domestic-product-June-2026-quarter/Download-data/"
    "gross-domestic-product-june-2026-quarter-current-price-income-and-expenditure.xlsx"
)
JUNE_SOURCE_VINTAGE = "StatsNZ-GDP-2026Q2"
JUNE_OBSERVED_AT = "2026-09-29T21:28:10.739074Z"
JUNE_SOURCE_MANIFEST_SHA256 = (
    "f54b0ad605b54e480cd0623360159b3ce14b6a9f762185d5244dec89837ffbfd"
)
JUNE_SILVER_TRANSFORMATION = "stats-nz-gdp-current-price-expenditure-actual-2026q2/v1"
JUNE_TRANSFORMATION = "stats-nz-gdp-june-canonical-current-price-context/v1"
_PRODUCTS = {"gdp_facts.parquet", "field_lineage.parquet", "cell_dispositions.parquet"}
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ERROR = "gdp_canonical_projection_invalid"
_MAX_PRECISION = 38
_MAX_SCALE = 18


@dataclass(frozen=True)
class GdpProjectionProfile:
    """Bind one exact source vintage to its independent projection identity."""

    source_sha256: str
    source_locator: str
    source_vintage: str
    observed_at: str
    source_manifest_sha256: str
    silver_transformation: str
    canonical_transformation: str


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _verify_silver(
    silver_root: Path,
    manifest_sha256: str,
    bronze: Path,
    profile: GdpProjectionProfile,
) -> tuple[pa.Table, pa.Table]:
    _require(_DIGEST.fullmatch(manifest_sha256) is not None)
    _require(not silver_root.is_symlink() and silver_root.is_dir())
    marker = silver_root / "MANIFEST.json"
    _require(not marker.is_symlink() and marker.is_file())
    marker_bytes = marker.read_bytes()
    _require(
        hashlib.sha256(marker_bytes).hexdigest()
        == manifest_sha256
        == profile.source_manifest_sha256
    )
    manifest = json.loads(marker_bytes, object_pairs_hook=_pairs)
    _require(
        isinstance(manifest, dict)
        and manifest.get("schema_version") == "archive-govt-nz.health-gdp-extraction/v1"
        and manifest.get("transformation_id") == profile.silver_transformation
        and manifest.get("source_object_sha256") == profile.source_sha256
        and manifest.get("source_locator") == profile.source_locator
        and manifest.get("source_vintage") == profile.source_vintage
        and manifest.get("rights_state") == "not_evaluated"
        and manifest.get("currency") is None
        and manifest.get("status") == "passed"
        and {path.name for path in silver_root.iterdir()}
        == _PRODUCTS | {"MANIFEST.json"}
    )
    with tempfile.TemporaryDirectory(prefix="gdp-silver-verify-") as directory:
        rebuilt = Path(directory) / "silver"
        rebuilt_manifest = gdp.normalize_gdp(
            bronze,
            rebuilt,
            expected_sha256=profile.source_sha256,
            source_locator=profile.source_locator,
            source_vintage=profile.source_vintage,
            observed_at=profile.observed_at,
            dry_run=False,
        )
        _require(rebuilt_manifest == manifest)
        for name in _PRODUCTS:
            stored = silver_root / name
            _require(not stored.is_symlink() and stored.is_file())
            raw = stored.read_bytes()
            _require(hashlib.sha256(raw).hexdigest() == manifest["output_sha256"][name])
            _require(raw == (rebuilt / name).read_bytes())
        return (
            pq.read_table(rebuilt / "gdp_facts.parquet"),
            pq.read_table(rebuilt / "field_lineage.parquet"),
        )


def _lineage_row(
    source: dict[str, Any],
    target_id: str,
    values: dict[str, Any],
    transformation: str,
) -> dict[str, Any]:
    field = values["field"]
    coordinate = values["coordinate"]
    return {
        "record_id": "sha256:"
        + hashlib.sha256(f"{target_id}\0{field}\0{coordinate}".encode()).hexdigest(),
        "schema_version": "archive-govt-nz.health-recordsets/v1",
        "recordset": "field_lineage",
        "domain": "health_appropriations",
        "source_object_sha256": source["source_object_sha256"],
        "source_observation_id": source["source_observation_id"],
        "source_locator": source["source_locator"],
        "source_vintage": source["source_vintage"],
        "valid_time_start": values["valid_time_start"],
        "valid_time_end": source["period_end"],
        "valid_time_status": "source_quarter_ended",
        "period_token": source["period_token"],
        "observed_at": source["observed_at"],
        "observation_context": (
            "Stats NZ quarterly GDP expenditure; actual current prices"
        ),
        "rights_state": "not_evaluated",
        "quality_flags": list(source["quality_flags"]),
        "transformation_id": transformation,
        "lineage_id": hashlib.sha256(f"{target_id}\0lineage".encode()).hexdigest(),
        "source_record_id": source["record_id"],
        "source_schema_version": source["schema_version"],
        "target_record_id": target_id,
        "field": field,
        "source_coordinate": coordinate,
        "raw_value": values["raw_value"],
        "normalized_value": values["normalized_value"],
        "rule": values["rule"],
    }


def _canonicalize(
    facts: pa.Table, source_lineage: pa.Table, transformation: str
) -> tuple[pa.Table, pa.Table]:
    links: dict[str, dict[str, dict[str, Any]]] = {}
    for item in source_lineage.to_pylist():
        links.setdefault(item["record_id"], {})[item["field"]] = item
    canonical: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    for source in facts.to_pylist():
        source_id = source["record_id"]
        target_id = (
            "sha256:"
            + hashlib.sha256(f"{transformation}\0{source_id}".encode()).hexdigest()
        )
        amount = Decimal(source["source_number_token"])
        precision = len(amount.as_tuple().digits)
        scale = max(0, -cast("int", amount.as_tuple().exponent))
        _require(
            amount == source["amount"]
            and precision <= _MAX_PRECISION
            and scale <= _MAX_SCALE
        )
        period_end = source["period_end"]
        start_month = ((period_end.month - 1) // 3) * 3 + 1
        period_start = date(period_end.year, start_month, 1)
        fact = {
            "record_id": target_id,
            "schema_version": "archive-govt-nz.health-recordsets/v1",
            "recordset": "fiscal_context_fact",
            "domain": "health_appropriations",
            "source_object_sha256": source["source_object_sha256"],
            "source_observation_id": source["source_observation_id"],
            "source_locator": source["source_locator"],
            "source_vintage": source["source_vintage"],
            "valid_time_start": period_start,
            "valid_time_end": period_end,
            "valid_time_status": "source_quarter_ended",
            "period_token": source["period_token"],
            "observed_at": source["observed_at"],
            "observation_context": (
                "Stats NZ GDP expenditure measure; actual current prices"
            ),
            "rights_state": "not_evaluated",
            "quality_flags": sorted(
                set(source["quality_flags"])
                | {
                    "canonical_context_projection",
                    "currency_unresolved",
                    "denominator_not_selected",
                }
            ),
            "transformation_id": transformation,
            "lineage_id": hashlib.sha256(f"{target_id}\0lineage".encode()).hexdigest(),
            "source_record_id": source_id,
            "source_schema_version": source["schema_version"],
            "measure": "gross_domestic_product_expenditure_actual_current_prices",
            "amount": amount,
            "value_token": source["source_number_token"],
            "null_reason": None,
            "source_decimal_precision": precision,
            "source_decimal_scale": scale,
            "unit": source["unit"],
            "currency": None,
            "price_basis": "current_prices",
            "base_period": None,
            "denominator_definition": None,
            "amount_type": "economic_aggregate",
            "source_label": source["label"],
            "institutional_coverage": "whole_economy",
            "accounting_basis": "national_accounts_expenditure",
            "seasonal_adjustment": "actual_as_published_not_seasonally_adjusted",
        }
        canonical.append(fact)
        maps = (
            ("measure", "label", fact["measure"]),
            ("amount", "amount", str(amount)),
            ("period_token", "period_token", source["period_token"]),
            ("valid_time_start", "period_end", period_start.isoformat()),
            ("valid_time_end", "period_end", period_end.isoformat()),
            ("unit", "unit", source["unit"]),
            ("source_label", "label", source["label"]),
        )
        row_links = links[source_id]
        for field, source_field, normalized in maps:
            item = row_links[source_field]
            lineage.append(
                _lineage_row(
                    source,
                    target_id,
                    {
                        "field": field,
                        "coordinate": item["source_coordinate"],
                        "raw_value": item["raw_value"],
                        "normalized_value": normalized,
                        "valid_time_start": period_start,
                        "rule": transformation,
                    },
                    transformation,
                )
            )
    fact_table = pa.Table.from_pylist(
        canonical, schema=recordset_schema("fiscal_context_fact")
    )
    lineage_table = pa.Table.from_pylist(
        lineage, schema=recordset_schema("field_lineage")
    )
    validate_table("fiscal_context_fact", fact_table)
    validate_table("field_lineage", lineage_table)
    return fact_table, lineage_table


def _project_gdp(
    silver_root: Path,
    manifest_sha256: str,
    cas_root: Path,
    profile: GdpProjectionProfile,
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Verify GDP Bronze/Silver and retain unqualified fiscal context."""
    _require(not cas_root.is_symlink() and cas_root.is_dir())
    original = cas_root / profile.source_sha256[:2] / profile.source_sha256
    _require(not original.is_symlink() and not original.parent.is_symlink())
    facts, source_lineage = _verify_silver(
        silver_root,
        manifest_sha256,
        original,
        profile,
    )
    canonical, lineage = _canonicalize(
        facts, source_lineage, profile.canonical_transformation
    )
    return (
        canonical,
        lineage,
        {
            "schema_version": "archive-govt-nz.health-gdp-canonical-projection/v1",
            "status": "verified_source_faithful_projection",
            "source_object_sha256": profile.source_sha256,
            "source_locator": profile.source_locator,
            "source_vintage": profile.source_vintage,
            "source_manifest_sha256": manifest_sha256,
            "silver_transformation_id": profile.silver_transformation,
            "transformation_id": profile.canonical_transformation,
            "input_records": facts.num_rows,
            "output_records": canonical.num_rows,
            "lineage_records": lineage.num_rows,
            "currency": "unresolved",
            "rights_state": "not_evaluated",
            "denominator_selection": "not_performed",
            "inflation_adjustment": "not_performed",
        },
    )


def project_gdp(
    silver_root: Path, manifest_sha256: str, cas_root: Path
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Project the pinned March GDP vintage into unqualified fiscal context."""
    return _project_gdp(
        silver_root,
        manifest_sha256,
        cas_root,
        GdpProjectionProfile(
            source_sha256=SOURCE_SHA256,
            source_locator=SOURCE_LOCATOR,
            source_vintage=SOURCE_VINTAGE,
            observed_at=OBSERVED_AT,
            source_manifest_sha256=SOURCE_MANIFEST_SHA256,
            silver_transformation=gdp.TRANSFORMATION,
            canonical_transformation=TRANSFORMATION,
        ),
    )


def project_gdp_june(
    silver_root: Path, manifest_sha256: str, cas_root: Path
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Project the pinned June successor as its own unqualified vintage."""
    return _project_gdp(
        silver_root,
        manifest_sha256,
        cas_root,
        GdpProjectionProfile(
            source_sha256=JUNE_SOURCE_SHA256,
            source_locator=JUNE_SOURCE_LOCATOR,
            source_vintage=JUNE_SOURCE_VINTAGE,
            observed_at=JUNE_OBSERVED_AT,
            source_manifest_sha256=JUNE_SOURCE_MANIFEST_SHA256,
            silver_transformation=JUNE_SILVER_TRANSFORMATION,
            canonical_transformation=JUNE_TRANSFORMATION,
        ),
    )
