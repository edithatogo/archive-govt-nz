"""Closed, deterministic provenance manifests for archive releases."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


class ProvenanceError(ValueError):
    """Manifest closure or serialization failure."""

    def __init__(self, error_class: str) -> None:
        self.error_class = error_class
        super().__init__(error_class)


@dataclass(frozen=True, slots=True)
class ManifestReceipt:
    """Canonical manifest bytes and its content hash."""

    document: dict[str, Any]
    canonical_json: bytes
    sha256: str


def _unique_object_ids(objects: list[dict[str, Any]]) -> set[Any]:
    ids = {item.get("object_id") for item in objects}
    if len(ids) != len(objects):
        raise ProvenanceError("duplicate_object_id")
    return ids


def build_manifest(
    *,
    archive_id: str,
    observations: list[dict[str, Any]],
    objects: list[dict[str, Any]],
    versions: list[dict[str, Any]],
    derivatives: list[dict[str, Any]] | None = None,
    warc_records: list[dict[str, Any]] | None = None,
    receipts: dict[str, list[dict[str, Any]]] | None = None,
    context: dict[str, Any] | None = None,
) -> ManifestReceipt:
    """Build a deterministic manifest and reject dangling relationships."""
    if not archive_id.strip():
        raise ProvenanceError("missing_archive_id")

    object_ids = _unique_object_ids(objects)
    observation_ids = {item.get("observation_id") for item in observations}
    version_ids = {item.get("version_id") for item in versions}
    if None in object_ids or None in observation_ids or None in version_ids:
        raise ProvenanceError("missing_identifier")
    for version in versions:
        if version.get("observation_id") not in observation_ids:
            raise ProvenanceError("dangling_observation")
    for derivative in derivatives or []:
        if derivative.get("source_object_id") not in object_ids:
            raise ProvenanceError("dangling_source_object")
        if derivative.get("version_id") not in version_ids:
            raise ProvenanceError("dangling_version")
    for warc in warc_records or []:
        if warc.get("object_id") not in object_ids:
            raise ProvenanceError("dangling_warc_object")
    receipt_document = receipts or {}
    _validate_receipts(receipt_document)
    allowed_receipts = {"transformations", "validations", "publications"}
    document = {
        "schema_version": "archive-govt-nz.manifest/v1",
        "archive_id": archive_id,
        "observations": sorted(
            observations, key=lambda item: str(item["observation_id"])
        ),
        "objects": sorted(objects, key=lambda item: str(item["object_id"])),
        "versions": sorted(versions, key=lambda item: str(item["version_id"])),
        "derivatives": sorted(
            derivatives or [], key=lambda item: str(item.get("derivative_id", ""))
        ),
        "warc_records": sorted(
            warc_records or [], key=lambda item: str(item.get("record_id", ""))
        ),
        "receipts": {
            key: sorted(
                receipt_document.get(key, []),
                key=lambda item: str(item.get("receipt_id", "")),
            )
            for key in sorted(allowed_receipts)
        },
        "context": context or {},
    }
    canonical = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return ManifestReceipt(document, canonical, hashlib.sha256(canonical).hexdigest())


def _validate_receipts(receipts: dict[str, list[dict[str, Any]]]) -> None:
    """Reject unknown receipt collections and entries without stable IDs.

    Also validates that transformation/validation/publication receipts have
    all required fields per their schema, not just receipt_id.
    """
    allowed_receipts = {"transformations", "validations", "publications"}
    if set(receipts) - allowed_receipts:
        raise ProvenanceError("unknown_receipt_type")

    required_fields = {
        "transformations": (
            "receipt_id",
            "name",
            "version",
            "implementation_revision",
            "input_object_ids",
            "output_object_ids",
            "parameters",
            "environment_sbom_id",
            "started_at",
            "ended_at",
            "information_loss",
            "deterministic",
        ),
        "validations": (
            "receipt_id",
            "validator_name",
            "validator_version",
            "subject_ids",
            "checks",
            "findings",
            "started_at",
            "ended_at",
        ),
        "publications": (
            "receipt_id",
            "target",
            "local_version_id",
            "manifest_sha256",
            "requested_at",
        ),
    }

    for receipt_type, entries in receipts.items():
        for entry in entries:
            if not str(entry.get("receipt_id", "")).strip():
                label = receipt_type.rstrip("s")
                error_class = f"missing_{label}_receipt_id"
                raise ProvenanceError(error_class)

            # Validate complete receipt structure
            if receipt_type in required_fields:
                missing = [f for f in required_fields[receipt_type] if f not in entry]
                if missing:
                    msg = f"incomplete_{receipt_type.rstrip('s')}_receipt"
                    raise ProvenanceError(msg)


# === Transformation record adapter for manifest interoperability ===

TRANSFORMATION_RECEIPT_FIELDS = (
    "receipt_id",
    "name",
    "version",
    "implementation_revision",
    "input_object_ids",
    "output_object_ids",
    "parameters",
    "environment_sbom_id",
    "started_at",
    "ended_at",
    "information_loss",
    "deterministic",
)

VALIDATION_RECEIPT_FIELDS = (
    "receipt_id",
    "validator_name",
    "validator_version",
    "subject_ids",
    "checks",
    "findings",
    "started_at",
    "ended_at",
)

PUBLICATION_RECEIPT_FIELDS = (
    "receipt_id",
    "target",
    "local_version_id",
    "manifest_sha256",
    "requested_at",
    "remote_identifier",
    "remote_revision",
    "verified_at",
    "doi",
)


def transformation_record_to_receipt(record: dict[str, Any]) -> dict[str, Any]:
    """Convert a strict TransformationRecord to a manifest transformation receipt entry.

    Validates the record has all required fields before inclusion in manifest.
    """
    missing = [f for f in TRANSFORMATION_RECEIPT_FIELDS if f not in record]
    if missing:
        raise ProvenanceError("incomplete_transformation_receipt")
    if not str(record.get("receipt_id", "")).strip():
        raise ProvenanceError("missing_transformation_receipt_id")
    return {k: record[k] for k in TRANSFORMATION_RECEIPT_FIELDS}


def validation_record_to_receipt(record: dict[str, Any]) -> dict[str, Any]:
    """Convert a strict ValidationRecord to a manifest validation receipt entry."""
    missing = [f for f in VALIDATION_RECEIPT_FIELDS if f not in record]
    if missing:
        raise ProvenanceError("incomplete_validation_receipt")
    if not str(record.get("receipt_id", "")).strip():
        raise ProvenanceError("missing_validation_receipt_id")
    return {k: record[k] for k in VALIDATION_RECEIPT_FIELDS}


def publication_record_to_receipt(record: dict[str, Any]) -> dict[str, Any]:
    """Convert a strict PublicationRecord to a manifest publication receipt entry."""
    missing = [f for f in PUBLICATION_RECEIPT_FIELDS if f not in record and f != "doi"]
    if missing:
        raise ProvenanceError("incomplete_publication_receipt")
    if not str(record.get("receipt_id", "")).strip():
        raise ProvenanceError("missing_publication_receipt_id")
    return {k: record[k] for k in PUBLICATION_RECEIPT_FIELDS if k in record}


def build_receipts_from_records(
    transformations: list[dict[str, Any]] | None = None,
    validations: list[dict[str, Any]] | None = None,
    publications: list[dict[str, Any]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Build manifest receipts dict from strict native records.

    Each record is validated and converted to the manifest receipt format.
    """
    receipts: dict[str, list[dict[str, Any]]] = {}
    if transformations:
        receipts["transformations"] = [
            transformation_record_to_receipt(r) for r in transformations
        ]
    if validations:
        receipts["validations"] = [validation_record_to_receipt(r) for r in validations]
    if publications:
        receipts["publications"] = [
            publication_record_to_receipt(r) for r in publications
        ]
    return receipts
