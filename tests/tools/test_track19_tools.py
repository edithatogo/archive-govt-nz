"""Integration and CLI tests for Track 19 tools."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[2]


def test_recover_broken_urls_cli(tmp_path: Path) -> None:
    """CLI tool handles missing input file cleanly."""
    result = subprocess.run(
        [
            sys.executable,
            "tools/recover_broken_urls.py",
            "--input",
            str(tmp_path / "missing.json"),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Broken URLs file not found" in result.stdout


def test_build_analytical_derivatives_cli(tmp_path: Path) -> None:
    """CLI tool handles missing input file cleanly."""
    result = subprocess.run(
        [
            sys.executable,
            "tools/build_analytical_derivatives.py",
            "--input",
            str(tmp_path / "missing.json"),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Capture receipt not found" in result.stdout


def test_detect_catalogue_drift_cli(tmp_path: Path) -> None:
    """CLI tool handles missing files and computes deltas."""
    # 1. Missing file
    res_miss = subprocess.run(
        [
            sys.executable,
            "tools/detect_catalogue_drift.py",
            "--previous",
            str(tmp_path / "prev.json"),
            "--current",
            str(tmp_path / "curr.json"),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_miss.returncode == 1

    # 2. Success run
    prev_file = tmp_path / "prev.json"
    curr_file = tmp_path / "curr.json"
    out_file = tmp_path / "drift.json"

    manifest = {"observed_at": "2026-08-01T00:00:00Z", "datasets": []}
    prev_file.write_text(json.dumps(manifest), encoding="utf-8")
    curr_file.write_text(json.dumps(manifest), encoding="utf-8")

    res_ok = subprocess.run(
        [
            sys.executable,
            "tools/detect_catalogue_drift.py",
            "--previous",
            str(prev_file),
            "--current",
            str(curr_file),
            "--output",
            str(out_file),
        ],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_ok.returncode == 0
    assert out_file.is_file()


def test_check_slops_cli() -> None:
    """Hygiene gate executes and passes."""
    result = subprocess.run(
        [sys.executable, "tools/check_slops.py"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "Hygiene & Slop Gate: PASSED" in result.stdout


def test_benchmark_cas_cli() -> None:
    """Benchmark tool executes and passes."""
    result = subprocess.run(
        [sys.executable, "tools/benchmark_cas.py"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "CAS Streaming Throughput:" in result.stdout


def test_publish_to_huggingface_cli_missing_token() -> None:
    """CLI tool fails gracefully when token is absent."""
    result = subprocess.run(
        [sys.executable, "tools/publish_to_huggingface.py"],
        cwd=REPOSITORY_ROOT,
        capture_output=True,
        text=True,
        check=False,
        env={"PATH": os.environ.get("PATH", "")},
    )
    assert result.returncode == 1
    assert "Hugging Face token required" in result.stdout
