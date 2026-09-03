"""Mutation controls for cumulative legislation document identity semantics."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "src/archive_govt_nz/domains/legislation/one_batch_reconciliation.py"
TEST = "tests/tools/test_reconcile_one_legislation_batch.py"
MUTANTS = (
    (
        "reject_valid_work_versions",
        (
            "prior_work = document_work_ids.setdefault(document_id, work_id)\n"
            "    if prior_work != work_id:\n"
            '        _fail("document_identity_duplicate")'
        ),
        (
            "if document_id in document_work_ids:\n"
            '        _fail("document_identity_duplicate")\n'
            "    document_work_ids[document_id] = work_id"
        ),
        "test_one_work_accepts_multiple_version_records",
    ),
    (
        "allow_cross_work_collision",
        'if prior_work != work_id:\n        _fail("document_identity_duplicate")',
        'if False:\n        _fail("document_identity_duplicate")',
        "document_duplicate",
    ),
)


def run(source: str, selection: str) -> int:
    """Run one identity mutant in an isolated source tree."""
    with tempfile.TemporaryDirectory(
        prefix="legislation-reconciliation-mutant-"
    ) as raw:
        base = Path(raw)
        shutil.copytree(ROOT / "src/archive_govt_nz", base / "src/archive_govt_nz")
        target = (
            base / "src/archive_govt_nz/domains/legislation/one_batch_reconciliation.py"
        )
        target.write_text(source, encoding="utf-8")
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(base / "src")
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        result = subprocess.run(  # noqa: S603 - isolated fixed test command
            [sys.executable, "-m", "pytest", "-q", TEST, "-k", selection],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
            check=False,
        )
        return result.returncode


def main() -> None:
    """Kill both permissive and over-restrictive identity mutants."""
    source = SOURCE.read_text(encoding="utf-8")
    outcomes = []
    for name, old, new, selection in MUTANTS:
        if source.count(old) != 1:
            message = f"mutation anchor mismatch: {name}"
            raise SystemExit(message)
        code = run(source.replace(old, new), selection)
        outcomes.append({"name": name, "exit_code": code, "killed": code == 1})
    receipt = {
        "schema_version": "archive-govt-nz.legislation-reconciliation-mutation/v1",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "mutants": outcomes,
        "killed": sum(item["killed"] for item in outcomes),
        "total": len(outcomes),
    }
    print(json.dumps(receipt, sort_keys=True))
    if receipt["killed"] != receipt["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
