"""Run isolated targeted mutants against adapter base implementation."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/archive_govt_nz/adapters/base.py"
MUTANTS = {
    "store_payload_digest": (
        'record_id = f"rec:{receipt.sha256[:16]}"',
        "record_id = f\"rec:{'0'*16}\"",
    ),
    "capture_event_status": (
        "return CaptureEvent(",
        "raise RuntimeError('mutant')",
    ),
}


def main() -> int:
    """Run all targeted mutants and emit a machine-readable receipt."""
    results: list[dict[str, Any]] = []
    for name, (needle, replacement) in MUTANTS.items():
        with tempfile.TemporaryDirectory(prefix="archive-adapter-mutant-") as directory:
            root = Path(directory)
            package = root / "archive_govt_nz"
            shutil.copytree(ROOT / "src/archive_govt_nz", package)
            mutated = package / "adapters" / "base.py"
            text = mutated.read_text(encoding="utf-8")
            if needle not in text:
                msg = f"mutant target missing: {name}"
                raise RuntimeError(msg)
            mutated.write_text(text.replace(needle, replacement, 1), encoding="utf-8")
            cmd = [
                "uv",
                "run",
                "--locked",
                "pytest",
                "tests/capture/test_base_adapter.py",
                "-q",
            ]
            result = subprocess.run(
                cmd,
                cwd=ROOT,
                env={"PYTHONPATH": str(root), **os.environ},
                capture_output=True,
                text=True,
                check=False,
            )
            results.append({"name": name, "killed": result.returncode != 0})
    payload = {
        "schema_version": "archive-govt-nz.mutation-adapters/v1",
        "source": str(SOURCE.relative_to(ROOT)),
        "mutants": results,
        "killed": sum(item["killed"] for item in results),
        "total": len(results),
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if payload["killed"] == payload["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
