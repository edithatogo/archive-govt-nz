"""Mutation controls for persisted legislation checkpoint-root accounting."""

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
SOURCE = ROOT / "src/archive_govt_nz/domains/legislation/corpus.py"
TEST = "tests/domains/test_legislation_archive_service.py"
SELECTION = "checkpoint_roots_hash_exact_persisted_bytes"
MUTANTS = (
    (
        "compact_reencoding",
        "manager.checkpoint_path.read_bytes()",
        (
            "json.dumps(json.loads(manager.checkpoint_path.read_text()), "
            'sort_keys=True, separators=(",", ":")).encode()'
        ),
    ),
)


def run(source: str) -> int:
    """Run one checkpoint mutant in an isolated source tree."""
    with tempfile.TemporaryDirectory(prefix="legislation-checkpoint-mutant-") as raw:
        base = Path(raw)
        shutil.copytree(ROOT / "src/archive_govt_nz", base / "src/archive_govt_nz")
        target = base / "src/archive_govt_nz/domains/legislation/corpus.py"
        target.write_text(source, encoding="utf-8")
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(base / "src")
        result = subprocess.run(  # noqa: S603 - isolated fixed test command
            [sys.executable, "-m", "pytest", "-q", TEST, "-k", SELECTION],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
            check=False,
        )
        return result.returncode


def main() -> None:
    """Kill both compact-reencoding substitutions."""
    source = SOURCE.read_text(encoding="utf-8")
    outcomes = []
    for name, old, new in MUTANTS:
        if source.count(old) != 1:
            message = "mutation anchor mismatch"
            raise SystemExit(message)
        code = run(source.replace(old, new))
        outcomes.append({"name": name, "exit_code": code, "killed": code == 1})
    receipt = {
        "schema_version": "archive-govt-nz.legislation-checkpoint-root-mutation/v1",
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
