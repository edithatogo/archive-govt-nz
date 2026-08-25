"""Run isolated targeted mutants against Platinum layer implementation."""

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

MUTANTS: dict[str, tuple[str, str, str, str]] = {
    "croissant_context_check": (
        "src/archive_govt_nz/schemas/medallion.py",
        '"cr": "http://mlcommons.org/croissant/",',
        '"cr": "http://invalid.org/croissant/",',
        "tests/schemas/test_medallion_croissant.py",
    ),
    "hf_package_validation": (
        "src/archive_govt_nz/distribution/verifier.py",
        "required_files = [",
        "required_files = [] # [",
        "tests/distribution/test_verifier.py",
    ),
    "nlp_export_filter": (
        "src/archive_govt_nz/gold/nlp_export.py",
        "cols = [",
        "cols = [c for c in table.column_names] # [",
        "tests/gold/test_nlp_export.py",
    ),
}


def _run_single_mutant(
    name: str, target_file: str, needle: str, replacement: str, test_file: str
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="platinum-mutant-") as directory:
        root = Path(directory)
        package = root / "archive_govt_nz"
        shutil.copytree(ROOT / "src/archive_govt_nz", package)

        rel_path = Path(target_file).relative_to("src/archive_govt_nz")
        mutated = package / rel_path
        text = mutated.read_text(encoding="utf-8")
        if needle not in text:
            msg = f"mutant target missing in {target_file}: {name}"
            raise RuntimeError(msg)
        mutated.write_text(text.replace(needle, replacement, 1), encoding="utf-8")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_file,
            "-q",
        ]
        result = subprocess.run(  # noqa: S603
            cmd,
            cwd=ROOT,
            env={"PYTHONPATH": str(root), **os.environ},
            capture_output=True,
            text=True,
            check=False,
        )
        return {"name": name, "killed": result.returncode != 0}


def main() -> int:
    """Run all targeted mutants and emit a machine-readable receipt."""
    results: list[dict[str, Any]] = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(_run_single_mutant, name, target, needle, repl, test): name
            for name, (target, needle, repl, test) in MUTANTS.items()
        }
        results.extend(
            future.result() for future in concurrent.futures.as_completed(futures)
        )

    results.sort(key=lambda x: x["name"])

    payload = {
        "schema_version": "archive-govt-nz.mutation-platinum/v1",
        "mutants": results,
        "all_killed": all(r["killed"] for r in results),
    }
    out = Path("build/mutation-platinum.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + chr(10), encoding="utf-8"
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload["all_killed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
