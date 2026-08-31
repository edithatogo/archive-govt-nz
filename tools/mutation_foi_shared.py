"""Require bounded integrity mutations to fail real FOI control tests."""

from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MUTATIONS = {
    "force_ref": ("foi_github_state", '"force": False', '"force": True'),
    "stale_head": ("foi_github_state", "head != self.expected[key]", "False"),
    "global_snapshot_pin": (
        "foi_github_state",
        "if self.batch_head is not None and self.batch_head != head:",
        "if False:",
    ),
    "public_identifier": ("foi_github_state", "    _slug(owner.lease_id)", "    pass"),
}


def check_mutant(name: str, replacement: tuple[str, str, str]) -> dict[str, object]:
    """Run each mutant against an isolated copy, rejecting infrastructure failures."""
    module, before, after = replacement
    source = Path(f"src/archive_govt_nz/{module}.py")
    test = f"tests/test_{module}.py"
    original = (ROOT / source).read_text(encoding="utf-8")
    if original.count(before) != 1:
        message = f"nonunique mutation target: {name}"
        raise ValueError(message)
    with tempfile.TemporaryDirectory(prefix="foi-integrity-mutant-") as temporary:
        stage = Path(temporary)
        shutil.copytree(ROOT / "src/archive_govt_nz", stage / "src/archive_govt_nz")
        (stage / source).write_text(original.replace(before, after), encoding="utf-8")
        environment = {**os.environ, "PYTHONPATH": str(stage / "src")}
        result = subprocess.run(  # noqa: S603 - fixed internal test module, no shell
            [
                sys.executable,
                "-m",
                "pytest",
                test,
                "-q",
                "--no-cov",
                "-o",
                f"cache_dir={stage / 'pytest-cache'}",
                "--maxfail=1",
            ],
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        return {
            "name": name,
            "exit_code": result.returncode,
            "killed": result.returncode == 1 and f"FAILED {test}" in result.stdout,
        }


def main() -> int:
    """Write a bounded mutation receipt and fail if any guard mutation survives."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(check_mutant, MUTATIONS, MUTATIONS.values()))
    receipt = {
        "scope": "shared GitHub authority control guards",
        "mutations": results,
        "passed": all(r["killed"] for r in results),
    }
    path = ROOT / "build/foi-shared-mutations.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
