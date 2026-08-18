"""Anti-simulation and completion evaluator test suite."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


def test_evaluator_fails_on_current_incomplete_branch() -> None:
    """The completion evaluator must report INCOMPLETE and exit non-zero on current repo."""
    root = Path(__file__).parents[2]
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/evaluate_legislation_completion.py",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "INCOMPLETE" in result.stdout
    assert "[BLOCKER]" in result.stdout


def test_evaluator_detects_fixed_constants_in_codebase(tmp_path: Path) -> None:
    """The scanner must detect hardcoded constants or fake coverage returns."""
    root = Path(__file__).parents[2]
    src_dir = tmp_path / "src" / "archive_govt_nz"
    src_dir.mkdir(parents=True)
    fake_cli = src_dir / "cli.py"
    fake_cli.write_text('payload = {"coverage_percent": 100.0}\n', encoding="utf-8")

    # Run evaluate tool against temp path
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            str(root / "tools/evaluate_legislation_completion.py"),
            "--output",
            str(tmp_path / "report.json"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "INCOMPLETE" in result.stdout


def test_evaluator_negative_control_fake_passing_receipt(tmp_path: Path) -> None:
    """Providing a fake 'passed' receipt inside a temp directory must still fail."""
    root = Path(__file__).parents[2]
    schema_dir = tmp_path / "schemas" / "contracts" / "v1"
    schema_dir.mkdir(parents=True)
    shutil.copy(
        root / "schemas/contracts/v1/contract.schema.json",
        schema_dir / "contract.schema.json",
    )

    ev_dir = tmp_path / "evidence" / "migrations" / "corpus-legislation-nz"
    ev_dir.mkdir(parents=True)
    fake_receipt = ev_dir / "observation-receipt.json"
    fake_receipt.write_text(json.dumps({"status": "passed"}), encoding="utf-8")

    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            str(root / "tools/evaluate_legislation_completion.py"),
            "--output",
            str(tmp_path / "report.json"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "INCOMPLETE" in result.stdout


def test_evaluator_fails_when_child_tracks_are_in_progress(tmp_path: Path) -> None:
    """The evaluator fails if any corrective child track is in_progress."""
    root = Path(__file__).parents[2]
    tracks_dir = (
        tmp_path / "conductor" / "tracks" / "legislation_corrective_test_20260818"
    )
    tracks_dir.mkdir(parents=True)
    meta = tracks_dir / "metadata.json"
    meta.write_text(
        json.dumps(
            {
                "id": "legislation_corrective_test",
                "status": "in_progress",
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            str(root / "tools/evaluate_legislation_completion.py"),
            "--output",
            str(tmp_path / "report.json"),
        ],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "INCOMPLETE" in result.stdout
