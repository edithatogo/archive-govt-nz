"""Require bounded integrity mutations to fail real FOI package tests."""

from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path("src/archive_govt_nz/foi_package.py")
MUTATIONS = {
    "attachment_integrity": (
        '_fail("invalid_attachment_index")',
        "pass",
    ),
    "attachment_census": (
        '_fail("incomplete_attachment_index")',
        "pass",
    ),
    "object_identity": (
        'row["object_id"] != "sha256:" + digest',
        'row["object_id"] == "sha256:" + digest',
    ),
    "index_parity": ('_fail("parquet_jsonl_mismatch")', "pass"),
    "response_population": ("claimed != set(responses)", "claimed == set(responses)"),
    "raw_inventory_bytes": (
        (
            'sha256(path) != row["sha256"]\n        ):\n'
            '            _fail("raw_object_integrity_failure")'
        ),
        (
            'sha256(path) == row["sha256"]\n        ):\n'
            '            _fail("raw_object_integrity_failure")'
        ),
    ),
}


def check_mutant(name: str, replacement: tuple[str, str]) -> dict[str, object]:
    """Run each mutant against an isolated copy, rejecting infrastructure failures."""
    original = (ROOT / SOURCE).read_text()
    before, after = replacement
    if original.count(before) != 1:
        message = f"nonunique mutation target: {name}"
        raise ValueError(message)
    with tempfile.TemporaryDirectory(prefix="foi-integrity-mutant-") as temporary:
        stage = Path(temporary)
        shutil.copytree(ROOT / "src/archive_govt_nz", stage / "src/archive_govt_nz")
        (stage / SOURCE).write_text(original.replace(before, after))
        environment = {**os.environ, "PYTHONPATH": str(stage / "src")}
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_foi_package.py",
                "-q",
                "--no-cov",
                "--maxfail=1",
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        return {
            "name": name,
            "exit_code": result.returncode,
            "killed": result.returncode == 1
            and "FAILED tests/test_foi_package.py" in result.stdout,
        }


def main() -> int:
    """Write a bounded mutation receipt and fail if any guard mutation survives."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(check_mutant, MUTATIONS, MUTATIONS.values()))
    receipt = {
        "source": SOURCE.as_posix(),
        "mutations": results,
        "passed": all(r["killed"] for r in results),
    }
    path = ROOT / "build/foi-package-mutations.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
