"""Static fault injection into critical child identity and hash checks."""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ("before", "after"),
    [
        ("hashlib.sha256(payload).hexdigest() != digest", "False"),
        ('manifest["source_id"] != source["id"]', "False"),
        ('pointer["repo_id"] != repo', "False"),
        ('not REVISION.fullmatch(pointer["snapshot_revision"])', "False"),
        ('not HASH.fullmatch(pointer["manifest_sha256"])', "False"),
        ('not REVISION.fullmatch(manifest["source_revision"])', "False"),
        ('not HASH.fullmatch(manifest["capture_inventory_sha256"])', "False"),
        ('not HASH.fullmatch(row["sha256"])', "False"),
    ],
)
def test_child_guard_mutant_killed(before: str, after: str) -> None:
    """Disabled guards fail executable negatives without modifying installed files."""
    code = (
        "import pathlib,pytest; import archive_govt_nz.foi_child_manifests as m; "
        "source=pathlib.Path(m.__file__).read_text(); "
        f"assert source.count({before!r}) == 1; "
        f"exec(compile(source.replace({before!r},{after!r}),"
        "m.__file__,'exec'),m.__dict__); "
        "raise SystemExit(pytest.main(['tests/test_foi_child_manifests.py','-q',"
        "'-k','invalid_child_fails_closed or newline']))"
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
