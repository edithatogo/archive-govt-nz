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


def build_manifest(
    *,
    archive_id: str,
    observations: list[dict[str, Any]],
    objects: list[dict[str, Any]],
    versions: list[dict[str, Any]],
    derivatives: list[dict[str, Any]] | None = None,
) -> ManifestReceipt:
    """Build a deterministic manifest and reject dangling relationships."""
    if not archive_id.strip():
        raise ProvenanceError("missing_archive_id")
    object_ids = {item.get("object_id") for item in objects}
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
    }
    canonical = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return ManifestReceipt(document, canonical, hashlib.sha256(canonical).hexdigest())
