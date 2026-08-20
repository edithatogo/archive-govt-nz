"""Authenticated read-only state projections for the legislation CLI."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.legislation.corpus import LegislationArchiveService
from archive_govt_nz.domains.legislation.models import validate_legislation_record
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path

_INVENTORY_FIELDS = {
    "discovered_work_ids",
    "discovered_works_count",
    "discovered_inventory_sha256",
}


def load_authenticated_manifest(path: Path) -> dict[str, Any]:
    """Load a rooted cumulative manifest with inventory and valid records."""
    manifest = LegislationArchiveService.load_manifest(path)
    if manifest is None:
        msg = "manifest is missing"
        raise ValueError(msg)
    if not _INVENTORY_FIELDS.issubset(manifest):
        msg = "manifest has no authenticated discovered inventory"
        raise ValueError(msg)
    records = manifest["records"]
    for record in records:
        schema_version = str(record.get("schema_version", ""))
        errors = validate_legislation_record(record, schema_version)
        if errors:
            msg = f"manifest record is invalid: {'; '.join(errors)}"
            raise ValueError(msg)
    return manifest


def coverage_counts(manifest_path: Path) -> tuple[int, int, int, int]:
    """Project coverage from the authenticated discovered inventory."""
    if not manifest_path.is_file():
        return 0, 0, 0, 0
    manifest = load_authenticated_manifest(manifest_path)
    records = manifest["records"]
    discovered = manifest["discovered_work_ids"]
    retrieved_ids = {str(record["work_id"]) for record in records}
    html_count = sum(
        1 for record in records if ":html:" in str(record.get("manifestation_id", ""))
    )
    return (
        len(discovered),
        len(retrieved_ids),
        len(records) - html_count,
        html_count,
    )


def verify_linked_state(
    cas_path: Path, checkpoint_path: Path, manifest_path: Path
) -> int:
    """Verify linked manifest, checkpoint, and sharded dual-hash CAS state."""
    manifest = load_authenticated_manifest(manifest_path)
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if not isinstance(checkpoint, dict):
        msg = "checkpoint must be an object"
        raise TypeError(msg)
    LegislationArchiveService.validate_checkpoint(checkpoint)
    metadata = checkpoint.get("metadata", {})
    if metadata.get("manifest_sha256") != manifest["manifest_sha256"]:
        msg = "checkpoint manifest root does not match"
        raise ValueError(msg)
    if checkpoint.get("total_records_preserved") != manifest["total_records"]:
        msg = "checkpoint record count does not match"
        raise ValueError(msg)

    store = ContentAddressedStore(cas_path, create=False)
    object_ids: set[str] = set()
    for record in manifest["records"]:
        object_id = f"sha256:{record['raw_cas_hash_sha256']}"
        receipt = store.verify(object_id)
        if receipt.blake3 != record["raw_cas_hash_blake3"]:
            msg = "manifest BLAKE3 does not match CAS object"
            raise ValueError(msg)
        if receipt.byte_count != record["byte_size"]:
            msg = "manifest byte size does not match CAS object"
            raise ValueError(msg)
        object_ids.add(object_id)
    return len(object_ids)
