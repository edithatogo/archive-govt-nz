"""Bounded cold mutations of isolated source copies; never edit working source."""

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
MODULE = "src/archive_govt_nz/warc_binding.py"
CASES = {
    "skip_framing": ("        _verify_capture_framing(payload)", "        pass"),
    "suffix_only": (
        'block[int(lengths[0]) :] != b"\\r\\n\\r\\n"',
        'not block.endswith(b"\\r\\n\\r\\n")',
    ),
    "extra_terminator": (
        'block[int(lengths[0]) :] != b"\\r\\n\\r\\n"',
        'not block[int(lengths[0]) :].startswith(b"\\r\\n\\r\\n")',
    ),
    "duplicate_length": ("len(lengths) != 1", "not lengths"),
    "duplicate_content_type": (
        "]\n                != ([] if content_type is None else [content_type])",
        "][:1]\n                != ([] if content_type is None else [content_type])",
    ),
    "case_sensitive_content_type": (
        'if key.lower() == "content-type"',
        'if key == "content-type"',
    ),
    "length_offset": ("block[int(lengths[0]) :]", "block[int(lengths[0]) + 1 :]"),
}


def run(case: tuple[str, str] | None) -> dict[str, int | bool]:
    """Require pytest assertion failures, not collection errors, for kills."""
    with tempfile.TemporaryDirectory(prefix="warc-framing-mutant-") as directory:
        root = Path(directory)
        shutil.copytree(
            ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__")
        )
        if case is not None:
            old, new = case
            path = root / MODULE
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
                "tests/warc/test_warc_binding_strict.py",
            ],
            cwd=ROOT,
            env={
                **os.environ,
                "PYTHONPATH": str(root / "src"),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
        return {
            "exit_code": result.returncode,
            "assertion_failure": "FAILED tests/" in result.stdout,
            "collection_error": "ERROR collecting" in result.stdout,
        }


def main() -> int:
    """Print only bounded outcomes; no fixture contents or environment values."""
    baseline = run(None)
    if baseline["exit_code"]:
        return 1
    results = {name: run(case) for name, case in CASES.items()}
    print(json.dumps({"baseline": baseline, "mutants": results}, sort_keys=True))  # noqa: T201
    return (
        0
        if all(
            value["exit_code"] == 1
            and value["assertion_failure"]
            and not value["collection_error"]
            for value in results.values()
        )
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
