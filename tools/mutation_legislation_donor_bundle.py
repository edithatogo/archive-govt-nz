"""Run targeted mutants against donor Git bundle integrity guards."""

# ruff: noqa: EM102, S603, TRY003

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
TOOL = Path("tools/verify_legislation_donor_bundle.py")
TEST = Path("tests/tools/test_verify_legislation_donor_bundle.py")
SCHEMA = Path("schemas/legislation-donor-bundle-verification-v1.schema.json")
MUTANTS = {
    "release_identity": (
        'release.get("id") != RELEASE_ID or release.get("draft") is not True',
        'release.get("id") == RELEASE_ID or release.get("draft") is not True',
    ),
    "asset_identity": (
        "if any(asset.get(key) != value for key, value in required_asset.items()):",
        "if any(asset.get(key) == value for key, value in required_asset.items()):",
    ),
    "asset_fixity": (
        "if len(raw) != ASSET_SIZE or _sha(raw) != ASSET_SHA256:",
        "if len(raw) == ASSET_SIZE or _sha(raw) != ASSET_SHA256:",
    ),
    "missing_refs": ("if missing:\n        _fail", "if not missing:\n        _fail"),
    "mismatched_refs": (
        "if mismatched:\n        _fail",
        "if not mismatched:\n        _fail",
    ),
    "final_head": (
        "if FINAL_HEAD not in {",
        "if FINAL_HEAD in {",
    ),
    "required_governance": (
        '    "LICENSE",',
        '    "MISSING",',
    ),
    "workflow_history": (
        "if not workflows:\n        _fail",
        "if workflows:\n        _fail",
    ),
    "conductor_history": (
        "if not conductor:\n        _fail",
        "if conductor:\n        _fail",
    ),
}


def _run(name: str, needle: str, replacement: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="donor-bundle-mutant-") as directory:
        root = Path(directory)
        for relative in (TOOL, TEST, SCHEMA):
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
        source = (root / TOOL).read_text(encoding="utf-8")
        if needle not in source:
            raise RuntimeError(f"mutant target missing:{name}")
        (root / TOOL).write_text(
            source.replace(needle, replacement, 1), encoding="utf-8"
        )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(TEST), "-q"],
            cwd=root,
            env={**os.environ, "PYTHONPATH": str(root)},
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        return {"name": name, "killed": result.returncode != 0}


def main() -> int:
    """Execute integrity mutants and report every result deterministically."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [
            executor.submit(_run, name, *mutation) for name, mutation in MUTANTS.items()
        ]
        results = sorted(
            (future.result() for future in futures), key=lambda item: item["name"]
        )
    payload = {
        "schema_version": "archive-govt-nz.legislation-donor-bundle-mutation/v1",
        "mutants": results,
        "killed": sum(result["killed"] for result in results),
        "total": len(results),
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if payload["killed"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
