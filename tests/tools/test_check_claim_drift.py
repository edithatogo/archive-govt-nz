"""Tests for the Conductor claim drift detection tool."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[2]))

from tools.check_claim_drift import check_claims, main


def test_check_claims_all_matching() -> None:
    """Check claims succeeds when live GitHub state matches recorded claims."""
    mock_data = {
        "edithatogo/corpus-legislation-nz": {"archived": True, "open_issues_count": 0},
        "edithatogo/sm-govt-nz": {"archived": False, "open_issues_count": 0},
    }
    status, checks = check_claims(mock_live_data=mock_data)
    assert status == "passed"
    assert len(checks) == 2
    assert all(c.status == "match" for c in checks)


def test_check_claims_detects_divergence() -> None:
    """Check claims fails when live repository state drifts from claims."""
    mock_data = {
        # Drifts: corpus-legislation-nz was supposed to be archived
        "edithatogo/corpus-legislation-nz": {"archived": False},
        "edithatogo/sm-govt-nz": {"archived": False},
    }
    status, checks = check_claims(mock_live_data=mock_data)
    assert status == "divergence_detected"
    drift_checks = [c for c in checks if c.status == "drift"]
    assert len(drift_checks) == 1
    assert drift_checks[0].subject == "edithatogo/corpus-legislation-nz"


def test_main_cli_execution(tmp_path: Path) -> None:
    """CLI execution generates schema-compliant receipt and exits 0 on match."""
    mock_file = tmp_path / "mock.json"
    mock_file.write_text(
        json.dumps(
            {
                "edithatogo/corpus-legislation-nz": {"archived": True},
                "edithatogo/sm-govt-nz": {"archived": False},
            }
        ),
        encoding="utf-8",
    )
    receipt_file = tmp_path / "receipt.json"

    ret = main(
        [
            "--mock-json",
            str(mock_file),
            "--output",
            str(receipt_file),
        ]
    )
    assert ret == 0
    assert receipt_file.exists()
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt["schema_version"] == "archive-govt-nz.claim-drift-receipt/v1"
    assert receipt["status"] == "passed"
    assert receipt["divergences_detected"] == 0
