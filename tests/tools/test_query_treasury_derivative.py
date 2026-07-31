"""Tests for the bounded read-only analytical query command."""

import subprocess
from pathlib import Path


def test_query_command_reads_derivative() -> None:
    root = Path(__file__).parents[2]
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/query_treasury_derivative.py",
            "--parquet",
            "build/derivatives/treasury/datasets.parquet",
            "--sql",
            "SELECT count(*) AS n FROM read_parquet(?)",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"n": 54' in result.stdout
