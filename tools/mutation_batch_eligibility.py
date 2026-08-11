"""Run isolated mutants against resource-level batch eligibility gates."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/archive_govt_nz/batch_capture.py"
MUTANTS = {
    "rights_disposition": ('== "eligible"', '!= "eligible"'),
    "preflight_confirmation": (
        'item.get("resource_id") in securely_observed_ids',
        'item.get("resource_id") not in securely_observed_ids',
    ),
}


def main() -> int:
    """Run every eligibility mutant and emit a deterministic receipt."""
    uv = shutil.which("uv")
    if uv is None:
        message = "uv_not_found"
        raise RuntimeError(message)
    results: list[dict[str, Any]] = []
    for name, (needle, replacement) in MUTANTS.items():
        with tempfile.TemporaryDirectory(
            prefix="archive-eligibility-mutant-"
        ) as directory:
            root = Path(directory)
            package = root / "archive_govt_nz"
            shutil.copytree(ROOT / "src/archive_govt_nz", package)
            mutated = package / "batch_capture.py"
            text = mutated.read_text(encoding="utf-8")
            if needle not in text:
                message = f"mutant target missing: {name}"
                raise RuntimeError(message)
            mutated.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
            result = subprocess.run(  # noqa: S603
                [
                    uv,
                    "run",
                    "--locked",
                    "pytest",
                    "tests/capture/test_batch_eligibility.py",
                    "-q",
                ],
                cwd=ROOT,
                env={"PYTHONPATH": str(root), **os.environ},
                capture_output=True,
                text=True,
                check=False,
            )
            results.append({"name": name, "killed": result.returncode != 0})
    payload = {
        "schema_version": "archive-govt-nz.mutation-batch-eligibility/v1",
        "source": str(SOURCE.relative_to(ROOT)),
        "mutants": results,
        "killed": sum(item["killed"] for item in results),
        "total": len(results),
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if payload["killed"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
