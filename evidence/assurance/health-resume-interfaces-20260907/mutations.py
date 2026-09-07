"""Cold bounded mutation checks in temporary copies, never the working source."""

# Standalone evidence recipe, not an importable package.
# ruff: noqa: INP001

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
MODULE = "src/archive_govt_nz/domains/health_appropriations/resume_operations.py"
SERVER = "src/archive_govt_nz/mcp_server.py"
CASES = {
    "duplicate_stage": (MODULE, "or name in result", "or False"),
    "stage_bound": (
        MODULE,
        "len(tokens) > len(PROFILES)",
        "len(tokens) >= len(PROFILES)",
    ),
    "stage_pin": (MODULE, 'or not re.fullmatch(r"[0-9a-f]{64}", digest)', "or False"),
    "default_write": (MODULE, "dry_run: bool = True", "dry_run: bool = False"),
    "plan_dispatch": (
        MODULE,
        "result = plan_resume(**kwargs)",
        "result = execute_resume(**kwargs)",
    ),
    "verify_dispatch": (
        MODULE,
        "result = verify_resume(**kwargs)",
        "result = execute_resume(**kwargs)",
    ),
    "input_contract": (
        MODULE,
        "Draft202012Validator(INPUTS[operation]).validate(arguments)",
        "pass",
    ),
    "mcp_failure": (MODULE, 'if result.get("status") == "failed":', "if False:"),
    "cli_exit": (
        MODULE,
        'return 2 if result.get("status") == "failed" else 0',
        "return 0",
    ),
    "plan_envelope": (
        MODULE,
        "return json.loads(json.dumps(result))",
        'return {"receipt": result}',
    ),
    "protocol_redaction": (
        SERVER,
        '"Invalid resume operation arguments"',
        '"unredacted"',
    ),
}


def run(case: tuple[str, str, str] | None) -> int:
    """Require test assertion failures, not collection errors, for each mutant."""
    with tempfile.TemporaryDirectory(
        prefix="health-resume-interface-mutant-"
    ) as directory:
        root = Path(directory)
        shutil.copytree(
            ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__")
        )
        if case is not None:
            relative, old, new = case
            path = root / relative
            source = path.read_text()
            if source.count(old) != 1:
                message = "mutation_target_not_unique"
                raise ValueError(message)
            path.write_text(source.replace(old, new, 1))
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "--no-cov",
                "tests/domains/health_appropriations/test_resume_operations.py",
            ],
            cwd=ROOT,
            env={
                **os.environ,
                "PYTHONPATH": str(root / "src"),
                "PYTHONDONTWRITEBYTECODE": "1",
                "HYPOTHESIS_STORAGE_DIRECTORY": str(root / "hypothesis"),
            },
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        return result.returncode


def main() -> int:
    """Print a bounded baseline and mutant outcome summary."""
    baseline = run(None)
    if baseline:
        return baseline
    results = {name: run(case) for name, case in CASES.items()}
    print(json.dumps({"baseline": baseline, "mutants": results}, sort_keys=True))  # noqa: T201
    return 0 if all(value == 1 for value in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
