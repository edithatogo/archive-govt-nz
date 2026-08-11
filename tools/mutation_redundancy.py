"""Run bounded source mutations against redundancy integrity tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[1]
SOURCE_RELATIVE = Path("src/archive_govt_nz/redundancy.py")
TEST_ARGUMENTS = ("tests/redundancy/test_redundancy.py", "-q")
MUTATIONS = {
    "archive_scheme": (
        'parsed.scheme != "https"\n        or parsed.hostname != _ARCHIVE_HOST',
        'parsed.scheme == "https"\n        or parsed.hostname != _ARCHIVE_HOST',
    ),
    "archive_host": (
        "parsed.hostname != _ARCHIVE_HOST",
        "parsed.hostname == _ARCHIVE_HOST",
    ),
    "source_allowlist": (
        "parsed.hostname not in policy.allowed_source_hosts",
        "parsed.hostname in policy.allowed_source_hosts",
    ),
    "object_size": (
        "path.stat().st_size != expected_size",
        "path.stat().st_size == expected_size",
    ),
    "object_hash": (
        "digest.hexdigest() != expected_sha256",
        "digest.hexdigest() == expected_sha256",
    ),
    "conflict_classification": ('"conflict"', '"mutated-conflict"'),
}


def _run_mutant(name: str, original: str, before: str, after: str) -> dict[str, object]:
    """Run one mutation in an isolated package source directory."""
    if original.count(before) != 1:
        message = f"mutation target is not unique: {name}"
        raise RuntimeError(message)
    with tempfile.TemporaryDirectory(
        prefix="archive-govt-nz-redundancy-mutant-"
    ) as directory:
        root = Path(directory)
        package_source = root / "src" / "archive_govt_nz"
        package_source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(REPOSITORY_ROOT / "src" / "archive_govt_nz", package_source)
        mutated_source = root / SOURCE_RELATIVE
        mutated_source.write_text(original.replace(before, after), encoding="utf-8")
        environment = os.environ.copy()
        existing_pythonpath = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = os.pathsep.join(
            item for item in (str(root / "src"), existing_pythonpath) if item
        )
        result = subprocess.run(
            ["uv", "run", "--locked", "pytest", *TEST_ARGUMENTS],
            cwd=REPOSITORY_ROOT,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        return {
            "name": name,
            "returncode": result.returncode,
            "killed": result.returncode != 0,
        }


def main() -> int:
    """Require every targeted redundancy mutation to be detected."""
    original = (REPOSITORY_ROOT / SOURCE_RELATIVE).read_text(encoding="utf-8")
    results = [
        _run_mutant(name, original, before, after)
        for name, (before, after) in MUTATIONS.items()
    ]
    killed = sum(result["killed"] is True for result in results)
    receipt = {
        "schema_version": "archive-govt-nz.mutation/v1",
        "source": str(SOURCE_RELATIVE).replace("\\", "/"),
        "mutants": results,
        "killed": killed,
        "total": len(results),
        "status": "passed" if killed == len(results) else "failed",
    }
    output = REPOSITORY_ROOT / "build" / "mutation-redundancy.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, separators=(",", ":")))
    return 0 if killed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
