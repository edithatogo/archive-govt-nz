"""Targeted mutation controls for historical legislation coverage integrity."""

# ruff: noqa: E501, EM101, EM102, TRY003

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
SOURCE = ROOT / "tools/legislation_historical_coverage.py"
TEST = "tests/tools/test_legislation_historical_coverage.py"

MUTANTS: tuple[tuple[str, tuple[tuple[str, str], ...], str], ...] = (
    (
        "candidate_hash",
        (("if _sha256(concatenated) != EXPECTED_CANDIDATE_SHA256:", "if False:"),),
        "test_batch_audit_fails_closed[hash]",
    ),
    (
        "expected_batch_count",
        (("EXPECTED_BATCHES = 68", "EXPECTED_BATCHES = 67"),),
        "test_build_report_preserves_distinct_counts_and_unknowns",
    ),
    (
        "candidate_uniqueness",
        (
            ("if ids != sorted(set(ids)):", "if ids != sorted(ids):"),
            (
                "if len(all_ids) != EXPECTED_CANDIDATES or len(set(all_ids)) != len(all_ids):",
                "if len(all_ids) != EXPECTED_CANDIDATES:",
            ),
            ("if candidate_lines != all_ids:", "if False:"),
            (
                "if _sha256(concatenated) != EXPECTED_CANDIDATE_SHA256:",
                "if False:",
            ),
        ),
        "test_batch_audit_fails_closed[duplicate]",
    ),
    (
        "unknown_to_zero",
        (
            (
                "'unknown' if item['value'] is None else format(item['value'], ',')",
                "'0' if item['value'] is None else format(item['value'], ',')",
            ),
        ),
        "test_build_report_preserves_distinct_counts_and_unknowns",
    ),
    (
        "reviewed_seed_subset",
        (
            (
                'and set(seed_ids).issubset(candidates["ids"])',
                "and True",
            ),
        ),
        "test_reviewed_seed_must_be_a_candidate_subset",
    ),
    (
        "receipt_readback_match",
        (
            (
                'if not isinstance(output, dict) or output != readback.get("output"):',
                "if not isinstance(output, dict):",
            ),
        ),
        "test_target_receipt_mismatch_is_rejected",
    ),
)


def _mutate(source: str, replacements: tuple[tuple[str, str], ...], name: str) -> str:
    """Apply exact single-occurrence replacements or fail on source drift."""
    mutated = source
    for old, new in replacements:
        if mutated.count(old) != 1:
            raise SystemExit(f"mutation anchor mismatch: {name}")
        mutated = mutated.replace(old, new)
    return mutated


def run(source: str, test_name: str) -> int:
    """Run one focused test against an isolated analyzer source tree."""
    with tempfile.TemporaryDirectory(prefix="legislation-coverage-mutant-") as raw:
        base = Path(raw)
        (base / "tools").mkdir()
        (base / "tests/tools").mkdir(parents=True)
        (base / "tools/legislation_historical_coverage.py").write_text(
            source, encoding="utf-8"
        )
        shutil.copy2(ROOT / TEST, base / TEST)
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(base)
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", f"{TEST}::{test_name}"],
            cwd=base,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
            check=False,
        )
        return result.returncode


def main() -> None:
    """Kill every declared historical coverage integrity mutant."""
    source = SOURCE.read_text(encoding="utf-8")
    baseline = "test_build_report_preserves_distinct_counts_and_unknowns"
    if run(source, baseline) != 0:
        raise SystemExit("historical coverage mutation baseline failed")
    outcomes: list[dict[str, object]] = []
    for name, replacements, test_name in MUTANTS:
        code = run(_mutate(source, replacements, name), test_name)
        outcomes.append({"name": name, "exit_code": code, "killed": code == 1})
    receipt = {
        "schema_version": "archive-govt-nz.legislation-historical-coverage-mutation/v1",
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
