"""Adversarial tests for one real legislation batch reconciliation."""

from __future__ import annotations

import hashlib
import json
import runpy
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import jsonschema
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from archive_govt_nz.domains.legislation.manifest import (
    compute_legislation_inventory_sha256,
    compute_legislation_manifest_sha256,
)
from archive_govt_nz.domains.legislation.one_batch_reconciliation import (
    OneBatchReconciliationError,
    canonical_batch_sha256,
    reconcile_one_batch,
    run_one_batch_reconciliation,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from collections.abc import Callable

SCHEMA_PATH = Path("schemas/legislation/v1/one-batch-reconciliation.schema.json")


def _record(
    work_id: str, content: bytes, store: ContentAddressedStore
) -> dict[str, Any]:
    stored = store.put_bytes(content)
    return {
        "schema_version": "archive-govt-nz.legislation/v2",
        "document_id": f"document-{work_id}",
        "work_id": work_id,
        "expression_id": f"expression-{work_id}",
        "manifestation_id": f"manifestation-{work_id}",
        "title": f"Title {work_id}",
        "legislation_type": "act",
        "status": "historical",
        "canonical_uri": f"https://www.legislation.govt.nz/{work_id}",
        "raw_cas_hash_sha256": stored.sha256,
        "raw_cas_hash_blake3": stored.blake3,
        "byte_size": stored.byte_count,
        "retrieval_timestamp": "2026-08-20T00:00:00Z",
        "rights_statement": None,
        "redistribution_policy": "rights_review_required",
    }


def _write_valid_state(tmp_path: Path) -> dict[str, Any]:
    batch_ids = ["work-1", "work-2"]
    batch_path = tmp_path / "historical-work-ids-0001.txt"
    batch_path.write_text("work-1\nwork-2\n", encoding="utf-8")
    expected_batch_sha256 = hashlib.sha256(b"work-1\nwork-2\n").hexdigest()

    cas_path = tmp_path / "cas"
    store = ContentAddressedStore(cas_path)
    records = [
        _record("prior-work", b"prior", store),
        _record("work-1", b"one", store),
        _record("work-2", b"two", store),
    ]
    discovered = ["prior-work", *batch_ids]
    manifest_sha256 = compute_legislation_manifest_sha256(records)
    inventory_sha256 = compute_legislation_inventory_sha256(discovered)
    manifest = {
        "schema_version": "archive-govt-nz.legislation-manifest/v1",
        "generated_at": "2026-08-20T00:00:00Z",
        "run_id": "batch-1",
        "discovered_work_ids": discovered,
        "discovered_works_count": len(discovered),
        "discovered_inventory_sha256": inventory_sha256,
        "total_records": len(records),
        "manifest_sha256": manifest_sha256,
        "records": records,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    checkpoint = {
        "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
        "last_updated": "2026-08-20T00:00:00Z",
        "completed_batches": ["prior-batch", "batch-1"],
        "processed_work_ids": discovered,
        "last_processed_index": len(discovered),
        "total_records_preserved": len(records),
        "metadata": {
            "manifest_sha256": manifest_sha256,
            "discovered_inventory_sha256": inventory_sha256,
            "conditional_requests": {},
        },
    }
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    return {
        "batch_ids": batch_ids,
        "batch_path": batch_path,
        "expected_batch_sha256": expected_batch_sha256,
        "cas_path": cas_path,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "checkpoint": checkpoint,
        "checkpoint_path": checkpoint_path,
    }


def _reconcile(state: dict[str, Any]) -> dict[str, Any]:
    return reconcile_one_batch(
        batch_id="batch-1",
        batch_path=state["batch_path"],
        expected_batch_sha256=state["expected_batch_sha256"],
        manifest_path=state["manifest_path"],
        checkpoint_path=state["checkpoint_path"],
        cas_path=state["cas_path"],
        evaluated_at="2026-08-20T00:00:00Z",
    )


def _rewrite(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def _rewrite_manifest_with_root(state: dict[str, Any]) -> None:
    manifest = state["manifest"]
    manifest["manifest_sha256"] = compute_legislation_manifest_sha256(
        manifest["records"]
    )
    _rewrite(state["manifest_path"], manifest)
    state["checkpoint"]["metadata"]["manifest_sha256"] = manifest["manifest_sha256"]
    _rewrite(state["checkpoint_path"], state["checkpoint"])


def test_one_batch_reconciliation_passes_on_real_cumulative_state(
    tmp_path: Path,
) -> None:
    """One selected batch may reconcile within truthful cumulative state."""
    state = _write_valid_state(tmp_path)

    receipt = _reconcile(state)

    assert receipt["status"] == "passed"
    assert receipt["batch_work_ids_count"] == 2
    assert receipt["reconciled_work_ids_count"] == 2
    assert receipt["selected_records_count"] == 2
    assert receipt["cas_objects_verified"] == 2
    assert receipt["manifest_total_records"] == 3
    assert receipt["mismatch_count"] == 0
    assert receipt["mismatches"] == []
    assert receipt["limitations"] == [
        "one_search_derived_batch_only",
        "not_corpus_completeness_evidence",
        "no_remote_publication_or_rights_verification",
    ]


@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(version_count=st.integers(min_value=2, max_value=12))
def test_one_work_accepts_multiple_version_records(
    tmp_path: Path, version_count: int
) -> None:
    """A Work document identity may own many distinct version manifestations."""
    state = _write_valid_state(tmp_path)
    records = state["manifest"]["records"]
    first = records[1]
    store = ContentAddressedStore(state["cas_path"])
    for index in range(1, version_count):
        version = _record("work-1", f"one-version-{index}".encode(), store)
        version["document_id"] = first["document_id"]
        version["expression_id"] = f"expression-work-1-v{index}"
        version["manifestation_id"] = f"manifestation-work-1-v{index}"
        records.append(version)
    state["manifest"]["total_records"] = len(records)
    state["checkpoint"]["total_records_preserved"] = len(records)
    _rewrite_manifest_with_root(state)

    receipt = _reconcile(state)

    assert receipt["status"] == "passed"
    assert receipt["selected_records_count"] == version_count + 1


def test_batch_sha256_is_canonical_and_rejects_ambiguous_ids(tmp_path: Path) -> None:
    """The exact sorted input identity sequence binds the selected donor batch."""
    path = tmp_path / "batch.txt"
    path.write_text("work-1\nwork-2\n", encoding="utf-8")
    assert (
        canonical_batch_sha256(path) == hashlib.sha256(b"work-1\nwork-2\n").hexdigest()
    )

    path.write_text("work-1\nwork-1\n", encoding="utf-8")
    with pytest.raises(OneBatchReconciliationError, match="batch_ids_duplicate"):
        canonical_batch_sha256(path)

    path.write_text("work-2\nwork-1\n", encoding="utf-8")
    with pytest.raises(OneBatchReconciliationError, match="batch_ids_not_canonical"):
        canonical_batch_sha256(path)


@pytest.mark.parametrize("content", ["", "# comment\n", " work-1\n", "work-1\n\n"])
def test_batch_file_rejects_empty_or_noncanonical_lines(
    tmp_path: Path, content: str
) -> None:
    """Empty, commented, padded, or blank identities are not batch evidence."""
    path = tmp_path / "batch.txt"
    path.write_text(content, encoding="utf-8")
    expected = "batch_empty" if not content else "batch_id_invalid"
    with pytest.raises(OneBatchReconciliationError, match=expected):
        canonical_batch_sha256(path)


def test_batch_file_rejects_unreadable_utf8(tmp_path: Path) -> None:
    """A batch that cannot be decoded is not silently replaced."""
    path = tmp_path / "batch.txt"
    path.write_bytes(b"\xff")
    with pytest.raises(OneBatchReconciliationError, match="batch_unreadable"):
        canonical_batch_sha256(path)


@pytest.mark.parametrize("batch_id", ["", " batch-1", "batch-1 "])
def test_reconciliation_rejects_invalid_batch_id(tmp_path: Path, batch_id: str) -> None:
    """The selected batch must have one explicit canonical identifier."""
    state = _write_valid_state(tmp_path)
    with pytest.raises(OneBatchReconciliationError, match="batch_id_invalid"):
        reconcile_one_batch(
            batch_id=batch_id,
            batch_path=state["batch_path"],
            expected_batch_sha256=state["expected_batch_sha256"],
            manifest_path=state["manifest_path"],
            checkpoint_path=state["checkpoint_path"],
            cas_path=state["cas_path"],
        )


def test_reconciliation_rejects_invalid_expected_digest(tmp_path: Path) -> None:
    """The caller must supply a canonical SHA-256, not an unbound label."""
    state = _write_valid_state(tmp_path)
    state["expected_batch_sha256"] = "not-a-sha256"
    with pytest.raises(OneBatchReconciliationError, match="batch_sha256_invalid"):
        _reconcile(state)


def test_reconciliation_rejects_invalid_manifest_json(tmp_path: Path) -> None:
    """Malformed and non-UTF-8 manifests fail before any parity assertion."""
    state = _write_valid_state(tmp_path)
    state["manifest_path"].write_bytes(b"\xff")
    with pytest.raises(OneBatchReconciliationError, match="manifest_invalid_json"):
        _reconcile(state)


@pytest.mark.parametrize(
    ("case", "error_class"),
    [
        ("records_not_list", "manifest_records_invalid"),
        ("records_empty", "manifest_records_invalid"),
        ("record_not_object", "manifest_records_invalid"),
        ("count_bool", "manifest_record_count_mismatch"),
        ("count_string", "manifest_record_count_mismatch"),
        ("inventory_not_list", "inventory_ids_invalid"),
        ("inventory_bad_item", "inventory_ids_invalid"),
        ("inventory_not_canonical", "inventory_ids_not_canonical"),
        ("inventory_count_bool", "inventory_count_mismatch"),
        ("inventory_count_string", "inventory_count_mismatch"),
        ("inventory_count_wrong", "inventory_count_mismatch"),
        ("record_schema", "manifest_record_schema_unsupported"),
        ("document_missing", "canonical_document_missing"),
        ("document_duplicate", "document_identity_duplicate"),
        ("expression_invalid", "canonical_expression_invalid"),
        ("expression_collision", "expression_identity_collision"),
        ("manifestation_invalid", "canonical_manifestation_invalid"),
    ],
)
def test_manifest_structure_and_identity_failures_are_terminal(  # noqa: C901, PLR0912
    tmp_path: Path, case: str, error_class: str
) -> None:
    """Cumulative manifest validation covers shape, roots, and FRBR identity."""
    state = _write_valid_state(tmp_path)
    manifest = state["manifest"]
    if case == "records_not_list":
        manifest["records"] = {}
    elif case == "records_empty":
        manifest["records"] = []
    elif case == "record_not_object":
        manifest["records"] = [1]
    elif case == "count_bool":
        manifest["total_records"] = True
    elif case == "count_string":
        manifest["total_records"] = "3"
    elif case == "inventory_not_list":
        manifest["discovered_work_ids"] = "work-1"
    elif case == "inventory_bad_item":
        manifest["discovered_work_ids"] = [""]
    elif case == "inventory_not_canonical":
        manifest["discovered_work_ids"] = ["work-2", "work-1", "prior-work"]
    elif case == "inventory_count_bool":
        manifest["discovered_works_count"] = True
    elif case == "inventory_count_string":
        manifest["discovered_works_count"] = "3"
    elif case == "inventory_count_wrong":
        manifest["discovered_works_count"] = 99
    elif case == "record_schema":
        manifest["records"][1]["schema_version"] = "unsupported"
        _rewrite_manifest_with_root(state)
    elif case == "document_missing":
        manifest["records"][1]["document_id"] = None
        _rewrite_manifest_with_root(state)
    elif case == "document_duplicate":
        manifest["records"][2]["document_id"] = manifest["records"][1]["document_id"]
        _rewrite_manifest_with_root(state)
    elif case == "expression_invalid":
        manifest["records"][1]["expression_id"] = []
        _rewrite_manifest_with_root(state)
    elif case == "expression_collision":
        manifest["records"][2]["expression_id"] = manifest["records"][1][
            "expression_id"
        ]
        _rewrite_manifest_with_root(state)
    elif case == "manifestation_invalid":
        manifest["records"][1]["manifestation_id"] = []
        _rewrite_manifest_with_root(state)
    if case in {
        "records_not_list",
        "records_empty",
        "record_not_object",
        "count_bool",
        "count_string",
        "inventory_not_list",
        "inventory_bad_item",
        "inventory_not_canonical",
        "inventory_count_bool",
        "inventory_count_string",
        "inventory_count_wrong",
    }:
        _rewrite(state["manifest_path"], manifest)
    with pytest.raises(OneBatchReconciliationError, match=error_class):
        _reconcile(state)


@pytest.mark.parametrize(
    ("missing_key", "error_class"),
    [
        ("batch_path", "batch_missing"),
        ("manifest_path", "manifest_missing"),
        ("checkpoint_path", "checkpoint_missing"),
        ("cas_path", "cas_missing"),
    ],
)
def test_reconciliation_rejects_missing_real_inputs(
    tmp_path: Path, missing_key: str, error_class: str
) -> None:
    """No absent input can be replaced with generated evidence."""
    state = _write_valid_state(tmp_path)
    state[missing_key] = tmp_path / f"missing-{missing_key}"
    with pytest.raises(OneBatchReconciliationError, match=error_class):
        _reconcile(state)


def test_reconciliation_rejects_wrong_batch_hash(tmp_path: Path) -> None:
    """A supplied donor batch must match its independently declared digest."""
    state = _write_valid_state(tmp_path)
    state["expected_batch_sha256"] = "0" * 64
    with pytest.raises(OneBatchReconciliationError, match="batch_sha256_mismatch"):
        _reconcile(state)


@pytest.mark.parametrize(
    ("case", "error_class"),
    [
        ("manifest_not_object", "manifest_not_object"),
        ("manifest_schema", "manifest_schema_unsupported"),
        ("manifest_count", "manifest_record_count_mismatch"),
        ("manifest_root", "manifest_root_mismatch"),
        ("inventory_root", "inventory_root_mismatch"),
        ("record_schema", "manifest_record_invalid"),
        ("expression_missing", "canonical_expression_missing"),
        ("manifestation_duplicate", "manifestation_identity_duplicate"),
        ("checkpoint_schema", "checkpoint_schema_unsupported"),
        ("batch_not_completed", "batch_not_completed"),
        ("checkpoint_root", "checkpoint_manifest_root_mismatch"),
        ("checkpoint_count", "checkpoint_record_count_mismatch"),
        ("batch_not_discovered", "manifest_work_not_discovered"),
        ("batch_not_processed", "batch_work_not_processed"),
        ("batch_not_manifested", "batch_work_not_manifested"),
        ("cas_corrupt", "cas_object_corrupt"),
        ("blake3_mismatch", "cas_blake3_mismatch"),
    ],
)
def test_reconciliation_fails_closed_on_divergent_state(  # noqa: C901, PLR0912, PLR0915
    tmp_path: Path, case: str, error_class: str
) -> None:
    """Every identity, root, accounting, and byte divergence is terminal."""
    state = _write_valid_state(tmp_path)
    manifest = state["manifest"]
    checkpoint = state["checkpoint"]

    if case == "manifest_not_object":
        _rewrite(state["manifest_path"], [])
    elif case == "manifest_schema":
        manifest["schema_version"] = "unsupported"
        _rewrite(state["manifest_path"], manifest)
    elif case == "manifest_count":
        manifest["total_records"] = 99
        _rewrite(state["manifest_path"], manifest)
    elif case == "manifest_root":
        manifest["manifest_sha256"] = "0" * 64
        _rewrite(state["manifest_path"], manifest)
    elif case == "inventory_root":
        manifest["discovered_inventory_sha256"] = "0" * 64
        _rewrite(state["manifest_path"], manifest)
    elif case == "record_schema":
        manifest["records"][1]["canonical_uri"] = 1
        manifest["manifest_sha256"] = compute_legislation_manifest_sha256(
            manifest["records"]
        )
        _rewrite(state["manifest_path"], manifest)
    elif case == "expression_missing":
        manifest["records"][1]["expression_id"] = None
        manifest["manifest_sha256"] = compute_legislation_manifest_sha256(
            manifest["records"]
        )
        _rewrite(state["manifest_path"], manifest)
        checkpoint["metadata"]["manifest_sha256"] = manifest["manifest_sha256"]
        _rewrite(state["checkpoint_path"], checkpoint)
    elif case == "manifestation_duplicate":
        manifest["records"][2]["manifestation_id"] = manifest["records"][1][
            "manifestation_id"
        ]
        manifest["manifest_sha256"] = compute_legislation_manifest_sha256(
            manifest["records"]
        )
        _rewrite(state["manifest_path"], manifest)
    elif case == "checkpoint_schema":
        checkpoint["schema_version"] = "unsupported"
        _rewrite(state["checkpoint_path"], checkpoint)
    elif case == "batch_not_completed":
        checkpoint["completed_batches"].remove("batch-1")
        _rewrite(state["checkpoint_path"], checkpoint)
    elif case == "checkpoint_root":
        checkpoint["metadata"]["manifest_sha256"] = "0" * 64
        _rewrite(state["checkpoint_path"], checkpoint)
    elif case == "checkpoint_count":
        checkpoint["total_records_preserved"] = 99
        _rewrite(state["checkpoint_path"], checkpoint)
    elif case == "batch_not_discovered":
        manifest["discovered_work_ids"].remove("work-2")
        manifest["discovered_works_count"] = len(manifest["discovered_work_ids"])
        manifest["discovered_inventory_sha256"] = compute_legislation_inventory_sha256(
            manifest["discovered_work_ids"]
        )
        _rewrite(state["manifest_path"], manifest)
        checkpoint["metadata"]["discovered_inventory_sha256"] = manifest[
            "discovered_inventory_sha256"
        ]
        _rewrite(state["checkpoint_path"], checkpoint)
    elif case == "batch_not_processed":
        checkpoint["processed_work_ids"].remove("work-2")
        checkpoint["last_processed_index"] = len(checkpoint["processed_work_ids"])
        _rewrite(state["checkpoint_path"], checkpoint)
    elif case == "batch_not_manifested":
        removed = manifest["records"].pop()
        assert removed["work_id"] == "work-2"
        manifest["total_records"] = len(manifest["records"])
        manifest["manifest_sha256"] = compute_legislation_manifest_sha256(
            manifest["records"]
        )
        _rewrite(state["manifest_path"], manifest)
        checkpoint["total_records_preserved"] = len(manifest["records"])
        checkpoint["metadata"]["manifest_sha256"] = manifest["manifest_sha256"]
        _rewrite(state["checkpoint_path"], checkpoint)
    elif case == "cas_corrupt":
        digest = manifest["records"][1]["raw_cas_hash_sha256"]
        object_path = state["cas_path"] / "sha256" / digest[:2] / digest
        object_path.write_bytes(b"corrupt")
    elif case == "blake3_mismatch":
        manifest["records"][1]["raw_cas_hash_blake3"] = "0" * 64
        manifest["manifest_sha256"] = compute_legislation_manifest_sha256(
            manifest["records"]
        )
        _rewrite(state["manifest_path"], manifest)
        checkpoint["metadata"]["manifest_sha256"] = manifest["manifest_sha256"]
        _rewrite(state["checkpoint_path"], checkpoint)

    with pytest.raises(OneBatchReconciliationError, match=error_class):
        _reconcile(state)


@pytest.mark.parametrize(
    ("case", "error_class"),
    [
        ("completed_invalid", "checkpoint_completed_batches_invalid"),
        ("completed_duplicate", "checkpoint_completed_batches_duplicate"),
        ("processed_invalid", "checkpoint_processed_work_ids_invalid"),
        ("processed_duplicate", "checkpoint_processed_work_ids_duplicate"),
        ("processed_order", "checkpoint_processed_work_ids_not_canonical"),
        ("processed_count_bool", "checkpoint_processed_count_mismatch"),
        ("processed_count_string", "checkpoint_processed_count_mismatch"),
        ("processed_count_wrong", "checkpoint_processed_count_mismatch"),
        ("record_count_bool", "checkpoint_record_count_mismatch"),
        ("record_count_string", "checkpoint_record_count_mismatch"),
        ("metadata_invalid", "checkpoint_metadata_invalid"),
        ("inventory_root", "checkpoint_inventory_root_mismatch"),
        ("conditionals_invalid", "checkpoint_conditionals_invalid"),
    ],
)
def test_checkpoint_shape_and_accounting_failures_are_terminal(  # noqa: C901, PLR0912
    tmp_path: Path, case: str, error_class: str
) -> None:
    """Checkpoint lists, counters, roots, and conditional state must agree."""
    state = _write_valid_state(tmp_path)
    checkpoint = state["checkpoint"]
    if case == "completed_invalid":
        checkpoint["completed_batches"] = "batch-1"
    elif case == "completed_duplicate":
        checkpoint["completed_batches"].append("batch-1")
    elif case == "processed_invalid":
        checkpoint["processed_work_ids"] = [""]
    elif case == "processed_duplicate":
        checkpoint["processed_work_ids"].append("work-2")
    elif case == "processed_order":
        checkpoint["processed_work_ids"] = list(
            reversed(checkpoint["processed_work_ids"])
        )
    elif case == "processed_count_bool":
        checkpoint["last_processed_index"] = True
    elif case == "processed_count_string":
        checkpoint["last_processed_index"] = "3"
    elif case == "processed_count_wrong":
        checkpoint["last_processed_index"] = 99
    elif case == "record_count_bool":
        checkpoint["total_records_preserved"] = True
    elif case == "record_count_string":
        checkpoint["total_records_preserved"] = "3"
    elif case == "metadata_invalid":
        checkpoint["metadata"] = []
    elif case == "inventory_root":
        checkpoint["metadata"]["discovered_inventory_sha256"] = "0" * 64
    elif case == "conditionals_invalid":
        checkpoint["metadata"]["conditional_requests"] = []
    _rewrite(state["checkpoint_path"], checkpoint)
    with pytest.raises(OneBatchReconciliationError, match=error_class):
        _reconcile(state)


def test_batch_must_be_present_in_inventory_and_processed_set(tmp_path: Path) -> None:
    """A valid target cannot pass for a different, unprocessed donor identity."""
    state = _write_valid_state(tmp_path)
    state["batch_path"].write_text("work-3\n", encoding="utf-8")
    state["expected_batch_sha256"] = hashlib.sha256(b"work-3\n").hexdigest()
    with pytest.raises(OneBatchReconciliationError, match="batch_work_not_discovered"):
        _reconcile(state)

    processed_root = tmp_path / "processed"
    processed_root.mkdir()
    state = _write_valid_state(processed_root)
    state["checkpoint"]["processed_work_ids"].remove("work-2")
    state["checkpoint"]["last_processed_index"] = len(
        state["checkpoint"]["processed_work_ids"]
    )
    _rewrite(state["checkpoint_path"], state["checkpoint"])
    with pytest.raises(OneBatchReconciliationError, match="batch_work_not_processed"):
        _reconcile(state)


@pytest.mark.parametrize(
    ("case", "error_class"),
    [
        ("manifestation_missing", "canonical_manifestation_missing"),
        ("sha_invalid", "manifest_record_invalid"),
        ("byte_size_bool", "manifest_record_invalid"),
        ("byte_size_string", "manifest_record_invalid"),
        ("byte_size_wrong", "cas_byte_size_mismatch"),
    ],
)
def test_selected_record_and_cas_metadata_failures_are_terminal(
    tmp_path: Path, case: str, error_class: str
) -> None:
    """Selected records require complete identity and matching streamed bytes."""
    state = _write_valid_state(tmp_path)
    record = state["manifest"]["records"][1]
    if case == "manifestation_missing":
        record["manifestation_id"] = None
    elif case == "sha_invalid":
        record["raw_cas_hash_sha256"] = "bad"
    elif case == "byte_size_bool":
        record["byte_size"] = True
    elif case == "byte_size_string":
        record["byte_size"] = "3"
    elif case == "byte_size_wrong":
        record["byte_size"] = 99
    _rewrite_manifest_with_root(state)
    with pytest.raises(OneBatchReconciliationError, match=error_class):
        _reconcile(state)


def test_cas_layout_rejects_missing_object_root_and_symlink(tmp_path: Path) -> None:
    """CAS verification cannot traverse a missing or redirected object layout."""
    state = _write_valid_state(tmp_path)
    objects_root = state["cas_path"] / "sha256"
    renamed = state["cas_path"] / "objects-real"
    objects_root.rename(renamed)
    with pytest.raises(OneBatchReconciliationError, match="cas_layout_invalid"):
        _reconcile(state)
    objects_root.symlink_to(renamed, target_is_directory=True)
    with pytest.raises(OneBatchReconciliationError, match="cas_layout_invalid"):
        _reconcile(state)


def test_cas_layout_rejects_redirected_digest_prefix(tmp_path: Path) -> None:
    """A symlink inside the digest fan-out cannot redirect object verification."""
    state = _write_valid_state(tmp_path)
    digest = state["manifest"]["records"][1]["raw_cas_hash_sha256"]
    prefix = state["cas_path"] / "sha256" / digest[:2]
    relocated = state["cas_path"] / "sha256" / f"{digest[:2]}-real"
    prefix.rename(relocated)
    prefix.symlink_to(relocated, target_is_directory=True)
    with pytest.raises(OneBatchReconciliationError, match="cas_layout_invalid"):
        _reconcile(state)


def test_duplicate_selected_cas_object_is_stream_verified_once(tmp_path: Path) -> None:
    """Distinct manifestations may share bytes without duplicate verification."""
    state = _write_valid_state(tmp_path)
    first = state["manifest"]["records"][1]
    second = state["manifest"]["records"][2]
    for field in ("raw_cas_hash_sha256", "raw_cas_hash_blake3", "byte_size"):
        second[field] = first[field]
    _rewrite_manifest_with_root(state)
    receipt = _reconcile(state)
    assert receipt["selected_records_count"] == 2
    assert receipt["cas_objects_verified"] == 1


def test_failure_receipt_is_nonzero_and_schema_valid(tmp_path: Path) -> None:
    """A failed run writes bounded evidence without upgrading failure to parity."""
    state = _write_valid_state(tmp_path)
    receipt_path = tmp_path / "receipt.json"
    state["expected_batch_sha256"] = "0" * 64

    code = run_one_batch_reconciliation(
        batch_id="batch-1",
        batch_path=state["batch_path"],
        expected_batch_sha256=state["expected_batch_sha256"],
        manifest_path=state["manifest_path"],
        checkpoint_path=state["checkpoint_path"],
        cas_path=state["cas_path"],
        receipt_path=receipt_path,
        evaluated_at="2026-08-20T00:00:00Z",
    )

    assert code == 1
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt == {
        "schema_version": ("archive-govt-nz.legislation-one-batch-reconciliation/v1"),
        "status": "failed",
        "evaluated_at": "2026-08-20T00:00:00Z",
        "batch_id": "batch-1",
        "error_class": "batch_sha256_mismatch",
        "mismatch_count": 1,
        "mismatches": ["batch_sha256_mismatch"],
        "limitations": [
            "one_search_derived_batch_only",
            "not_corpus_completeness_evidence",
            "no_remote_publication_or_rights_verification",
        ],
    }

    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(receipt, schema)


def test_success_receipt_writer_and_schema(tmp_path: Path) -> None:
    """The wrapper persists the same validated receipt returned by the core."""
    state = _write_valid_state(tmp_path)
    receipt_path = tmp_path / "receipt.json"
    code = run_one_batch_reconciliation(
        batch_id="batch-1",
        batch_path=state["batch_path"],
        expected_batch_sha256=state["expected_batch_sha256"],
        manifest_path=state["manifest_path"],
        checkpoint_path=state["checkpoint_path"],
        cas_path=state["cas_path"],
        receipt_path=receipt_path,
        evaluated_at="2026-08-20T00:00:00Z",
    )
    assert code == 0
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(receipt, schema)


def test_cli_reconciles_only_explicit_local_state(tmp_path: Path) -> None:
    """The executable requires every local input and writes one bounded receipt."""
    state = _write_valid_state(tmp_path)
    receipt_path = tmp_path / "cli-receipt.json"
    namespace = runpy.run_path("tools/reconcile_one_legislation_batch.py")
    reconcile_main = cast("Callable[[list[str]], int]", namespace["main"])
    code = reconcile_main(
        [
            "--batch-id",
            "batch-1",
            "--batch-path",
            str(state["batch_path"]),
            "--expected-batch-sha256",
            state["expected_batch_sha256"],
            "--manifest-path",
            str(state["manifest_path"]),
            "--checkpoint-path",
            str(state["checkpoint_path"]),
            "--cas-path",
            str(state["cas_path"]),
            "--receipt-path",
            str(receipt_path),
        ]
    )
    assert code == 0
    assert json.loads(receipt_path.read_text(encoding="utf-8"))["status"] == "passed"


def test_superseded_generator_is_removed_and_receipts_are_invalidated() -> None:
    """Historical generated receipts remain provenance, never current evidence."""
    assert not Path("tools/generate_executable_legislation_parity.py").exists()
    invalidation = Path(
        "evidence/migrations/corpus-legislation-nz/parity/README.md"
    ).read_text(encoding="utf-8")
    assert "not valid operational" in invalidation
    assert "must not be committed" in invalidation
