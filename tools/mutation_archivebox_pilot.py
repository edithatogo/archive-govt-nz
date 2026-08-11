"""Run bounded source mutations against ArchiveBox pilot integrity tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[1]
SOURCE_RELATIVE = Path("src/archive_govt_nz/archivebox_pilot.py")
TEST_ARGUMENTS = ("tests/archivebox/test_archivebox_pilot.py", "-q")
MUTATIONS = {
    "https_required": ('parsed.scheme != "https"', 'parsed.scheme == "https"'),
    "host_allowlist": (
        "parsed.hostname not in _ALLOWED_HOSTS",
        "parsed.hostname in _ALLOWED_HOSTS",
    ),
    "candidate_limit": (
        "len(urls) > _MAX_CANDIDATES",
        "len(urls) < _MAX_CANDIDATES",
    ),
    "duplicate_rejection": (
        "len(set(urls)) != len(urls)",
        "len(set(urls)) == len(urls)",
    ),
    "digest_pin": (
        "not _IMAGE_PATTERN.fullmatch(image)",
        "_IMAGE_PATTERN.fullmatch(image)",
    ),
    "aggregate_byte_limit": (
        "total_bytes > max_total_bytes",
        "total_bytes < max_total_bytes",
    ),
    "secondary_role": (
        (
            '"role": _output_role(relative),\n'
            '                "authoritative_original": False'
        ),
        (
            '"role": _output_role(relative),\n'
            '                "authoritative_original": True'
        ),
    ),
    "snapshot_candidate_reconciliation": (
        "if seen != expected:",
        "if seen == expected:",
    ),
    "snapshot_original_not_verified": (
        '"original_payload_verified": False',
        '"original_payload_verified": True',
    ),
}


def _run_mutant(name: str, original: str, before: str, after: str) -> dict[str, object]:
    """Run one mutation against an isolated package source copy."""
    if original.count(before) != 1:
        message = f"mutation target is not unique: {name}"
        raise RuntimeError(message)
    with tempfile.TemporaryDirectory(
        prefix="archive-govt-nz-archivebox-mutant-"
    ) as directory:
        root = Path(directory)
        package_source = root / "src/archive_govt_nz"
        package_source.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(REPOSITORY_ROOT / "src/archive_govt_nz", package_source)
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
    """Require every targeted ArchiveBox pilot mutation to be detected."""
    original = (REPOSITORY_ROOT / SOURCE_RELATIVE).read_text(encoding="utf-8")
    results = [
        _run_mutant(name, original, before, after)
        for name, (before, after) in MUTATIONS.items()
    ]
    killed = sum(result["killed"] is True for result in results)
    receipt = {
        "schema_version": "archive-govt-nz.mutation/v1",
        "source": SOURCE_RELATIVE.as_posix(),
        "mutants": results,
        "killed": killed,
        "total": len(results),
        "status": "passed" if killed == len(results) else "failed",
    }
    output = REPOSITORY_ROOT / "build/mutation-archivebox-pilot.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, separators=(",", ":")))
    return 0 if killed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
