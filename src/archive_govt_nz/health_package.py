"""Deterministic preparation of eligibility-gated health preservation packages."""
# pyright: reportMissingTypeStubs=false, reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false

from __future__ import annotations

import hashlib
import json
import shutil
from typing import TYPE_CHECKING, Any, NoReturn, cast

import blake3
import pyarrow as pa
import pyarrow.parquet as pq

if TYPE_CHECKING:
    from pathlib import Path


class HealthPackageError(ValueError):
    """Fail-closed package preparation error with a stable class."""


def _fail(error_class: str) -> NoReturn:
    raise HealthPackageError(error_class)


def _canonical_json(document: object) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def _classification_by_dataset(document: dict[str, Any]) -> dict[str, dict[str, Any]]:
    records = document.get("records")
    if not isinstance(records, list):
        _fail("invalid_classification_records")
    indexed: dict[str, dict[str, Any]] = {}
    for raw in cast("list[object]", records):
        if not isinstance(raw, dict) or not isinstance(raw.get("dataset_id"), str):
            _fail("invalid_classification_record")
        record = cast("dict[str, Any]", raw)
        identifier = cast("str", record["dataset_id"])
        if identifier in indexed:
            _fail("duplicate_dataset_classification")
        indexed[identifier] = record
    return indexed


def _hash_receipt(path: Path, root: Path, role: str) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "path": path.relative_to(root).as_posix(),
        "role": role,
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "blake3": blake3.blake3(payload).hexdigest(),
    }


def prepare_health_package(  # noqa: C901, PLR0915
    resource_metadata_path: Path,
    classification_path: Path,
    output_dir: Path,
) -> dict[str, object]:
    """Prepare, but never publish, a resource-level health archive package."""
    metadata = cast(
        "dict[str, Any]", json.loads(resource_metadata_path.read_text(encoding="utf-8"))
    )
    classifications = cast(
        "dict[str, Any]", json.loads(classification_path.read_text(encoding="utf-8"))
    )
    resources = metadata.get("resources")
    if not isinstance(resources, list):
        _fail("invalid_resource_metadata")
    indexed = _classification_by_dataset(classifications)
    normalized: list[dict[str, Any]] = []
    capture_outcomes: list[dict[str, object]] = []
    tombstones: list[dict[str, object]] = []
    seen: set[str] = set()
    for raw in cast("list[object]", resources):
        if not isinstance(raw, dict):
            _fail("invalid_resource_record")
        resource = cast("dict[str, Any]", raw)
        resource_id = resource.get("resource_id")
        dataset_id = resource.get("dataset_id")
        if not isinstance(resource_id, str) or not isinstance(dataset_id, str):
            _fail("invalid_resource_identifier")
        if resource_id in seen:
            _fail("duplicate_resource")
        seen.add(resource_id)
        classification = indexed.get(dataset_id)
        if classification is None:
            _fail("missing_dataset_classification")
        authorized = (
            classification.get("classification") == "eligible"
            and classification.get("download_authorized") is True
        )
        disposition = "eligible" if authorized else "restricted"
        reason = (
            "eligible_resource_receipt" if authorized else "resource_rights_unknown"
        )
        row = {
            **resource,
            "classification": classification.get("classification"),
            "download_authorized": authorized,
            "disposition": disposition,
            "reason": reason,
        }
        normalized.append(row)
        capture_outcomes.append(
            {
                "resource_id": resource_id,
                "source_url": resource.get("url"),
                "decision": {
                    "disposition": disposition,
                    "reason": reason,
                    "declared_size": resource.get("size"),
                },
            }
        )
        if not authorized:
            tombstones.append(
                {
                    "dataset_id": dataset_id,
                    "resource_id": resource_id,
                    "state": "rights-restricted",
                    "reason": reason,
                    "source_url": resource.get("url"),
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    source_dir = output_dir / "source"
    source_dir.mkdir(exist_ok=True)
    metadata_copy = source_dir / "moh-resource-metadata.json"
    classification_copy = source_dir / "moh-classification.json"
    shutil.copyfile(resource_metadata_path, metadata_copy)
    shutil.copyfile(classification_path, classification_copy)
    resources_jsonl = output_dir / "resources.jsonl"
    resources_jsonl.write_bytes(b"".join(_canonical_json(row) for row in normalized))
    tombstones_jsonl = output_dir / "tombstones.jsonl"
    tombstones_jsonl.write_bytes(b"".join(_canonical_json(row) for row in tombstones))
    capture_plan = output_dir / "capture-plan.json"
    capture_plan.write_bytes(
        _canonical_json(
            {
                "schema_version": "archive-govt-nz.health-capture-plan/v1",
                "outcomes": capture_outcomes,
            }
        )
    )
    parquet_path = output_dir / "resources.parquet"
    pq.write_table(pa.Table.from_pylist(normalized), parquet_path, compression="zstd")
    readme = output_dir / "README.md"
    readme.write_text(
        "# Ministry of Health preservation candidate\n\n"
        "Status: **prepared-not-published**.\n\n"
        f"Resources classified: {len(normalized)}. Eligible: "
        f"{len(normalized) - len(tombstones)}. Rights-restricted: "
        f"{len(tombstones)}.\n\n"
        "No resource is downloaded unless its resource-level classification is "
        "eligible and explicitly authorizes download. Dataset-level licensing is not "
        "treated as resource-level authority. JSONL and Parquet are transformations; "
        "the source evidence JSON is preserved unchanged.\n",
        encoding="utf-8",
    )
    capture_receipt_path = output_dir / "capture-run.json"
    capture_receipt: dict[str, Any] | None = None
    if capture_receipt_path.is_file():
        loaded_receipt = json.loads(capture_receipt_path.read_text(encoding="utf-8"))
        if not isinstance(loaded_receipt, dict):
            _fail("invalid_capture_receipt")
        capture_receipt = cast("dict[str, Any]", loaded_receipt)
    capture_results = (
        capture_receipt.get("results", []) if capture_receipt is not None else []
    )
    if not isinstance(capture_results, list):
        _fail("invalid_capture_results")
    captured_count = sum(
        1
        for result in cast("list[object]", capture_results)
        if isinstance(result, dict) and result.get("state") == "captured"
    )
    artifacts = [
        _hash_receipt(metadata_copy, output_dir, "source-evidence"),
        _hash_receipt(classification_copy, output_dir, "source-evidence"),
        _hash_receipt(resources_jsonl, output_dir, "normalized-metadata"),
        _hash_receipt(parquet_path, output_dir, "normalized-metadata"),
        _hash_receipt(tombstones_jsonl, output_dir, "tombstones"),
        _hash_receipt(capture_plan, output_dir, "capture-plan"),
        _hash_receipt(readme, output_dir, "human-readable-summary"),
    ]
    if capture_receipt is not None:
        artifacts.append(
            _hash_receipt(capture_receipt_path, output_dir, "capture-receipt")
        )
    manifest: dict[str, object] = {
        "schema_version": "archive-govt-nz.health-preservation-package/v1",
        "status": "prepared-not-published",
        "publication_authorized": False,
        "payload_transfer": bool(
            capture_receipt and capture_receipt.get("payload_transfer")
        ),
        "observed_at": metadata.get("observed_at"),
        "counts": {
            "resources": len(normalized),
            "eligible": len(normalized) - len(tombstones),
            "rights_restricted": len(tombstones),
            "captured": captured_count,
        },
        "artifacts": artifacts,
        "transformations": [
            {
                "name": "resource-metadata-jsonl-and-parquet",
                "version": "health-package/v1",
                "source": "source/moh-resource-metadata.json",
                "information_loss": [
                    "unmodelled CKAN fields are absent from source evidence"
                ],
            }
        ],
    }
    (output_dir / "manifest.json").write_bytes(_canonical_json(manifest))
    return manifest


__all__ = ["HealthPackageError", "prepare_health_package"]
