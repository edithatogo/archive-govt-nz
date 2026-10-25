"""Tests for the Conductor claim drift detection tool across all 5 donor repos."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from tools.check_claim_drift import check_claims, main

from tools import check_claim_drift


def test_check_claims_all_matching() -> None:
    """Check claims succeeds when live GitHub state matches recorded claims."""
    mock_data = {
        "edithatogo/corpus-legislation-nz": {"archived": True, "open_issues_count": 0},
        "edithatogo/sm-govt-nz": {"archived": True, "open_issues_count": 0},
        "edithatogo/corpus-nz-hansard": {"archived": True, "open_issues_count": 0},
        "edithatogo/hathi-nz": {"archived": True, "open_issues_count": 0},
        "edithatogo/corpus-cases-medilegal-nz": {
            "archived": True,
            "open_issues_count": 0,
        },
    }
    status, checks = check_claims(mock_live_data=mock_data)
    assert status == "passed"
    assert len(checks) == 5
    assert all(c.status == "match" for c in checks)


def test_check_claims_detects_divergence() -> None:
    """Check claims fails when live repository state drifts from claims."""
    mock_data = {
        # Drifts: corpus-legislation-nz was supposed to be archived
        "edithatogo/corpus-legislation-nz": {"archived": False},
        "edithatogo/sm-govt-nz": {"archived": True},
        "edithatogo/corpus-nz-hansard": {"archived": True},
        "edithatogo/hathi-nz": {"archived": True},
        "edithatogo/corpus-cases-medilegal-nz": {"archived": True},
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
                "edithatogo/sm-govt-nz": {"archived": True},
                "edithatogo/corpus-nz-hansard": {"archived": True},
                "edithatogo/hathi-nz": {"archived": True},
                "edithatogo/corpus-cases-medilegal-nz": {"archived": True},
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
    assert receipt["claims_checked"] == 5
    assert receipt["divergences_detected"] == 0


def test_github_token_prefers_explicit_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prefer the workflow token without invoking the CLI credential helper."""
    monkeypatch.setenv("GH_TOKEN", "explicit-gh-token")
    monkeypatch.setenv("GITHUB_TOKEN", "explicit-github-token")
    monkeypatch.setattr(check_claim_drift.shutil, "which", lambda _: None)

    assert (
        check_claim_drift.github_token_from_environment_or_cli() == "explicit-gh-token"
    )


def test_github_token_uses_logged_in_cli_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use the existing gh credential when no token was passed by the runner."""
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr(check_claim_drift.shutil, "which", lambda _: "/usr/bin/gh")

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        assert command == ["/usr/bin/gh", "auth", "token", "--hostname", "github.com"]
        assert kwargs["capture_output"] is True
        return subprocess.CompletedProcess(command, 0, stdout="cli-token\n", stderr="")

    monkeypatch.setattr(check_claim_drift.subprocess, "run", run)

    assert check_claim_drift.github_token_from_environment_or_cli() == "cli-token"
