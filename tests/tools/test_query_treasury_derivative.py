"""Tests for the bounded read-only analytical query command."""

import subprocess
from pathlib import Path

import duckdb


def derivative_fixture(tmp_path: Path) -> Path:
    """Create a clean-runner-safe analytical fixture."""
    path = tmp_path / "datasets.parquet"
    with duckdb.connect(":memory:") as connection:
        connection.execute(
            "COPY (SELECT * FROM VALUES ('a'), ('b') AS t(dataset_id)) "
            "TO ? (FORMAT PARQUET)",
            [str(path)],
        )
    return path


def test_query_command_reads_derivative(tmp_path: Path) -> None:
    """The command returns the expected row count from the canonical derivative."""
    root = Path(__file__).parents[2]
    result = subprocess.run(
        [  # noqa: S607
            "uv",
            "run",
            "--locked",
            "python",
            "tools/query_treasury_derivative.py",
            "--parquet",
            str(derivative_fixture(tmp_path)),
            "--sql",
            "SELECT count(*) AS n FROM treasury",
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"n": 2' in result.stdout


def test_query_command_rejects_non_select_and_external_reads(tmp_path: Path) -> None:
    """Only one SELECT over the preloaded Treasury table is accepted."""
    root = Path(__file__).parents[2]
    base = [
        "uv",
        "run",
        "--locked",
        "python",
        "tools/query_treasury_derivative.py",
        "--parquet",
        str(derivative_fixture(tmp_path)),
        "--sql",
    ]
    for query in ("PRAGMA version", "SELECT * FROM read_csv_auto('secret.csv')"):
        result = subprocess.run(
            [*base, query],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
