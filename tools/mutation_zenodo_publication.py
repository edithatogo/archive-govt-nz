"""Run targeted mutants against irreversible Zenodo publication guards."""

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
SOURCE = ROOT / "src/archive_govt_nz/zenodo.py"
MUTANTS = {
    "release_approval": ("if not release_approved:", "if release_approved:"),
    "draft_preflight": ('if before.state != "draft":', 'if before.state == "draft":'),
    "preflight_identity": (
        "if before.deposition_id != deposition_id:",
        "if before.deposition_id == deposition_id:",
    ),
    "published_readback": (
        'if deposition.state != "published":',
        'if deposition.state == "published":',
    ),
    "doi_readback": (
        "if deposition.doi != confirm_doi:",
        "if deposition.doi == confirm_doi:",
    ),
}


def _run_mutant(name: str, needle: str, replacement: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="zenodo-publication-mutant-") as directory:
        root = Path(directory)
        package = root / "archive_govt_nz"
        shutil.copytree(ROOT / "src/archive_govt_nz", package)
        mutated = package / "zenodo.py"
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
                "tests/publication/test_zenodo_client.py",
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
    """Execute publication mutants and emit a deterministic result."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(MUTANTS)) as executor:
        futures = [
            executor.submit(_run_mutant, name, needle, replacement)
            for name, (needle, replacement) in MUTANTS.items()
        ]
        results = [future.result() for future in futures]
    payload = {
        "schema_version": "archive-govt-nz.zenodo-publication-mutation/v1",
        "source": str(SOURCE.relative_to(ROOT)),
        "mutants": results,
        "killed": sum(result["killed"] for result in results),
        "total": len(results),
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if payload["killed"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
