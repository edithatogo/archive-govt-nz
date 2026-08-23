"""Tests for optional Scalene profiling integration."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import TYPE_CHECKING

from archive_govt_nz.profiling import ProfilingResult, profile_execution

if TYPE_CHECKING:
    from pathlib import Path


def test_profile_execution_enabled(tmp_path: Path) -> None:
    """Test profiling context manager when enabled."""
    out_file = tmp_path / "profile.json"
    with profile_execution(output_path=out_file, enabled=True) as result:
        assert isinstance(result, ProfilingResult)
        assert result.enabled is True
        assert result.output_path == str(out_file)
        total = sum(i * i for i in range(100))
        assert total > 0


def test_profile_execution_disabled() -> None:
    """Test profiling context manager when disabled."""
    with profile_execution(enabled=False) as result:
        assert isinstance(result, ProfilingResult)
        assert result.enabled is False
        assert result.output_path is None


def test_test_profiler_fixture(test_profiler: ProfilingResult) -> None:
    """Test pytest fixture integration for test profiling."""
    assert isinstance(test_profiler, ProfilingResult)
    assert test_profiler.enabled is True


def test_profile_runner_cli(tmp_path: Path) -> None:
    """Test profile_runner CLI execution via subprocess."""
    out_file = tmp_path / "cli-profile.json"
    proc = subprocess.run(
        [
            sys.executable,
            "tools/profile_runner.py",
            "--target",
            "bronze-manifest",
            "--output",
            str(out_file),
        ],
        capture_output=True,
        text=True,
        check=False,
        env={"PYTHONPATH": ".", **os.environ},
    )
    assert proc.returncode == 0
    assert "Profiling completed: target=bronze-manifest" in proc.stdout
