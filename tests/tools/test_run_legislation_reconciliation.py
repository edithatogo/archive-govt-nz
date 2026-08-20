"""Tests for monthly legislation reconciliation runner and inventory integrity."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.domains.legislation.manifest import (
    compute_legislation_inventory_sha256,
)

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = Path(__file__).parents[2] / "tools" / "run_legislation_reconciliation.py"
_SPEC = importlib.util.spec_from_file_location(
    "run_legislation_reconciliation", _TOOL_PATH
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

reconcile_inventory = _MODULE.reconcile_inventory
run_monthly_reconciliation = _MODULE.run_monthly_reconciliation
main = _MODULE.main


def test_reconcile_inventory_consistent(tmp_path: Path) -> None:
    """Verify inventory reconciliation passes cleanly on consistent state."""
    manifest_file = tmp_path / "manifest.json"
    manifest_data = {
        "records": [
            {
                "schema_version": "archive-govt-nz.legislation/v2",
                "document_id": "leg-act-public-2024-0001",
                "work_id": "act-public-2024-0001",
                "expression_id": "exp-1",
                "manifestation_id": "man-1",
                "title": "Appropriation Act 2024",
                "legislation_type": "act",
                "status": "in_force",
                "canonical_uri": (
                    "https://www.legislation.govt.nz/act/public/2024/0001/latest/whole.html"
                ),
                "raw_cas_hash_sha256": (
                    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
                ),
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

    report = reconcile_inventory(
        manifest_path=manifest_file,
        checkpoint_path=checkpoint_file,
        candidate_works_denominator=100,
        hosted_dataset_slug="edithatogo/corpus-legislation-nz",
    )

    assert report["status"] == "consistent"
    assert report["total_manifest_records"] == 1
    assert report["distinct_works_count"] == 1
    assert report["coverage_percent"] == 1.0
    assert report["checkpoint_gaps_count"] == 0
    assert report["manifest_gaps_count"] == 0


def test_reconcile_inventory_missing_manifest(tmp_path: Path) -> None:
    """Verify missing manifest raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError, match="missing"):
        reconcile_inventory(
            manifest_path=tmp_path / "non_existent.json",
            checkpoint_path=tmp_path / "chk.json",
        )


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ({"discovered_works_count": 2}, "count does not match"),
        ({"discovered_inventory_sha256": "0" * 64}, "root does not match"),
        ({"discovered_work_ids": ["work-2", "work-1"]}, "canonical"),
    ],
)
def test_reconcile_inventory_rejects_unauthenticated_discovery_denominator(
    tmp_path: Path, mutation: dict[str, object], error: str
) -> None:
    """Reject a discovered denominator that is not bound to its inventory root."""
    work_ids = ["work-1"]
    manifest_data: dict[str, object] = {
        "records": [],
        "discovered_work_ids": work_ids,
        "discovered_works_count": len(work_ids),
        "discovered_inventory_sha256": compute_legislation_inventory_sha256(work_ids),
    }
    manifest_data.update(mutation)
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")
    checkpoint_file = tmp_path / "checkpoint.json"
    checkpoint_file.write_text(json.dumps({"processed_work_ids": []}), encoding="utf-8")

    with pytest.raises(ValueError, match=error):
        reconcile_inventory(
            manifest_path=manifest_file,
            checkpoint_path=checkpoint_file,
        )


def test_reconcile_inventory_uses_authenticated_discovery_denominator(
    tmp_path: Path,
) -> None:
    """Use the authenticated discovered inventory as the coverage denominator."""
    work_ids = ["work-1", "work-2"]
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(
        json.dumps(
            {
                "records": [],
                "discovered_work_ids": work_ids,
                "discovered_works_count": len(work_ids),
                "discovered_inventory_sha256": (
                    compute_legislation_inventory_sha256(work_ids)
                ),
            }
        ),
        encoding="utf-8",
    )
    checkpoint_file = tmp_path / "checkpoint.json"
    checkpoint_file.write_text(json.dumps({"processed_work_ids": []}), encoding="utf-8")

    report = reconcile_inventory(
        manifest_path=manifest_file,
        checkpoint_path=checkpoint_file,
    )

    assert report["candidate_works_denominator"] == 2


def test_run_monthly_reconciliation_runner(tmp_path: Path) -> None:
    """Verify run_monthly_reconciliation generates receipt file."""
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps({"records": []}), encoding="utf-8")

    checkpoint_file = tmp_path / "checkpoint.json"
    checkpoint_file.write_text(json.dumps({"processed_work_ids": []}), encoding="utf-8")

    receipt_file = tmp_path / "receipt.json"

    code = run_monthly_reconciliation(
        manifest_path=manifest_file,
        checkpoint_path=checkpoint_file,
        receipt_path=receipt_file,
    )
    assert code == 0
    assert receipt_file.is_file()
    data = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert data["candidate_works_denominator"] == 0
    assert data["coverage_percent"] == 0.0


def test_run_monthly_reconciliation_failure(tmp_path: Path) -> None:
    """Verify runner handles missing input with non-zero exit code and error receipt."""
    receipt_file = tmp_path / "receipt.json"
    code = run_monthly_reconciliation(
        manifest_path=tmp_path / "non_existent.json",
        checkpoint_path=tmp_path / "chk.json",
        receipt_path=receipt_file,
    )
    assert code == 1
    assert receipt_file.is_file()
    data = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert data["status"] == "failed"


def test_main_reconciliation_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify main entrypoint handles CLI flags."""
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps({"records": []}), encoding="utf-8")

    checkpoint_file = tmp_path / "checkpoint.json"
    checkpoint_file.write_text(json.dumps({"processed_work_ids": []}), encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_legislation_reconciliation.py",
            "--manifest-path",
            str(manifest_file),
            "--checkpoint-path",
            str(checkpoint_file),
            "--receipt-path",
            str(tmp_path / "receipt.json"),
        ],
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
