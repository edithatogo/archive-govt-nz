"""Manifest-driven original-workbook rebuilds, separate from publication.

Complete runs can be reused only after full fixity checks. Incomplete runs are
preserved; retry in a new directory. Fixity is not a signature or rights grant.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.budget import (
    normalize_budget_workbook,
)
from archive_govt_nz.domains.health_appropriations.forecast import (
    normalize_forecast_workbook,
)
from archive_govt_nz.domains.health_appropriations.historical import (
    normalize_historical_workbook,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    source_context,
    verified_snapshot,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path

_SCHEMA = "archive-govt-nz.health-raw-rebuild/v1"
_MAX_MANIFEST_BYTES = 4 * 1024 * 1024


@dataclass(frozen=True)
class SourceProfile:
    """Versioned source selection and expected derivative file contract."""

    filename: str
    vintage: str
    schema: str
    outputs: tuple[str, str, str]


PROFILES = {
    "budget": SourceProfile(
        "b25-expenditure-data.xlsx",
        "Budget-2025",
        "archive-govt-nz.health-budget-extraction/v1",
        ("budget_facts.parquet", "field_lineage.parquet", "row_dispositions.parquet"),
    ),
    "befu": SourceProfile(
        "befu25-data-expense-tables.xlsx",
        "BEFU-2025",
        "archive-govt-nz.health-forecast-extraction/v1",
        (
            "forecast_facts.parquet",
            "field_lineage.parquet",
            "cell_dispositions.parquet",
        ),
    ),
    "hyefu": SourceProfile(
        "hyefu24-data-expense-tables.xlsx",
        "HYEFU-2024",
        "archive-govt-nz.health-forecast-extraction/v1",
        (
            "forecast_facts.parquet",
            "field_lineage.parquet",
            "cell_dispositions.parquet",
        ),
    ),
    "historical": SourceProfile(
        "fiscaltimeseries1972-2024.xlsx",
        "fiscal-2024",
        "archive-govt-nz.health-historical-extraction/v1",
        (
            "historical_facts.parquet",
            "field_lineage.parquet",
            "cell_dispositions.parquet",
        ),
    ),
}


def _unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            message = "duplicate_manifest_key"
            raise ValueError(message)
        result[key] = value
    return result


def _json(payload: bytes) -> dict[str, Any]:
    result = json.loads(payload, object_pairs_hook=_unique_pairs)
    if not isinstance(result, dict):
        msg = "invalid_manifest"
        raise TypeError(msg)
    return result


def _hash(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        msg = "invalid_output_file"
        raise ValueError(msg)
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def _read(path: Path) -> dict[str, Any]:
    if path.is_symlink():
        msg = "invalid_output_file"
        raise ValueError(msg)
    with path.open("rb") as handle:
        payload = handle.read(_MAX_MANIFEST_BYTES + 1)
    if len(payload) > _MAX_MANIFEST_BYTES:
        msg = "manifest_byte_limit"
        raise ValueError(msg)
    return _json(payload)


def _write(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(encode_json(value) + "\n")


def plan_rebuild(
    donor_manifest: Path,
    store_root: Path,
    manifest_sha256: str,
    observed_at: str,
) -> dict[str, Any]:
    """Verify pinned manifest and every original without writing archive state."""
    context = source_context(manifest_sha256, "donor-manifest", "v1", observed_at)
    donor = _json(
        verified_snapshot(
            donor_manifest, manifest_sha256, max_bytes=_MAX_MANIFEST_BYTES
        )
    )
    if donor.get("schema_version") != "archive-govt-nz.health-donor-manifest/v1":
        msg = "invalid_donor_schema"
        raise ValueError(msg)
    rows = donor.get("objects")
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        msg = "invalid_donor_objects"
        raise ValueError(msg)
    sources = {}
    store = ContentAddressedStore(store_root, create=False)
    for name, profile in PROFILES.items():
        locator = "data/raw/" + profile.filename
        matches = [row for row in rows if row.get("path") == locator]
        if len(matches) != 1 or not isinstance(matches[0].get("object_id"), str):
            msg = "missing_or_ambiguous_source"
            raise ValueError(msg)
        receipt = store.verify(matches[0]["object_id"])
        sources[name] = {
            "object_id": receipt.object_id,
            "sha256": receipt.sha256,
            "locator": locator,
            "vintage": profile.vintage,
        }
    return {
        "schema_version": _SCHEMA,
        "donor_manifest_sha256": manifest_sha256,
        "observed_at": context["observed_at"].isoformat(),
        "sources": sources,
    }


def _verify_plan(plan: dict[str, Any], store_root: Path) -> dict[str, Path]:
    if (
        set(plan)
        != {"schema_version", "donor_manifest_sha256", "observed_at", "sources"}
        or plan["schema_version"] != _SCHEMA
        or not isinstance(plan["sources"], dict)
        or set(plan["sources"]) != set(PROFILES)
    ):
        msg = "invalid_rebuild_plan"
        raise ValueError(msg)
    source_context(
        plan["donor_manifest_sha256"], "donor-manifest", "v1", plan["observed_at"]
    )
    store = ContentAddressedStore(store_root, create=False)
    paths = {}
    for name, profile in PROFILES.items():
        source = plan["sources"][name]
        if (
            not isinstance(source, dict)
            or set(source) != {"object_id", "sha256", "locator", "vintage"}
            or source["locator"] != "data/raw/" + profile.filename
            or source["vintage"] != profile.vintage
            or not isinstance(source["sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", source["sha256"]) is None
            or source["object_id"] != "sha256:" + source["sha256"]
        ):
            msg = "invalid_rebuild_source"
            raise ValueError(msg)
        paths[name] = store.verify(source["object_id"]).path
    return paths


def _stage_receipt(root: Path, name: str, plan: dict[str, Any]) -> str:
    stage = root / name
    if stage.is_symlink():
        msg = "invalid_stage_directory"
        raise ValueError(msg)
    manifest = stage / "MANIFEST.json"
    receipt = _read(manifest)
    profile = PROFILES[name]
    source = plan["sources"][name]
    expected = {
        "schema_version": profile.schema,
        "status": "passed",
        "source_object_sha256": source["sha256"],
        "source_locator": source["locator"],
        "source_vintage": source["vintage"],
        "observed_at": plan["observed_at"],
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        msg = "invalid_stage_receipt"
        raise ValueError(msg)
    hashes = receipt.get("output_sha256")
    if not isinstance(hashes, dict) or set(hashes) != set(profile.outputs):
        msg = "invalid_stage_outputs"
        raise ValueError(msg)
    if {path.name for path in stage.iterdir()} != {*profile.outputs, "MANIFEST.json"}:
        msg = "unexpected_stage_files"
        raise ValueError(msg)
    for filename, digest in hashes.items():
        if _hash(stage / filename) != digest:
            msg = "output_hash_mismatch"
            raise ValueError(msg)
    return _hash(manifest)


def _completion(root: Path, plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": _SCHEMA,
        "status": "passed",
        "plan_sha256": hashlib.sha256(encode_json(plan).encode()).hexdigest(),
        "stages": {name: _stage_receipt(root, name, plan) for name in PROFILES},
        "publication_state": "local_validation_only",
    }


def _extract(name: str, path: Path, root: Path, plan: dict[str, Any]) -> None:
    source = plan["sources"][name]
    context = {
        "expected_sha256": source["sha256"],
        "observed_at": plan["observed_at"],
        "source_locator": source["locator"],
        "source_vintage": source["vintage"],
    }
    if name == "budget":
        normalize_budget_workbook(path, root / name, **context)
    elif name == "historical":
        normalize_historical_workbook(path, root / name, **context)
    else:
        normalize_forecast_workbook(path, root / name, profile=name, **context)


def _verified_existing(output_dir: Path, plan: dict[str, Any]) -> dict[str, Any]:
    if not (output_dir / "MANIFEST.json").is_file():
        msg = "incomplete_run_use_new_directory"
        raise ValueError(msg)
    if {path.name for path in output_dir.iterdir()} != {
        *PROFILES,
        "PLAN.json",
        "MANIFEST.json",
    }:
        message = "unexpected_run_files"
        raise ValueError(message)
    if _read(output_dir / "PLAN.json") != plan:
        msg = "run_plan_mismatch"
        raise ValueError(msg)
    completion = _completion(output_dir, plan)
    if _read(output_dir / "MANIFEST.json") != completion:
        msg = "run_manifest_mismatch"
        raise ValueError(msg)
    return completion


def _verify_pinned_run(
    output_dir: Path, store_root: Path, manifest_sha256: str
) -> dict[str, Any]:
    if output_dir.is_symlink():
        message = "invalid_run_directory"
        raise ValueError(message)
    manifest = output_dir / "MANIFEST.json"
    if _hash(manifest) != manifest_sha256:
        message = "run_manifest_hash_mismatch"
        raise ValueError(message)
    plan = _read(output_dir / "PLAN.json")
    _verify_plan(plan, store_root)
    result = _verified_existing(output_dir, plan)
    if _hash(manifest) != manifest_sha256:
        message = "run_manifest_changed_during_verification"
        raise ValueError(message)
    return result


def verify_rebuild(
    output_dir: Path, store_root: Path, manifest_sha256: str
) -> dict[str, Any]:
    """Verify a hash-pinned completed run without ever creating archive state."""
    try:
        result = _verify_pinned_run(output_dir, store_root, manifest_sha256)
    except Exception as error:  # noqa: BLE001 - read-only protocol redaction boundary
        message = "raw_run_verification_failed:" + type(error).__name__
        raise ValueError(message) from None
    else:
        return result


def execute_rebuild(
    plan: dict[str, Any], store_root: Path, output_dir: Path
) -> dict[str, Any]:
    """Build originals into a new local run, or verify an identical complete run."""
    paths = _verify_plan(plan, store_root)
    if output_dir.resolve().is_relative_to(store_root.resolve()):
        message = "output_inside_bronze_store"
        raise ValueError(message)
    if output_dir.is_symlink():
        msg = "invalid_run_directory"
        raise ValueError(msg)
    if output_dir.exists():
        return _verified_existing(output_dir, plan)
    output_dir.mkdir(parents=True, exist_ok=False)
    _write(output_dir / "PLAN.json", plan)
    for name, path in paths.items():
        try:
            _extract(name, path, output_dir, plan)
            _stage_receipt(output_dir, name, plan)
        except Exception as error:  # noqa: BLE001 - redacted adapter failure boundary
            # Adapter boundary: retain failure evidence without leaking source
            # diagnostics; re-raise a stable failure, never swallow the error.
            _write(
                output_dir / "FAILURE.json",
                {
                    "schema_version": _SCHEMA,
                    "status": "failed",
                    "stage": name,
                    "error_class": type(error).__name__,
                },
            )
            raise ValueError("stage_failed:" + name) from None
    result = _completion(output_dir, plan)
    _write(output_dir / "MANIFEST.json", result)
    return result
