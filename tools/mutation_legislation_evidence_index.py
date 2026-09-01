"""Run targeted mutants against evidence-index completion guards."""

from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = Path("tools/legislation_evidence_index.py")
EVALUATOR = Path("tools/evaluate_legislation_completion.py")
MUTANTS = {
    "fixity_comparison": (
        VALIDATOR,
        'if observed != row["sha256"]:',
        'if observed == row["sha256"]:',
    ),
    "active_input_guard": (
        VALIDATOR,
        'if entries[evidence_id]["classification"] != "active":',
        'if entries[evidence_id]["classification"] == "active":',
    ),
    "input_dimension_guard": (
        VALIDATOR,
        'if dimension not in entries[evidence_id]["claim_dimensions"]:',
        'if dimension in entries[evidence_id]["claim_dimensions"]:',
    ),
    "negative_status_binding": (
        VALIDATOR,
        'if status not in {"complete", classification}:',
        'if status in {"complete", classification}:',
    ),
    "public_claim_guard": (
        VALIDATOR,
        'if (\n                status == "complete"\n'
        '                and entries[evidence_id]["artefact_type"] == "public_claim"\n'
        "            ):",
        'if (\n                status == "complete"\n'
        '                and entries[evidence_id]["artefact_type"] != "public_claim"\n'
        "            ):",
    ),
    "complete_classification": (
        EVALUATOR,
        'and entries[proof_id].get("classification") == "active"',
        'and entries[proof_id].get("classification") != "active"',
    ),
    "proof_kind_allowlist": (
        EVALUATOR,
        "in COMPLETE_PROOF_KINDS[dimension]",
        "not in COMPLETE_PROOF_KINDS[dimension]",
    ),
    "all_dimensions_required": (
        EVALUATOR,
        'and not result["blockers"]',
        'and result["blockers"]',
    ),
}


def _prepare(root: Path) -> None:
    for relative in (
        VALIDATOR,
        EVALUATOR,
        Path("tests/tools/test_legislation_evidence_index.py"),
        Path("tests/tools/test_evaluate_legislation_completion.py"),
        Path("tests/fixtures/legislation-evidence-index-v1.json"),
        Path("schemas/legislation-evidence-index-v1.schema.json"),
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)


def _run_mutant(
    name: str, relative: Path, needle: str, replacement: str
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="evidence-index-mutant-") as directory:
        root = Path(directory)
        _prepare(root)
        source_path = root / relative
        source = source_path.read_text(encoding="utf-8")
        if needle not in source:
            message = f"mutant target missing: {name}"
            raise RuntimeError(message)
        source_path.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/tools/test_legislation_evidence_index.py",
                "tests/tools/test_evaluate_legislation_completion.py",
                "-q",
            ],
            cwd=root,
            env={**os.environ, "PYTHONPATH": str(root)},
            capture_output=True,
            text=True,
            check=False,
        )
        return {"name": name, "killed": result.returncode != 0}


def main() -> int:
    """Execute mutants concurrently and emit a deterministic result."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(MUTANTS)) as executor:
        futures = [
            executor.submit(_run_mutant, name, relative, needle, replacement)
            for name, (relative, needle, replacement) in MUTANTS.items()
        ]
        results = [future.result() for future in futures]
    payload = {
        "schema_version": "archive-govt-nz.legislation-evidence-index-mutation/v1",
        "mutants": results,
        "killed": sum(result["killed"] for result in results),
        "total": len(results),
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if payload["killed"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
