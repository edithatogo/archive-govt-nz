"""Static mutations demonstrate replay, digest and scope assertions are live."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("before", "after", "selection"),
    [
        (
            "files = build_source_index(seeds, track)",
            (
                "files = {p.name: p.read_bytes() for p in __import__('pathlib').Path("
                "'conductor/tracks/global_foi_public_archive_20260830/"
                "canonical-index-20260907').iterdir()}"
            ),
            "recomputed_inputs_reject_faults",
        ),
        (
            "hashlib.sha256(data).hexdigest()",
            "'0' * 64",
            "actual_canonical_receipt",
        ),
        (
            '"programme_completion": "not_assessed"',
            '"programme_completion": "satisfied"',
            "actual_canonical_receipt",
        ),
    ],
)
def test_disposition_mutant_killed(before: str, after: str, selection: str) -> None:
    """Fail from semantic assertions, not imports, without editing source files."""
    code = (
        "import pathlib,pytest; "
        "import archive_govt_nz.foi_disposition_validation as module; "
        "source=pathlib.Path(module.__file__).read_text(); "
        f"assert source.count({before!r}) == 1; "
        f"exec(compile(source.replace({before!r}, {after!r}), "
        "module.__file__, 'exec'), module.__dict__); "
        "raise SystemExit(pytest.main(['tests/test_foi_disposition_validation.py',"
        f"'-q','-k',{selection!r}]))"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).parents[1],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 1, result.stdout + result.stderr
    assert "failed" in result.stdout
    assert "ERROR collecting" not in result.stdout
