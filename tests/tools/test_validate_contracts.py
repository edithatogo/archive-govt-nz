"""Tests for contract validation tool."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_validate_contracts_tool() -> None:
    """The contract validator successfully validates all repository contracts."""
    root = Path(__file__).parents[2]
    result = subprocess.run(
        ["uv", "run", "--locked", "python", "tools/validate_contracts.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "VALIDATED successfully" in result.stdout
