"""Verified local Gold projection of the bounded HAIR2024 CSV profiles."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import moh_indicators
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA

if TYPE_CHECKING:
    from pathlib import Path

MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_PRODUCT_BYTES = 16 * 1024 * 1024
MAX_PACKAGE_BYTES = 64 * 1024 * 1024
SOURCE_VINTAGE = "MoH-HAIR-2024"
OBSERVED_AT = "2026-08-29T09:00:17+00:00"
PROFILES = {
    "fig27/v1": "https://www.health.govt.nz/system/files/2025-08/hair2024-fig27.csv",
    "fig28/v1": "https://www.health.govt.nz/system/files/2025-08/hair2024-fig28.csv",
}
PRODUCTS = {
    "moh_indicator_facts.parquet",
    "field_lineage.parquet",
    "row_dispositions.parquet",
}
_DIGEST = re.compile(r"^[0-9a-f]{64}$")
_ERROR = "moh_canonical_projection_invalid"
_EXPECTED_COUNTS = {"input": 20, "facts": 40, "lineage": 120}


@dataclass(frozen=True)
class MohIndicatorInput:
    """Caller-pinned Silver package and its exact Bronze source identity."""

    profile: str
    root: Path
    manifest_sha256: str
    source_sha256: str


@dataclass(frozen=True)
class MohGoldInput:
    """The two required HAIR2024 profiles plus the immutable Bronze CAS root."""

    packages: tuple[MohIndicatorInput, ...]
    source_cas_root: Path


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _digest_file(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def _read_profile(
    item: MohIndicatorInput, source_cas_root: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    _require(item.profile in PROFILES)
    _require(
        _DIGEST.fullmatch(item.manifest_sha256) is not None
        and _DIGEST.fullmatch(item.source_sha256) is not None
    )
    root = item.root
    _require(not root.is_symlink() and root.is_dir())
    manifest_path = root / "MANIFEST.json"
    _require(not manifest_path.is_symlink() and manifest_path.is_file())
    _require(manifest_path.stat().st_size <= MAX_MANIFEST_BYTES)
    manifest_bytes = manifest_path.read_bytes()
    _require(
        len(manifest_bytes) <= MAX_MANIFEST_BYTES
        and hashlib.sha256(manifest_bytes).hexdigest() == item.manifest_sha256
    )
    manifest = json.loads(manifest_bytes, object_pairs_hook=_pairs)
    locator = PROFILES[item.profile]
    _require(
        manifest.get("schema_version")
        == "archive-govt-nz.health-moh-indicator-extraction/v1"
        and manifest.get("transformation_id") == moh_indicators.TRANSFORMATION
        and manifest.get("status") == "passed"
        and manifest.get("profile") == item.profile
        and manifest.get("source_object_sha256") == item.source_sha256
        and manifest.get("source_locator") == locator
        and manifest.get("source_vintage") == SOURCE_VINTAGE
        and manifest.get("observed_at") == OBSERVED_AT
        and manifest.get("rights_state") == "not_evaluated"
    )
    _require({path.name for path in root.iterdir()} == PRODUCTS | {"MANIFEST.json"})
    source_path = source_cas_root / item.source_sha256[:2] / item.source_sha256
    _require(
        not source_cas_root.is_symlink()
        and source_cas_root.is_dir()
        and not source_path.parent.is_symlink()
        and not source_path.is_symlink()
        and source_path.is_file()
    )
    source_digest = _digest_file(source_path)
    _require(source_digest == item.source_sha256)
    declared = manifest.get("output_sha256")
    _require(isinstance(declared, dict) and set(declared) == PRODUCTS)
    package_bytes = len(manifest_bytes) + source_path.stat().st_size
    tables: dict[str, pa.Table] = {}
    for name, schema in (
        ("moh_indicator_facts.parquet", moh_indicators.FACT_SCHEMA),
        ("field_lineage.parquet", LINEAGE_SCHEMA),
        ("row_dispositions.parquet", moh_indicators.DISPOSITION_SCHEMA),
    ):
        path = root / name
        _require(not path.is_symlink() and path.is_file())
        size = path.stat().st_size
        package_bytes += size
        _require(0 < size <= MAX_PRODUCT_BYTES)
        digest = _digest_file(path)
        _require(digest == declared[name])
        table = pq.read_table(path)
        _require(table.schema.equals(schema))
        tables[name] = table
    _require(package_bytes <= MAX_PACKAGE_BYTES)
    facts = tables["moh_indicator_facts.parquet"].to_pylist()
    lineage = tables["field_lineage.parquet"].to_pylist()
    dispositions = tables["row_dispositions.parquet"].to_pylist()
    _require(
        manifest.get("counts") == _EXPECTED_COUNTS
        and len(facts) == _EXPECTED_COUNTS["facts"]
        and len(lineage) == _EXPECTED_COUNTS["lineage"]
        and len(dispositions) == _EXPECTED_COUNTS["input"]
    )
    record_ids = {row["record_id"] for row in facts}
    _require(len(record_ids) == _EXPECTED_COUNTS["facts"])
    _require(
        all(
            row["source_object_sha256"] == item.source_sha256
            and row["source_locator"] == locator
            and row["source_vintage"] == SOURCE_VINTAGE
            and row["profile"] == item.profile
            and row["rights_state"] == "not_evaluated"
            and row["unit"] is None
            and row["price_base"] is None
            and row["denominator"] is None
            and row["period_start"] is None
            and row["period_end"] is None
            for row in facts
        )
    )
    _require(
        {row["period_token"] for row in facts} == moh_indicators.PERIODS
        and {row["record_id"] for row in lineage} == record_ids
        and all(row["source_object_sha256"] == item.source_sha256 for row in lineage)
    )
    return (
        facts,
        lineage,
        {
            "profile": item.profile,
            "source_sha256": item.source_sha256,
            "silver_manifest_sha256": item.manifest_sha256,
            "fact_count": len(facts),
            "lineage_count": len(lineage),
            "disposition_count": len(dispositions),
            "rights_state": "not_evaluated",
        },
    )


def project_moh_indicators(
    source: MohGoldInput,
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Read two caller-pinned, source-bound profiles without measure derivation."""
    try:
        _require(isinstance(source, MohGoldInput))
        _require(
            isinstance(source.packages, tuple)
            and len(source.packages) == len(PROFILES)
            and all(isinstance(item, MohIndicatorInput) for item in source.packages)
            and {item.profile for item in source.packages} == set(PROFILES)
            and not source.source_cas_root.is_symlink()
            and source.source_cas_root.is_dir()
        )
        facts: list[dict[str, Any]] = []
        lineage: list[dict[str, Any]] = []
        profiles = []
        for item in sorted(source.packages, key=lambda value: value.profile):
            profile_facts, profile_lineage, evidence = _read_profile(
                item, source.source_cas_root
            )
            facts.extend(profile_facts)
            lineage.extend(profile_lineage)
            profiles.append(evidence)
        return (
            pa.Table.from_pylist(facts, schema=moh_indicators.FACT_SCHEMA),
            pa.Table.from_pylist(lineage, schema=LINEAGE_SCHEMA),
            {
                "schema_version": "archive-govt-nz.health-moh-canonical-projection/v1",
                "status": "verified_source_faithful_projection",
                "profiles": profiles,
                "input_records": len(facts),
                "aggregation": "none_published_indicator_rows_preserved",
                "actual_expenditure": "not_asserted",
                "rights_state": "not_evaluated",
                "cross_source_join": "not_performed",
                "vintage_pooling": "not_performed",
            },
        )
    except (
        OSError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        pa.ArrowException,
    ):
        raise ValueError(_ERROR) from None
