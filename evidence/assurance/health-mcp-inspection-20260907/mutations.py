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
MODULE = "src/archive_govt_nz/mcp_health_inspection.py"
SERVER = "src/archive_govt_nz/mcp_server.py"
CASES = {
    "preview_default": (
        MODULE,
        'rows=arguments.get("rows", 0)',
        'rows=arguments.get("rows", 1)',
    ),
    "preview_selection": (MODULE, 'sheet=arguments.get("sheet")', 'sheet="Missing"'),
    "column_selection": (MODULE, 'columns=arguments.get("columns", 12)', "columns=1"),
    "pin_binding": (MODULE, 'arguments["expected_sha256"],', '"0" * 64,'),
    "integer_types": (MODULE, "type(arguments[key]) is not int", "False"),
    "input_validation": (MODULE, "if invalid:", "if False:"),
    "direct_validation": (MODULE, "    validate_arguments(arguments)", "    pass"),
    "protocol_redaction": (
        SERVER,
        '"Invalid workbook inspection arguments"',
        '"unredacted"',
    ),
}


def run(case: tuple[str, str, str] | None) -> int:
    """Require test assertion failures, not collection errors, for each mutant."""
    with tempfile.TemporaryDirectory(
        prefix="health-mcp-inspection-mutant-"
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
                "tests/mcp/test_health_inspection.py",
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
