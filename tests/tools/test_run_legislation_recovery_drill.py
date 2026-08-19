"""Tests for quarterly legislation recovery drill and fixity assertions."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

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


def test_execute_recovery_drill_verified(tmp_path: Path) -> None:
    """Verify recovery drill succeeds and verifies hashes on intact CAS store."""
    cas_path = tmp_path / "cas"
    sha_dir = cas_path / "sha256"
    sha_dir.mkdir(parents=True)

    dummy_content = b"<act>Test Legislation</act>"
    sha256_hex = hashlib.sha256(dummy_content).hexdigest()
    (sha_dir / sha256_hex).write_bytes(dummy_content)

    manifest_file = tmp_path / "manifest.json"
    manifest_data = {
        "records": [
            {
                "schema_version": "archive-govt-nz.legislation/v2",
                "document_id": "act-public-2024-0001",
                "work_id": "act-public-2024-0001",
                "title": "Appropriation Act 2024",
                "legislation_type": "act",
                "status": "in_force",
                "canonical_uri": (
                    "https://www.legislation.govt.nz/act/public/2024/0001/latest/whole.html"
                ),
                "raw_cas_hash_sha256": sha256_hex,
                "raw_cas_hash_blake3": (
                    "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"
                ),
                "retrieval_timestamp": "2026-08-20T00:00:00Z",
            }
        ]
    }
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

    checkpoint_file = tmp_path / "checkpoint.json"
    checkpoint_data = {
        "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
        "processed_work_ids": ["act-public-2024-0001"],
    }
    checkpoint_file.write_text(json.dumps(checkpoint_data), encoding="utf-8")

    recovery_dir = tmp_path / "recovery"
    report = execute_recovery_drill(
        checkpoint_path=checkpoint_file,
        manifest_path=manifest_file,
        cas_path=cas_path,
        recovery_dir=recovery_dir,
    )

    assert report["status"] == "verified"
    assert report["cas_objects_reconstructed"] == 1
    assert report["mismatches_count"] == 0
    assert (recovery_dir / "cas" / "sha256" / sha256_hex).is_file()


def test_execute_recovery_drill_missing_checkpoint(tmp_path: Path) -> None:
    """Verify missing checkpoint raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="checkpoint"):
        execute_recovery_drill(
            checkpoint_path=tmp_path / "missing_chk.json",
            manifest_path=tmp_path / "man.json",
            cas_path=tmp_path / "cas",
            recovery_dir=tmp_path / "rec",
        )


def test_execute_recovery_drill_missing_manifest(tmp_path: Path) -> None:
    """Verify missing manifest raises FileNotFoundError."""
    chk = tmp_path / "chk.json"
    chk.write_text("{}", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="manifest"):
        execute_recovery_drill(
            checkpoint_path=chk,
            manifest_path=tmp_path / "missing_man.json",
            cas_path=tmp_path / "cas",
            recovery_dir=tmp_path / "rec",
        )


def test_run_quarterly_recovery_drill_runner(tmp_path: Path) -> None:
    """Verify recovery drill runner saves receipt."""
    chk = tmp_path / "chk.json"
    chk.write_text("{}", encoding="utf-8")
    man = tmp_path / "man.json"
    man.write_text(json.dumps({"records": []}), encoding="utf-8")
    receipt = tmp_path / "receipt.json"

    code = run_quarterly_recovery_drill(
        checkpoint_path=chk,
        manifest_path=man,
        cas_path=tmp_path / "cas",
        recovery_dir=tmp_path / "rec",
        receipt_path=receipt,
    )
    assert code == 0
    assert receipt.is_file()


def test_run_quarterly_recovery_drill_blocked(tmp_path: Path) -> None:
    """Verify missing retained state results in blocked receipt and code 1."""
    receipt = tmp_path / "receipt.json"
    code = run_quarterly_recovery_drill(
        checkpoint_path=tmp_path / "missing_chk.json",
        manifest_path=tmp_path / "missing_man.json",
        cas_path=tmp_path / "cas",
        recovery_dir=tmp_path / "rec",
        receipt_path=receipt,
    )
    assert code == 1
    assert receipt.is_file()
    data = json.loads(receipt.read_text(encoding="utf-8"))
    assert data["status"] == "blocked"


def test_main_recovery_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main entrypoint handles CLI flags."""
    chk = tmp_path / "chk.json"
    chk.write_text("{}", encoding="utf-8")
    man = tmp_path / "man.json"
    man.write_text(json.dumps({"records": []}), encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_legislation_recovery_drill.py",
            "--checkpoint-path",
            str(chk),
            "--manifest-path",
            str(man),
            "--cas-path",
            str(tmp_path / "cas"),
            "--recovery-dir",
            str(tmp_path / "rec"),
            "--receipt-path",
            str(tmp_path / "receipt.json"),
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
