"""Bronze-bound canonical projection for the pinned annual population profile."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.population_annual_silver import (
    TRANSFORMATION as SILVER_TRANSFORMATION,
)
from archive_govt_nz.domains.health_appropriations.population_annual_silver import (
    normalize_population_annual,
)
from archive_govt_nz.schemas.health_recordset_normalization import validate_table
from archive_govt_nz.schemas.health_recordsets import recordset_schema

SOURCE_SHA256 = "a52e0344d1b6e707de04b7b968f2667fc969c0f0777b319921ff716ead82a1d9"
SOURCE_LOCATOR = "https://infoshare.stats.govt.nz/ExportDirect.aspx"
SOURCE_VINTAGE = "2026-08-18"
OBSERVED_AT = "2026-09-25T09:37:50Z"
SOURCE_MANIFEST_SHA256 = (
    "067255c4ac18377312d0a8234dc94804c876ba68866cfba3a483a4dd89415798"
)
TRANSFORMATION = "population-annual-canonical-source-faithful/v1"
_PRODUCTS = {
    "population_facts.parquet",
    "field_lineage.parquet",
    "row_dispositions.parquet",
}
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ERROR = "population_annual_canonical_projection_invalid"


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _lineage(
    source: dict[str, Any], target_id: str, values: dict[str, Any]
) -> dict[str, Any]:
    field = values["field"]
    coordinate = values["coordinate"]
    lineage_id = hashlib.sha256(f"{target_id}\0lineage".encode()).hexdigest()
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
        "valid_time_start": source["valid_time_start"],
        "valid_time_end": source["valid_time_end"],
        "valid_time_status": source["valid_time_status"],
        "period_token": source["period_token"],
        "observed_at": source["observed_at"],
        "observation_context": source["observation_context"],
        "rights_state": source["rights_state"],
        "quality_flags": list(source["quality_flags"]),
        "transformation_id": TRANSFORMATION,
        "lineage_id": lineage_id,
        "source_record_id": source["record_id"],
        "source_schema_version": source["schema_version"],
        "target_record_id": target_id,
        "field": field,
        "source_coordinate": coordinate,
        "raw_value": values["raw_value"],
        "normalized_value": values["normalized_value"],
        "rule": values["rule"],
    }


def _verified_silver(silver_root: Path, manifest_sha256: str, bronze: Path) -> pa.Table:
    _require(_DIGEST.fullmatch(manifest_sha256) is not None)
    _require(not silver_root.is_symlink() and silver_root.is_dir())
    marker = silver_root / "MANIFEST.json"
    _require(not marker.is_symlink() and marker.is_file())
    payload = marker.read_bytes()
    _require(
        hashlib.sha256(payload).hexdigest() == manifest_sha256 == SOURCE_MANIFEST_SHA256
    )
    manifest = json.loads(payload, object_pairs_hook=_pairs)
    _require(
        isinstance(manifest, dict)
        and manifest.get("schema_version")
        == "archive-govt-nz.health-population-annual-extraction/v1"
        and manifest.get("transformation_id") == SILVER_TRANSFORMATION
        and manifest.get("status") == "passed"
        and manifest.get("source_object_sha256") == SOURCE_SHA256
        and manifest.get("source_locator") == SOURCE_LOCATOR
        and manifest.get("source_vintage") == SOURCE_VINTAGE
        and manifest.get("rights_state") == "not_evaluated"
        and manifest.get("analytical_selection") == "not_selected"
        and {path.name for path in silver_root.iterdir()}
        == _PRODUCTS | {"MANIFEST.json"}
    )
    with tempfile.TemporaryDirectory(prefix="population-silver-verify-") as directory:
        rebuilt = Path(directory) / "silver"
        rebuilt_manifest = normalize_population_annual(
            bronze,
            rebuilt,
            expected_sha256=SOURCE_SHA256,
            observed_at=OBSERVED_AT,
            source_vintage=SOURCE_VINTAGE,
            source_locator=SOURCE_LOCATOR,
            dry_run=False,
        )
        _require(rebuilt_manifest == manifest)
        for name in _PRODUCTS:
            stored = silver_root / name
            _require(not stored.is_symlink() and stored.is_file())
            raw = stored.read_bytes()
            _require(hashlib.sha256(raw).hexdigest() == manifest["output_sha256"][name])
            _require(raw == (rebuilt / name).read_bytes())
        return pq.read_table(rebuilt / "population_facts.parquet")


def _canonicalize(facts: pa.Table) -> tuple[pa.Table, pa.Table]:
    canonical: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    for source in facts.to_pylist():
        target_id = (
            "sha256:"
            + hashlib.sha256(
                f"{TRANSFORMATION}\0{source['record_id']}".encode()
            ).hexdigest()
        )
        amount = source["amount"]
        precision = len(str(abs(int(amount)))) if amount is not None else None
        row = {
            **source,
            "record_id": target_id,
            "recordset": "price_population_fact",
            "transformation_id": TRANSFORMATION,
            "lineage_id": hashlib.sha256(f"{target_id}\0lineage".encode()).hexdigest(),
            "source_record_id": source["record_id"],
            "source_decimal_precision": precision,
            "source_decimal_scale": 0 if amount is not None else None,
            "quality_flags": sorted(
                set(source["quality_flags"]) | {"canonical_context_projection"}
            ),
        }
        canonical.append(row)
        year = int(source["period_token"][2:])
        source_row = year - 1991 + 5
        for field, column, raw_value, normalized in (
            ("period_token", "A", source["period_token"], source["period_token"]),
            (
                "amount",
                "B",
                source["value_token"],
                str(source["amount"]) if source["amount"] is not None else None,
            ),
            ("source_label", "header", "Total All Ages", source["source_label"]),
        ):
            coordinate = f"csv:row={source_row};column={column}"
            if column == "header":
                coordinate = "csv:row=4;column=C"
            lineage.append(
                _lineage(
                    source,
                    target_id,
                    {
                        "field": field,
                        "coordinate": coordinate,
                        "raw_value": raw_value,
                        "normalized_value": normalized,
                        "rule": TRANSFORMATION,
                    },
                )
            )
    canonical_table = pa.Table.from_pylist(
        canonical, schema=recordset_schema("price_population_fact")
    )
    lineage_table = pa.Table.from_pylist(
        lineage, schema=recordset_schema("field_lineage")
    )
    validate_table("price_population_fact", canonical_table)
    validate_table("field_lineage", lineage_table)
    return canonical_table, lineage_table


def project_population_annual(
    silver_root: Path, manifest_sha256: str, cas_root: Path
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Verify the pinned Bronze/Silver source and map facts to canonical context."""
    _require(not cas_root.is_symlink() and cas_root.is_dir())
    original = cas_root / SOURCE_SHA256[:2] / SOURCE_SHA256
    _require(not original.is_symlink() and not original.parent.is_symlink())
    facts = _verified_silver(silver_root, manifest_sha256, original)
    canonical_table, lineage_table = _canonicalize(facts)
    receipt = {
        "schema_version": "archive-govt-nz.health-population-canonical-projection/v1",
        "status": "verified_source_faithful_projection",
        "source_object_sha256": SOURCE_SHA256,
        "source_manifest_sha256": manifest_sha256,
        "input_records": facts.num_rows,
        "output_records": canonical_table.num_rows,
        "lineage_records": lineage_table.num_rows,
        "rights_state": "not_evaluated",
        "analytical_selection": "not_selected",
        "denominator_approval": "not_selected",
    }
    return canonical_table, lineage_table, receipt
