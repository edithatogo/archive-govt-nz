"""Run targeted mutants against GitHub release correction guards."""

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
TOOL = Path("tools/legislation_release_correction.py")
MUTANTS = {
    "ambiguous_backslash_path": (
        'or any("\\\\" in part for part in relative.parts)',
        'or any("\\\\" not in part for part in relative.parts)',
    ),
    "release_identity": (
        "if any(snapshot.get(key) != value for key, value in expected.items()):",
        "if any(snapshot.get(key) == value for key, value in expected.items()):",
    ),
    "bad_cycle_count": (
        "if body.count(BAD_CYCLE_1) != 1:",
        "if body.count(BAD_CYCLE_1) == 1:",
    ),
    "cycle_semantics": (
        "if body.count(GOOD_CYCLE_2) != 1 or GOOD_CYCLE_1 in body:",
        "if body.count(GOOD_CYCLE_2) == 1 or GOOD_CYCLE_1 in body:",
    ),
    "source_body_fixity": (
        'snapshot.get("body_sha256") != PRE_BODY_SHA256',
        'snapshot.get("body_sha256") == PRE_BODY_SHA256',
    ),
    "attestation_cycles": ("if observed != expected:", "if observed == expected:"),
    "hosted_run_identity": (
        'hosted["runs"] != HOSTED_EVIDENCE',
        'hosted["runs"] == HOSTED_EVIDENCE',
    ),
    "applied_exact_body": ("if body != expected_body:", "if body == expected_body:"),
    "applied_identity": (
        'if readback["release_identity"] != expected_identity:',
        'if readback["release_identity"] == expected_identity:',
    ),
    "applied_body_fixity": (
        'if _sha(body.encode()) != readback["body_sha256"]:',
        'if _sha(body.encode()) == readback["body_sha256"]:',
    ),
    "applied_response_fixity": (
        'if _sha(canonical_response) != readback["normalized_response_sha256"]:',
        'if _sha(canonical_response) == readback["normalized_response_sha256"]:',
    ),
    "local_evidence_fixity": (
        "if observed_sha != expected_sha:",
        "if observed_sha == expected_sha:",
    ),
    "rendered_addendum_fixity": (
        'if addendum["rendered_remote_addendum_sha256"] != rendered_sha:',
        'if addendum["rendered_remote_addendum_sha256"] == rendered_sha:',
    ),
    "post_response_fixity": (
        'if _sha(post_bytes) != readback["raw_response_sha256"]:',
        'if _sha(post_bytes) == readback["raw_response_sha256"]:',
    ),
    "post_raw_identity": (
        "if raw_identity != comparable_identity:",
        "if raw_identity == comparable_identity:",
    ),
}


def _prepare(root: Path) -> None:
    for relative in (
        TOOL,
        Path("tests/tools/test_legislation_release_correction.py"),
        Path("tests/fixtures/legislation-github-release-correction-v1.json"),
        Path("schemas/legislation-github-release-correction-v1.schema.json"),
        Path(
            "evidence/migrations/corpus-legislation-nz/cutover-release-provenance/release-post-readback.json"
        ),
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)


def _run_mutant(name: str, needle: str, replacement: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="release-correction-mutant-") as directory:
        root = Path(directory)
        _prepare(root)
        source_path = root / TOOL
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
                "tests/tools/test_legislation_release_correction.py",
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
            executor.submit(_run_mutant, name, needle, replacement)
            for name, (needle, replacement) in MUTANTS.items()
        ]
        results = [future.result() for future in futures]
    payload = {
        "schema_version": "archive-govt-nz.legislation-release-correction-mutation/v1",
        "mutants": results,
        "killed": sum(result["killed"] for result in results),
        "total": len(results),
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if payload["killed"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
