"""Fail-closed reconciliation for one explicit real legislation batch."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, NoReturn

from archive_govt_nz.domains.legislation.manifest import (
    compute_legislation_inventory_sha256,
    compute_legislation_manifest_sha256,
)
from archive_govt_nz.domains.legislation.models import (
    validate_legislation_record,
)
from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreError

if TYPE_CHECKING:
    from pathlib import Path

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_LIMITATIONS = [
    "one_search_derived_batch_only",
    "not_corpus_completeness_evidence",
    "no_remote_publication_or_rights_verification",
]


class OneBatchReconciliationError(RuntimeError):
    """Stable fail-closed one-batch reconciliation error."""

    def __init__(self, error_class: str) -> None:
        """Create an error without embedding local paths or source payloads."""
        self.error_class = error_class
        super().__init__(error_class)


def _fail(error_class: str) -> NoReturn:
    """Raise one stable reconciliation failure."""
    raise OneBatchReconciliationError(error_class)


def _require_file(path: Path, error_class: str) -> None:
    """Require one direct regular-file input."""
    if path.is_symlink() or not path.is_file():
        _fail(error_class)


def _load_json_object(path: Path, kind: str) -> dict[str, Any]:
    """Load one required JSON object with stable failure classes."""
    _require_file(path, f"{kind}_missing")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError, UnicodeError, json.JSONDecodeError:
        _fail(f"{kind}_invalid_json")
    if not isinstance(payload, dict):
        _fail(f"{kind}_not_object")
    return payload


def _load_batch_ids(path: Path) -> list[str]:
    """Load a non-empty, canonical, unique donor batch identity sequence."""
    _require_file(path, "batch_missing")
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError, UnicodeError:
        _fail("batch_unreadable")
    if not lines:
        _fail("batch_empty")
    if any(not line or line != line.strip() or line.startswith("#") for line in lines):
        _fail("batch_id_invalid")
    if len(set(lines)) != len(lines):
        _fail("batch_ids_duplicate")
    if lines != sorted(lines):
        _fail("batch_ids_not_canonical")
    return lines


def canonical_batch_sha256(path: Path) -> str:
    """Hash one canonical line-normalized donor batch identity sequence."""
    work_ids = _load_batch_ids(path)
    return _batch_sha256(work_ids)


def _batch_sha256(work_ids: list[str]) -> str:
    """Hash a previously validated canonical identity sequence."""
    payload = ("\n".join(work_ids) + "\n").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _validate_inventory(manifest: dict[str, Any]) -> set[str]:
    """Validate the cumulative discovered-work inventory and its root."""
    discovered = manifest.get("discovered_work_ids")
    if not isinstance(discovered, list) or not all(
        isinstance(work_id, str) and work_id for work_id in discovered
    ):
        _fail("inventory_ids_invalid")
    if discovered != sorted(set(discovered)):
        _fail("inventory_ids_not_canonical")
    discovered_count = manifest.get("discovered_works_count")
    if (
        isinstance(discovered_count, bool)
        or not isinstance(discovered_count, int)
        or discovered_count != len(discovered)
    ):
        _fail("inventory_count_mismatch")
    if manifest.get(
        "discovered_inventory_sha256"
    ) != compute_legislation_inventory_sha256(discovered):
        _fail("inventory_root_mismatch")
    return set(discovered)


def _validate_record_header(
    record: dict[str, Any], discovered: set[str], document_ids: set[str]
) -> tuple[str, str]:
    """Validate one record schema, work membership, and document identity."""
    schema_version = record.get("schema_version")
    if schema_version not in {
        "archive-govt-nz.legislation/v1",
        "archive-govt-nz.legislation/v2",
    }:
        _fail("manifest_record_schema_unsupported")
    work_id = record.get("work_id")
    if not isinstance(work_id, str) or not work_id or work_id not in discovered:
        _fail("manifest_work_not_discovered")
    document_id = record.get("document_id")
    if not isinstance(document_id, str) or not document_id:
        _fail("canonical_document_missing")
    if document_id in document_ids:
        _fail("document_identity_duplicate")
    document_ids.add(document_id)
    return str(schema_version), work_id


def _validate_expression_identity(
    record: dict[str, Any], work_id: str, expression_work_ids: dict[str, str]
) -> None:
    """Validate one optional canonical expression identity."""
    expression_id = record.get("expression_id")
    if expression_id is None:
        return
    if not isinstance(expression_id, str) or not expression_id:
        _fail("canonical_expression_invalid")
    prior_work = expression_work_ids.setdefault(expression_id, work_id)
    if prior_work != work_id:
        _fail("expression_identity_collision")


def _validate_manifestation_identity(
    record: dict[str, Any], manifestation_ids: set[str]
) -> None:
    """Validate one optional canonical manifestation identity."""
    manifestation_id = record.get("manifestation_id")
    if manifestation_id is None:
        return
    if not isinstance(manifestation_id, str) or not manifestation_id:
        _fail("canonical_manifestation_invalid")
    if manifestation_id in manifestation_ids:
        _fail("manifestation_identity_duplicate")
    manifestation_ids.add(manifestation_id)


def _validate_record_identities(
    records: list[dict[str, Any]], discovered: set[str]
) -> None:
    """Validate cumulative record schemas and canonical identity uniqueness."""
    manifestation_ids: set[str] = set()
    document_ids: set[str] = set()
    expression_work_ids: dict[str, str] = {}
    for record in records:
        schema_version, work_id = _validate_record_header(
            record, discovered, document_ids
        )
        _validate_expression_identity(record, work_id, expression_work_ids)
        _validate_manifestation_identity(record, manifestation_ids)
        if validate_legislation_record(record, str(schema_version)):
            _fail("manifest_record_invalid")


def _validate_manifest(
    manifest_path: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], set[str]]:
    """Validate cumulative manifest structure, roots, and record identities."""
    manifest = _load_json_object(manifest_path, "manifest")
    if manifest.get("schema_version") != "archive-govt-nz.legislation-manifest/v1":
        _fail("manifest_schema_unsupported")
    records = manifest.get("records")
    if (
        not isinstance(records, list)
        or not records
        or not all(isinstance(record, dict) for record in records)
    ):
        _fail("manifest_records_invalid")
    typed_records = list(records)
    total_records = manifest.get("total_records")
    if (
        isinstance(total_records, bool)
        or not isinstance(total_records, int)
        or total_records != len(typed_records)
    ):
        _fail("manifest_record_count_mismatch")
    if manifest.get("manifest_sha256") != compute_legislation_manifest_sha256(
        typed_records
    ):
        _fail("manifest_root_mismatch")
    discovered = _validate_inventory(manifest)
    _validate_record_identities(typed_records, discovered)
    return manifest, typed_records, discovered


def _identifier_list(
    checkpoint: dict[str, Any], field_name: str, *, sorted_required: bool
) -> list[str]:
    """Validate one checkpoint identifier list."""
    identifiers = checkpoint.get(field_name)
    if not isinstance(identifiers, list) or not all(
        isinstance(identifier, str) and identifier for identifier in identifiers
    ):
        _fail(f"checkpoint_{field_name}_invalid")
    if len(set(identifiers)) != len(identifiers):
        _fail(f"checkpoint_{field_name}_duplicate")
    if sorted_required and identifiers != sorted(identifiers):
        _fail(f"checkpoint_{field_name}_not_canonical")
    return identifiers


def _validate_checkpoint(
    checkpoint_path: Path,
    manifest: dict[str, Any],
    *,
    batch_id: str,
) -> set[str]:
    """Validate checkpoint accounting and linkage to the cumulative manifest."""
    checkpoint = _load_json_object(checkpoint_path, "checkpoint")
    if checkpoint.get("schema_version") != "archive-govt-nz.legislation-checkpoint/v1":
        _fail("checkpoint_schema_unsupported")
    completed = _identifier_list(checkpoint, "completed_batches", sorted_required=False)
    if batch_id not in completed:
        _fail("batch_not_completed")
    processed = _identifier_list(checkpoint, "processed_work_ids", sorted_required=True)
    last_index = checkpoint.get("last_processed_index")
    if (
        isinstance(last_index, bool)
        or not isinstance(last_index, int)
        or last_index != len(processed)
    ):
        _fail("checkpoint_processed_count_mismatch")
    total_records = checkpoint.get("total_records_preserved")
    if (
        isinstance(total_records, bool)
        or not isinstance(total_records, int)
        or total_records != manifest["total_records"]
    ):
        _fail("checkpoint_record_count_mismatch")
    metadata = checkpoint.get("metadata")
    if not isinstance(metadata, dict):
        _fail("checkpoint_metadata_invalid")
    if metadata.get("manifest_sha256") != manifest["manifest_sha256"]:
        _fail("checkpoint_manifest_root_mismatch")
    if (
        metadata.get("discovered_inventory_sha256")
        != manifest["discovered_inventory_sha256"]
    ):
        _fail("checkpoint_inventory_root_mismatch")
    conditional = metadata.get("conditional_requests", {})
    if not isinstance(conditional, dict):
        _fail("checkpoint_conditionals_invalid")
    return set(processed)


def _selected_records(
    records: list[dict[str, Any]], batch_ids: list[str]
) -> list[dict[str, Any]]:
    """Select batch records and require complete canonical FRBR identity."""
    batch_set = set(batch_ids)
    selected = [record for record in records if record.get("work_id") in batch_set]
    selected_work_ids = {str(record["work_id"]) for record in selected}
    if selected_work_ids != batch_set:
        _fail("batch_work_not_manifested")
    for record in selected:
        if (
            not isinstance(record.get("expression_id"), str)
            or not record["expression_id"]
        ):
            _fail("canonical_expression_missing")
        if (
            not isinstance(record.get("manifestation_id"), str)
            or not record["manifestation_id"]
        ):
            _fail("canonical_manifestation_missing")
    return selected


def _verify_selected_cas(cas_path: Path, selected: list[dict[str, Any]]) -> int:
    """Stream-verify selected target objects and their dual hashes."""
    if cas_path.is_symlink() or not cas_path.is_dir():
        _fail("cas_missing")
    objects_root = cas_path / "sha256"
    if objects_root.is_symlink() or not objects_root.is_dir():
        _fail("cas_layout_invalid")
    store = ContentAddressedStore(cas_path, create=False)
    verified: set[str] = set()
    for record in selected:
        sha256 = str(record["raw_cas_hash_sha256"])
        object_id = f"sha256:{sha256}"
        object_path = store.get_path(object_id)
        if (
            object_path.parent.is_symlink()
            or object_path.is_symlink()
            or not object_path.resolve().is_relative_to(cas_path.resolve())
        ):
            _fail("cas_layout_invalid")
        if object_id in verified:
            continue
        try:
            receipt = store.verify(object_id)
        except ObjectStoreError as exc:
            _fail(f"cas_{exc.error_class}")
        if receipt.blake3 != record.get("raw_cas_hash_blake3"):
            _fail("cas_blake3_mismatch")
        byte_size = int(record["byte_size"])
        if receipt.byte_count != byte_size:
            _fail("cas_byte_size_mismatch")
        verified.add(object_id)
    return len(verified)


def reconcile_one_batch(  # noqa: PLR0913
    *,
    batch_id: str,
    batch_path: Path,
    expected_batch_sha256: str,
    manifest_path: Path,
    checkpoint_path: Path,
    cas_path: Path,
    evaluated_at: str | None = None,
) -> dict[str, Any]:
    """Reconcile exactly one real donor batch against durable target state."""
    if not batch_id or batch_id != batch_id.strip():
        _fail("batch_id_invalid")
    if not _SHA256.fullmatch(expected_batch_sha256):
        _fail("batch_sha256_invalid")
    batch_ids = _load_batch_ids(batch_path)
    actual_batch_sha256 = _batch_sha256(batch_ids)
    if actual_batch_sha256 != expected_batch_sha256:
        _fail("batch_sha256_mismatch")

    manifest, records, discovered = _validate_manifest(manifest_path)
    missing_discovered = sorted(set(batch_ids) - discovered)
    if missing_discovered:
        _fail("batch_work_not_discovered")
    processed = _validate_checkpoint(checkpoint_path, manifest, batch_id=batch_id)
    if set(batch_ids) - processed:
        _fail("batch_work_not_processed")
    selected = _selected_records(records, batch_ids)
    verified = _verify_selected_cas(cas_path, selected)

    timestamp = evaluated_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": ("archive-govt-nz.legislation-one-batch-reconciliation/v1"),
        "status": "passed",
        "evaluated_at": timestamp,
        "batch_id": batch_id,
        "batch_file": batch_path.name,
        "batch_sha256": actual_batch_sha256,
        "batch_work_ids_count": len(batch_ids),
        "reconciled_work_ids_count": len(batch_ids),
        "selected_records_count": len(selected),
        "cas_objects_verified": verified,
        "manifest_total_records": manifest["total_records"],
        "manifest_sha256": manifest["manifest_sha256"],
        "discovered_works_count": manifest["discovered_works_count"],
        "discovered_inventory_sha256": manifest["discovered_inventory_sha256"],
        "checkpoint_processed_ids_count": len(processed),
        "mismatch_count": 0,
        "mismatches": [],
        "limitations": list(_LIMITATIONS),
    }


def _write_receipt(path: Path, receipt: dict[str, Any]) -> None:
    """Atomically write one explicit reconciliation receipt."""
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_suffix(f"{path.suffix}.staging.tmp")
    staging.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    staging.replace(path)


def run_one_batch_reconciliation(  # noqa: PLR0913
    *,
    batch_id: str,
    batch_path: Path,
    expected_batch_sha256: str,
    manifest_path: Path,
    checkpoint_path: Path,
    cas_path: Path,
    receipt_path: Path,
    evaluated_at: str | None = None,
) -> int:
    """Write a passed or bounded failed receipt and return its process code."""
    timestamp = evaluated_at or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        receipt = reconcile_one_batch(
            batch_id=batch_id,
            batch_path=batch_path,
            expected_batch_sha256=expected_batch_sha256,
            manifest_path=manifest_path,
            checkpoint_path=checkpoint_path,
            cas_path=cas_path,
            evaluated_at=timestamp,
        )
    except OneBatchReconciliationError as exc:
        receipt = {
            "schema_version": (
                "archive-govt-nz.legislation-one-batch-reconciliation/v1"
            ),
            "status": "failed",
            "evaluated_at": timestamp,
            "batch_id": batch_id,
            "error_class": exc.error_class,
            "mismatch_count": 1,
            "mismatches": [exc.error_class],
            "limitations": list(_LIMITATIONS),
        }
        _write_receipt(receipt_path, receipt)
        return 1
    _write_receipt(receipt_path, receipt)
    return 0
