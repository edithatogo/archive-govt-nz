"""Tests for authenticated sharded-CAS legislation recovery."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

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

_TOOL_PATH = Path(__file__).parents[2] / "tools" / "run_legislation_recovery_drill.py"
_SPEC = importlib.util.spec_from_file_location(
    "run_legislation_recovery_drill", _TOOL_PATH
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

execute_recovery_drill = _MODULE.execute_recovery_drill
run_quarterly_recovery_drill = _MODULE.run_quarterly_recovery_drill
main = _MODULE.main


def _authenticated_state(tmp_path: Path) -> tuple[Path, Path, Path]:
    cas_path = tmp_path / "cas"
    receipt = ContentAddressedStore(cas_path).put_bytes(
        b"<act><title>Test Act</title></act>"
    )
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
    manifest = build_legislation_manifest(
        [record], run_id="batch-a", discovered_work_ids=[record.work_id]
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    checkpoint = {
        "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
        "last_updated": "2026-08-20T00:00:00Z",
        "completed_batches": ["batch-a"],
        "processed_work_ids": [record.work_id],
        "last_processed_index": 1,
        "total_records_preserved": 1,
        "metadata": {
            "manifest_sha256": manifest["manifest_sha256"],
            "discovered_inventory_sha256": manifest["discovered_inventory_sha256"],
            "conditional_requests": {},
        },
    }
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    return checkpoint_path, manifest_path, cas_path


def test_execute_recovery_drill_streams_verified_sharded_state(tmp_path: Path) -> None:
    """Reconstruct an authenticated object into a fresh canonical CAS."""
    checkpoint, manifest, cas = _authenticated_state(tmp_path)
    recovery = tmp_path / "recovery"
    report = execute_recovery_drill(checkpoint, manifest, cas, recovery)
    assert report["status"] == "verified"
    assert report["cas_objects_reconstructed"] == 1
    assert len(list((recovery / "cas" / "sha256").glob("*/*"))) == 1


def test_recovery_rejects_missing_or_nonempty_state(tmp_path: Path) -> None:
    """Fail closed for missing retained state or a non-clean recovery target."""
    with pytest.raises(FileNotFoundError, match="checkpoint"):
        execute_recovery_drill(
            tmp_path / "missing.json",
            tmp_path / "manifest.json",
            tmp_path / "cas",
            tmp_path / "recovery",
        )
    checkpoint, manifest, cas = _authenticated_state(tmp_path)
    recovery = tmp_path / "nonempty"
    recovery.mkdir()
    (recovery / "unexpected").write_text("state", encoding="utf-8")
    with pytest.raises(ValueError, match="new or empty"):
        execute_recovery_drill(checkpoint, manifest, cas, recovery)


def test_recovery_rejects_corrupt_cas(tmp_path: Path) -> None:
    """Reject source bytes that do not match the manifest object identity."""
    checkpoint, manifest, cas = _authenticated_state(tmp_path)
    object_path = next((cas / "sha256").glob("*/*"))
    object_path.write_bytes(b"corrupt")
    with pytest.raises(Exception, match="object_corrupt"):
        execute_recovery_drill(checkpoint, manifest, cas, tmp_path / "recovery-corrupt")


def test_recovery_runner_writes_blocked_receipt_on_invalid_state(
    tmp_path: Path,
) -> None:
    """Return non-zero and a blocked receipt when retained state is absent."""
    receipt = tmp_path / "receipt.json"
    code = run_quarterly_recovery_drill(
        checkpoint_path=tmp_path / "missing.json",
        manifest_path=tmp_path / "manifest.json",
        cas_path=tmp_path / "cas",
        recovery_dir=tmp_path / "recovery",
        receipt_path=receipt,
    )
    assert code == 1
    assert json.loads(receipt.read_text(encoding="utf-8"))["status"] == "blocked"


def test_main_recovery_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Run the explicit recovery CLI against authenticated state."""
    checkpoint, manifest, cas = _authenticated_state(tmp_path)
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_legislation_recovery_drill.py",
            "--checkpoint-path",
            str(checkpoint),
            "--manifest-path",
            str(manifest),
            "--cas-path",
            str(cas),
            "--recovery-dir",
            str(tmp_path / "recovery-main"),
            "--receipt-path",
            str(tmp_path / "receipt-main.json"),
        ],
    )
    with pytest.raises(SystemExit) as raised:
        main()
    assert raised.value.code == 0
