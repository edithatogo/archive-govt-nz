"""Targeted mutation controls for bounded legislation discovery integrity."""

# ruff: noqa: EM101, EM102, S603, TRY003

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "src/archive_govt_nz/domains/legislation/discovery_lane.py"
TEST = ROOT / "tests/domains/test_legislation_discovery_lane.py"
MUTANTS = (
    (
        "generic_terms",
        "if all(term.casefold() in GENERIC_TERMS for term in normalized):",
        "if False:",
    ),
    ("official_endpoint", "if self.endpoint != OFFICIAL_ENDPOINT:", "if False:"),
    (
        "stable_sort",
        'if self.start_page < 1 or self.sort != "work_id":',
        "if self.start_page < 1:",
    ),
    (
        "canonical_state_boundary",
        '"canonical_state_changed": False,',
        '"canonical_state_changed": True,',
    ),
)


def run(source: str) -> int:
    """Run discovery tests against an isolated mutant module."""
    with tempfile.TemporaryDirectory(prefix="legislation-discovery-mutant-") as raw:
        base = Path(raw)
        package = base / "archive_govt_nz/domains/legislation"
        package.mkdir(parents=True)
        for parent in (
            base / "archive_govt_nz",
            base / "archive_govt_nz/domains",
            package,
        ):
            (parent / "__init__.py").write_text("", encoding="utf-8")
        (package / "discovery_lane.py").write_text(source, encoding="utf-8")
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(base)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "--confcutdir",
                str(TEST.parent),
                str(TEST),
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            timeout=60,
            check=False,
        )
        if result.returncode not in {0, 1}:
            sys.stderr.write(result.stdout.decode() + result.stderr.decode())
        return result.returncode


def main() -> None:
    """Kill all bounded-discovery integrity mutants."""
    source = SOURCE.read_text(encoding="utf-8")
    if run(source) != 0:
        raise SystemExit("discovery mutation baseline failed")
    outcomes = []
    for name, old, new in MUTANTS:
        if source.count(old) != 1:
            raise SystemExit(f"mutation anchor mismatch: {name}")
        code = run(source.replace(old, new))
        outcomes.append({"name": name, "exit_code": code, "killed": code == 1})
    receipt = {
        "schema_version": "archive-govt-nz.legislation-discovery-mutation/v1",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "mutants": outcomes,
        "killed": sum(bool(item["killed"]) for item in outcomes),
        "total": len(outcomes),
    }
    print(json.dumps(receipt, sort_keys=True))
    if receipt["killed"] != receipt["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
