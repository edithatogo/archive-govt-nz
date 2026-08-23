"""Run bounded source mutations against gazette domain integrity tests."""

from __future__ import annotations

import concurrent.futures
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[1]
SOURCE_RELATIVE = Path("src/archive_govt_nz/domains/gazette/validate.py")
TEST_ARGUMENTS = ("tests/domains/test_gazette_service.py", "-q")
MUTATIONS = {
    "notice_id_field": (
        'str(record.get("notice_id", "")).strip()',
        'str(record.get("issue_number", "")).strip()',
    ),
    "hash_wrong_field": (
        '_HASH_REGEX.match(str(record.get("raw_cas_hash_sha256", "")))',
        '_HASH_REGEX.match(str(record.get("title", "")))',
    ),
    "uri_scheme_drop_https": (
        'canonical_uri.startswith(("http://", "https://"))',
        'canonical_uri.startswith(("http://",))',
    ),
    "chronology_direction": (
        "if retrieved > datetime.now(tz=UTC):",
        "if retrieved < datetime.now(tz=UTC):",
    ),
    "iso_parse_guard": ("except ValueError:", "except TypeError:"),
    "year_bounds_flip": (
        "elif not _MIN_YEAR <= year <= _MAX_YEAR:",
        "elif _MIN_YEAR <= year <= _MAX_YEAR:",
    ),
    "bool_year_accepted": (
        "or isinstance(year, bool)",
        "and isinstance(year, bool)",
    ),
}


def _run_mutant(name: str, original: str, before: str, after: str) -> dict[str, object]:
    """Run one mutation in an isolated source directory."""
    if original.count(before) != 1:
        message = f"mutation target is not unique: {name}"
        raise RuntimeError(message)
    with tempfile.TemporaryDirectory(prefix="archive-govt-nz-mutant-") as directory:
        root = Path(directory)
        package_source = root / "src" / "archive_govt_nz"
        package_source.parent.mkdir(parents=True, exist_ok=True)
        original_package = REPOSITORY_ROOT / "src" / "archive_govt_nz"
        shutil.copytree(original_package, package_source)
        mutated_source = root / SOURCE_RELATIVE
        mutated_source.write_text(original.replace(before, after), encoding="utf-8")
        environment = os.environ.copy()
        existing_pythonpath = environment.get("PYTHONPATH", "")
        environment["PYTHONPATH"] = os.pathsep.join(
            item for item in (str(root / "src"), existing_pythonpath) if item
        )
        result = subprocess.run(
            [sys.executable, "-m", "pytest", *TEST_ARGUMENTS],
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
    """Require every targeted mutation to be detected by gazette domain tests."""
    source_path = REPOSITORY_ROOT / SOURCE_RELATIVE
    original = source_path.read_text(encoding="utf-8")
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=min(8, os.cpu_count() or 4)
    ) as executor:
        futures = [
            executor.submit(_run_mutant, name, original, before, after)
            for name, (before, after) in MUTATIONS.items()
        ]
        results = [f.result() for f in futures]
    killed = sum(1 for result in results if result["killed"] is True)
    receipt = {
        "schema_version": "archive-govt-nz.mutation/v1",
        "source": str(SOURCE_RELATIVE).replace("\\", "/"),
        "mutants": results,
        "killed": killed,
        "total": len(results),
        "status": "passed" if killed == len(results) else "failed",
    }
    output = REPOSITORY_ROOT / "build" / "mutation-gazette.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(receipt, separators=(",", ":")))
    return 0 if killed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
