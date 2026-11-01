"""Bounded in-memory mutations of canonical join integrity and policy guards."""

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]


@pytest.mark.parametrize(
    ("before", "after", "selection"),
    [
        ("len(result) == len(rows)", "True", "negative_joins"),
        (
            "set(assessed) == set(materialized) - set(seeds)",
            "True",
            "negative_joins",
        ),
        (
            'receipts[source_id]["entity_id"] == entity',
            "True",
            "negative_joins",
        ),
        (
            'row["retained_receipt_sha256"] == receipt["receipt_sha256"]',
            "True",
            "negative_joins",
        ),
        (
            'hashlib.sha256(payload).hexdigest() == pins["files"][name]',
            "True",
            "input_drift_and_missing_receipts",
        ),
        (
            "row[key] is False",
            "row[key] is not None",
            "candidate_cannot_grant_execution",
        ),
        (
            'candidates == docs["candidate-assessment-complete.json"]',
            "True",
            "recomputed_report_drift",
        ),
    ],
)
def test_canonical_guard_mutant_killed(before: str, after: str, selection: str) -> None:
    """Each disabled guard causes assertion failures, not an import/setup error."""
    code = (
        "import pathlib,pytest; "
        "import archive_govt_nz.foi_canonical as module; "
        "source=pathlib.Path(module.__file__).read_text(); "
        f"assert source.count({before!r}) == 1; "
        f"exec(compile(source.replace({before!r}, {after!r}), "
        "module.__file__, 'exec'), module.__dict__); "
        "raise SystemExit(pytest.main(['tests/test_foi_canonical.py',"
        f"'-q','-k',{selection!r}]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "failed" in result.stdout
    assert "ERROR collecting" not in result.stdout
