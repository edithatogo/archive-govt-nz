"""Exact receipt status exclusions must not hide credential candidates."""

from __future__ import annotations

import json
import re
import runpy
import shutil
import subprocess
from pathlib import Path
from typing import cast

import pytest

PATTERN = cast(
    "str",
    runpy.run_path(str(Path(__file__).parents[2] / "tools/supply_chain.py"))[
        "RECEIPT_EXCLUSION_PATTERN"
    ],
)


@pytest.mark.parametrize("field", ["secrets", "audit_licenses_secrets_sbom"])
def test_only_complete_passed_status_is_excluded(field: str) -> None:
    """Match one whole status line, including ordinary JSON indentation."""
    line = f'"{field}": "passed",'
    assert re.search(PATTERN, line)
    assert re.search(PATTERN, "  " + line + "\t\n")
    for invalid in (
        line.replace("passed", "failed"),
        line.replace("passed", "synthetic-credential-value"),
        line.replace("passed", "passed-extra"),
        line.replace(field, "other_" + field),
        line.removesuffix(","),
        "prefix " + line,
        line + ' "password": "synthetic-credential-value"',
        line + ' // password="synthetic-credential-value"',
        line + '\npassword="synthetic-credential-value"',
    ):
        assert re.search(PATTERN, invalid) is None


@pytest.mark.parametrize(
    ("line", "excluded"),
    [
        ('  "secrets": "passed",', True),
        ('  "audit_licenses_secrets_sbom": "passed",', True),
        ('  "secrets": "synthetic-credential-value",', False),
        (
            '  "secrets": "passed", "password": "different-synthetic-credential"',
            False,
        ),
    ],
)
def test_scanner_retains_nonpassed_and_trailing_credentials(
    tmp_path: Path, line: str, *, excluded: bool
) -> None:
    """Exercise the production scanner, retaining findings on unsafe lines."""
    receipt = tmp_path / "receipt.json"
    receipt.write_text(line + "\n", encoding="utf-8")
    executable = shutil.which("detect-secrets")
    assert executable is not None
    command = [executable, "scan", "--all-files", "--force-use-all-plugins"]
    baseline = subprocess.run(
        [*command, receipt.name],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    filtered = subprocess.run(
        [*command, "--exclude-lines", PATTERN, receipt.name],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    )
    before = json.loads(baseline.stdout)["results"][receipt.name]
    after = json.loads(filtered.stdout)["results"]
    assert before
    assert after == ({} if excluded else {receipt.name: before})
