"""Source and transformation manifest compilation for legislation packages."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from archive_govt_nz.domains.legislation.models import LegislationRecord


def _entry_key(entry: dict[str, Any]) -> str:
    """Return the strongest canonical identity available for one entry."""
    return str(entry.get("manifestation_id") or entry.get("document_id") or "")


def _entry_sha256(entry: dict[str, Any]) -> str:
    """Return the source-byte SHA-256 across v1 and v2 manifest aliases."""
    return str(entry.get("raw_cas_hash_sha256") or entry.get("raw_sha256") or "")


def compute_legislation_manifest_sha256(records: list[dict[str, Any]]) -> str:
    """Hash canonical manifest records in stable identity order."""
    hasher = hashlib.sha256()
    for entry in sorted(records, key=_entry_key):
        hasher.update(json.dumps(entry, sort_keys=True).encode("utf-8"))
    return hasher.hexdigest()


def compute_legislation_inventory_sha256(work_ids: list[str]) -> str:
    """Hash the canonical bounded discovered-work inventory."""
    canonical_ids = sorted(set(work_ids))
    payload = json.dumps(canonical_ids, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _add_existing_entry(
    entries_by_id: dict[str, dict[str, Any]], entry: dict[str, Any]
) -> None:
    """Add one validated prior entry without collapsing duplicate identities."""
    key = _entry_key(entry)
    if not key:
        msg = "manifest record missing canonical identity"
        raise ValueError(msg)
    if not _entry_sha256(entry):
        msg = f"manifest record {key} missing source SHA-256"
        raise ValueError(msg)
    if key in entries_by_id:
        msg = f"duplicate canonical manifest identity: {key}"
        raise ValueError(msg)
    entries_by_id[key] = entry


def _merge_new_entry(
    entries_by_id: dict[str, dict[str, Any]], entry: dict[str, Any]
) -> None:
    """Merge a current entry while protecting canonical identity immutability."""
    key = _entry_key(entry)
    if not key:
        msg = "normalised record missing canonical identity"
        raise ValueError(msg)
    previous = entries_by_id.get(key)
    if previous is None:
        entries_by_id[key] = entry
        return
    if _entry_sha256(previous) != _entry_sha256(entry):
        msg = f"manifestation identity collision for {key}"
        raise ValueError(msg)
    for field_name in ("work_id", "expression_id", "manifestation_id"):
        previous_value = previous.get(field_name)
        current_value = entry.get(field_name)
        if previous_value and current_value and previous_value != current_value:
            msg = f"canonical identity collision for {key}: {field_name}"
            raise ValueError(msg)


def build_legislation_manifest(
    records: list[LegislationRecord],
    run_id: str = "",
    *,
    existing_records: list[dict[str, Any]] | None = None,
    discovered_work_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Compile a cumulative immutable source manifest from canonical records."""
    entries_by_id: dict[str, dict[str, Any]] = {}
    for entry in existing_records or []:
        _add_existing_entry(entries_by_id, entry)

    for record in records:
        entry = record.to_dict("v2")
        entry["raw_sha256"] = record.raw_cas_hash_sha256
        entry["raw_blake3"] = record.raw_cas_hash_blake3
        _merge_new_entry(entries_by_id, entry)

    entries = sorted(entries_by_id.values(), key=_entry_key)
    discovered = sorted(
        set(discovered_work_ids or [])
        | {str(entry["work_id"]) for entry in entries if entry.get("work_id")}
    )

    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": "archive-govt-nz.legislation-manifest/v1",
        "generated_at": now_iso,
        "run_id": run_id or f"run-leg-{now_iso}",
        "discovered_work_ids": discovered,
        "discovered_works_count": len(discovered),
        "discovered_inventory_sha256": compute_legislation_inventory_sha256(discovered),
        "total_records": len(entries),
        "manifest_sha256": compute_legislation_manifest_sha256(entries),
        "records": entries,
    }
