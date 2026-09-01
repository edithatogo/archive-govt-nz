"""Run targeted mutants against Zenodo identity and publication-state guards."""

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
SOURCE = ROOT / "src/archive_govt_nz/zenodo_identity.py"
MUTANTS = {
    "distinct_identity": (
        "if concept_id == version_id:",
        "if concept_id != version_id:",
    ),
    "version_record_binding": (
        'if version_id != identity["version_record_id"]:',
        'if version_id == identity["version_record_id"]:',
    ),
    "observation_authority": (
        'if operation["external_action_authorized"] or '
        'operation["approval_reference"]:',
        'if operation["external_action_authorized"] and '
        'operation["approval_reference"]:',
    ),
    "publication_approval": (
        'elif (\n        not operation["external_action_authorized"]\n'
        '        or not operation["approval_reference"]\n    ):',
        'elif (\n        not operation["external_action_authorized"]\n'
        '        and not operation["approval_reference"]\n    ):',
    ),
    "published_receipt": (
        'if operation["status"] == "published" and not '
        'operation["remote_receipt_path"]:',
        'if operation["status"] == "published" and operation["remote_receipt_path"]:',
    ),
}


def _run_mutant(name: str, needle: str, replacement: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="zenodo-identity-mutant-") as directory:
        root = Path(directory)
        package = root / "archive_govt_nz"
        shutil.copytree(ROOT / "src/archive_govt_nz", package)
        mutated = package / "zenodo_identity.py"
        source = mutated.read_text(encoding="utf-8")
        if needle not in source:
            msg = f"mutant target missing: {name}"
            raise RuntimeError(msg)
        mutated.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/publication/test_zenodo_identity.py",
                "-q",
            ],
            cwd=ROOT,
            env={"PYTHONPATH": str(root), **os.environ},
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
        "schema_version": "archive-govt-nz.zenodo-identity-mutation/v1",
        "source": str(SOURCE.relative_to(ROOT)),
        "mutants": results,
        "killed": sum(result["killed"] for result in results),
        "total": len(results),
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if payload["killed"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
