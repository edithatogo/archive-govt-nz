"""Run cold isolated dimension-contract mutants; no repository source edits."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RELATIVE = Path(
    "src/archive_govt_nz/domains/health_appropriations/dimension_mapping.py"
)
TEST = "tests/domains/health_appropriations/test_dimension_mapping.py"
MUTATIONS = {
    "kind": ("_require(value.kind in KINDS)", "_require(True)"),
    "text_bound": ("len(value) <= MAX_TEXT", "len(value) <= MAX_TEXT + 1"),
    "date_order": ("value.start <= value.end", "True"),
    "literal_label": ("            value.label,", "            value.label.lower(),"),
    "period_key": ("            value.period_token,", "            None,"),
    "vintage": ("_text(value.vintage)", "pass"),
    "version": ("_text(value.version)", "pass"),
    "evidence_bound": ("len(value.evidence) <= MAX_EVIDENCE", "True"),
    "evidence_digest": ('re.fullmatch(r"[0-9a-f]{64}", digest)', "True"),
    "evidence_order": (
        "_require(tuple(sorted(set(value.evidence))) == value.evidence)",
        "pass",
    ),
    "unresolved": ("_require(value.method is None and not value.evidence)", "pass"),
    "evidence_required": ("_require(bool(value.evidence))", "pass"),
    "inclusive_end": (
        "right.start or date.min) <= min(",
        "right.start or date.min) < min(",
    ),
    "row_bound": ("len(rows) <= MAX_ROWS", "len(rows) < MAX_ROWS"),
    "duplicate": ("_require(key not in indexed)", "pass"),
    "conflict": (
        "== (right.target, right.vintage, right.version)",
        "== (left.target, left.vintage, left.version)",
    ),
    "drift": (
        '("vintage", "version", "target", "method", "evidence")',
        '("vintage", "version", "target", "method")',
    ),
    "added": ('changes = ("added",)', 'changes = ("removed",)'),
    "bridge_state": ('_require(row["mapping_state"] == "unmapped")', "pass"),
    "bridge_target": ('_require(row["normalized_identifier"] is None)', "pass"),
    "bridge_version": ('_require(row["scheme_version"] is None)', "pass"),
}


def run(needle: str, replacement: str) -> int:
    """Run only the focused suite against one temporary source tree."""
    original = (ROOT / RELATIVE).read_text(encoding="utf-8")
    if needle and original.count(needle) != 1:
        message = "mutation target must occur exactly once"
        raise ValueError(message)
    with tempfile.TemporaryDirectory(prefix="health-dimension-mutant-") as directory:
        root = Path(directory)
        shutil.copytree(
            ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__")
        )
        changed = original.replace(needle, replacement, 1) if needle else original
        (root / RELATIVE).write_text(changed, encoding="utf-8")
        environment = {
            **os.environ,
            "PYTHONPATH": str(root / "src"),
            "PYTHONDONTWRITEBYTECODE": "1",
            "HYPOTHESIS_STORAGE_DIRECTORY": str(root / "hypothesis"),
        }
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                TEST,
                "-q",
                "--no-cov",
                "-p",
                "no:cacheprovider",
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        return completed.returncode


def main() -> int:
    """Require a green baseline and assertion failures, not collection errors."""
    baseline = run("", "")
    if baseline != 0:
        return baseline
    results = {name: run(*mutation) for name, mutation in MUTATIONS.items()}
    print(json.dumps({"baseline": baseline, "mutants": results}, sort_keys=True))  # noqa: T201
    return 0 if all(code == 1 for code in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
