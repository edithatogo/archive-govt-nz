"""Tests for authenticated legislation inventory reconciliation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

from archive_govt_nz.domains.legislation.manifest import build_legislation_manifest
from archive_govt_nz.domains.legislation.models import (
    LegislationRecord,
    LegislationType,
    VersionStatus,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = Path(__file__).parents[2] / "tools/run_legislation_reconciliation.py"
_SPEC = importlib.util.spec_from_file_location(
    "run_legislation_reconciliation", _TOOL_PATH
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

authenticated_count = _MODULE._authenticated_discovered_count  # noqa: SLF001
reconcile_inventory = _MODULE.reconcile_inventory
run_monthly_reconciliation = _MODULE.run_monthly_reconciliation
main = _MODULE.main


def _state(tmp_path: Path, *, populated: bool = True) -> tuple[Path, Path, Path]:
    cas_path = tmp_path / "cas"
    store = ContentAddressedStore(cas_path)
    records: list[LegislationRecord] = []
    work_ids: list[str] = []
    if populated:
        receipt = store.put_bytes(b"<act><title>Test Act</title></act>")
        record = LegislationRecord(
            document_id="act-public-2024-0001",
            work_id="act-public-2024-0001",
            expression_id="act-public-2024-0001:expression:latest",
            manifestation_id="act-public-2024-0001:expression:latest:xml:whole",
            title="Test Act",
            legislation_type=LegislationType.ACT,
            status=VersionStatus.IN_FORCE,
            canonical_uri=(
                "https://www.legislation.govt.nz/act/public/2024/0001/latest/whole.xml"
            ),
            raw_cas_hash_sha256=receipt.sha256,
            raw_cas_hash_blake3=receipt.blake3,
            byte_size=receipt.byte_count,
            retrieval_timestamp="2026-08-20T00:00:00Z",
        )
        records = [record]
        work_ids = [record.work_id]
    manifest = build_legislation_manifest(
        records, run_id="batch-a", discovered_work_ids=work_ids
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    checkpoint: dict[str, Any] = {
        "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
        "last_updated": "2026-08-20T00:00:00Z" if populated else None,
        "completed_batches": ["batch-a"] if populated else [],
        "processed_work_ids": work_ids,
        "last_processed_index": len(work_ids),
        "total_records_preserved": len(records),
        "metadata": {
            "manifest_sha256": manifest["manifest_sha256"],
            "discovered_inventory_sha256": manifest["discovered_inventory_sha256"],
            "conditional_requests": {},
        },
    }
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    return manifest_path, checkpoint_path, cas_path


def test_reconcile_inventory_requires_linked_complete_state(tmp_path: Path) -> None:
    """Return consistency only for authenticated inventory, checkpoint, and CAS."""
    manifest, checkpoint, cas = _state(tmp_path)
    report = reconcile_inventory(manifest, checkpoint, cas)
    assert report["status"] == "consistent"
    assert report["candidate_works_denominator"] == 1
    assert report["coverage_percent"] == 100.0
    assert report["cas_objects_verified"] == 1
    assert report["unretrieved_discovered_works_count"] == 0


def test_discovery_inventory_authentication_rejects_mutations() -> None:
    """Reject missing, partial, noncanonical, or mismatched inventory evidence."""
    with pytest.raises(ValueError, match="missing"):
        authenticated_count({}, set())
    with pytest.raises(ValueError, match="incomplete"):
        authenticated_count({"discovered_works_count": 1}, set())
    with pytest.raises(ValueError, match="canonical"):
        authenticated_count(
            {
                "discovered_work_ids": ["b", "a"],
                "discovered_works_count": 2,
                "discovered_inventory_sha256": "0" * 64,
            },
            set(),
        )


def test_reconcile_rejects_denominator_override(tmp_path: Path) -> None:
    """Do not let a caller replace authenticated discovery evidence."""
    manifest, checkpoint, cas = _state(tmp_path)
    with pytest.raises(ValueError, match="overrides"):
        reconcile_inventory(manifest, checkpoint, cas, candidate_works_denominator=100)


def test_reconciliation_no_state_is_nonzero(tmp_path: Path) -> None:
    """Write an explicit no-state receipt without reporting success."""
    manifest, checkpoint, cas = _state(tmp_path, populated=False)
    receipt = tmp_path / "receipt.json"
    code = run_monthly_reconciliation(
        manifest_path=manifest,
        checkpoint_path=checkpoint,
        cas_path=cas,
        receipt_path=receipt,
    )
    assert code == 1
    assert json.loads(receipt.read_text(encoding="utf-8"))["status"] == "no_state"


def test_reconciliation_missing_state_writes_failed_receipt(tmp_path: Path) -> None:
    """Capture missing linked state as a non-zero failed receipt."""
    receipt = tmp_path / "receipt.json"
    code = run_monthly_reconciliation(
        manifest_path=tmp_path / "missing-manifest.json",
        checkpoint_path=tmp_path / "missing-checkpoint.json",
        cas_path=tmp_path / "missing-cas",
        receipt_path=receipt,
    )
    assert code == 1
    assert json.loads(receipt.read_text(encoding="utf-8"))["status"] == "failed"


def test_main_reconciliation_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run explicit reconciliation against all three linked state components."""
    manifest, checkpoint, cas = _state(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_legislation_reconciliation.py",
            "--manifest-path",
            str(manifest),
            "--checkpoint-path",
            str(checkpoint),
            "--cas-path",
            str(cas),
            "--receipt-path",
            str(tmp_path / "receipt.json"),
            "--hosted-dataset-slug",
            "",
        ],
    )
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0
