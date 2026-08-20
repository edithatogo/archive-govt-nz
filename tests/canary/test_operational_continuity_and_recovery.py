"""Tests for operational continuity cycles and clean workspace recovery drill."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.domains.legislation.models import (
    LegislationRecord,
    LegislationType,
    VersionStatus,
)

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = (
    Path(__file__).parents[2]
    / "tools"
    / "verify_operational_continuity_and_recovery.py"
)
_SPEC = importlib.util.spec_from_file_location(
    "verify_operational_continuity_and_recovery", _TOOL_PATH
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

execute_operational_continuity_and_recovery = (
    _MODULE.execute_operational_continuity_and_recovery
)
load_canonical_sample_records = _MODULE.load_canonical_sample_records
run_clean_workspace_recovery_drill = _MODULE.run_clean_workspace_recovery_drill
main = _MODULE.main


def test_run_clean_workspace_recovery_drill(tmp_path: Path) -> None:
    """Verify clean workspace recovery drill reconstructs derivatives and parity."""
    records = load_canonical_sample_records()
    workspace = tmp_path / "workspace"

    result = run_clean_workspace_recovery_drill(records, workspace_dir=workspace)

    assert result["status"] == "passed"
    assert result["manifest_root_match"] is True
    assert result["recovered_records_count"] == len(records)
    assert result["mismatches"] == []
    assert result["parquet_size_bytes"] > 0
    assert result["jsonl_size_bytes"] > 0
    assert (workspace / "data/corpus.parquet").is_file()
    assert (workspace / "data/corpus.jsonl").is_file()
    assert (workspace / "checkpoint.json").is_file()


def test_recovery_drill_negative_control_corrupted_cas(tmp_path: Path) -> None:
    """Negative control: corrupted CAS hash in record fails parity and reports error."""
    records = load_canonical_sample_records()
    corrupted_records = [
        LegislationRecord(
            document_id=records[0].document_id,
            work_id=records[0].work_id,
            expression_id=records[0].expression_id,
            manifestation_id=records[0].manifestation_id,
            title=records[0].title,
            legislation_type=LegislationType.ACT,
            status=VersionStatus.IN_FORCE,
            canonical_uri=records[0].canonical_uri,
            raw_cas_hash_sha256=(
                "0000000000000000000000000000000000000000000000000000000000000000"
            ),
            raw_cas_hash_blake3=records[0].raw_cas_hash_blake3,
            retrieval_timestamp=records[0].retrieval_timestamp,
        )
    ]
    workspace = tmp_path / "corrupted_workspace"

    result = run_clean_workspace_recovery_drill(
        corrupted_records, workspace_dir=workspace
    )

    assert result["status"] == "failed"
    assert result["mismatches_count"] > 0
    assert any("CAS SHA-256 mismatch" in m for m in result["mismatches"])


def test_execute_operational_continuity_and_recovery(tmp_path: Path) -> None:
    """Verify operational continuity execution records 2 cycles and valid receipt."""
    receipt_path = tmp_path / "continuity_receipt.json"

    receipt = execute_operational_continuity_and_recovery(receipt_path=receipt_path)

    assert receipt["status"] == "passed"
    assert receipt["operational_cycles_count"] == 2
    assert receipt["remote_publish_attempted"] is False
    assert receipt_path.is_file()

    data = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert data["operational_cycles"][0]["cycle_type"] == "scheduled_weekly_harvest"
    assert data["operational_cycles"][1]["cycle_type"] == "monthly_reconciliation"
    assert data["recovery_drill"]["manifest_root_match"] is True


def test_main_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify CLI entrypoint executes and exits 0 on success."""
    receipt_path = tmp_path / "cli_receipt.json"

    monkeypatch.setattr(
        "sys.argv",
        [
            "verify_operational_continuity_and_recovery.py",
            "--receipt-path",
            str(receipt_path),
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert receipt_path.is_file()
