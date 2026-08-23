"""Run bounded source mutations against global rights and policy tests."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).parents[1]
SOURCE_RELATIVE = Path("src/archive_govt_nz/global_policy.py")
TEST_ARGUMENTS = ("tests/test_global_policy.py", "-q")
MUTATIONS = {
    "scheme_acceptance": ('parsed.scheme != "https"', 'parsed.scheme == "https"'),
    "size_budget": (
        "if isinstance(size, int) and size > max_bytes:",
        "if isinstance(size, int) and size < max_bytes:",
    ),
    "open_license": (
        "if not is_open_license(effective_license_id, effective_license_title):",
        "if is_open_license(effective_license_id, effective_license_title):",
    ),
    "eligible_reason": (
        '"open_license_https_within_budget"',
        '"mutated_open_license"',
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
            [str(root / "src"), existing_pythonpath]
            if existing_pythonpath
            else [str(root / "src")]
        )
        command = ("pytest", *TEST_ARGUMENTS)
        process = subprocess.run(
            command,
            cwd=REPOSITORY_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        killed = process.returncode != 0
        return {
            "name": name,
            "returncode": process.returncode,
            "killed": killed,
        }


def main() -> int:
    """Run all configured mutations and fail closed on any survivor."""
    original_path = REPOSITORY_ROOT / SOURCE_RELATIVE
    original = original_path.read_text(encoding="utf-8")
    mutants: list[dict[str, object]] = []
    for name, (before, after) in MUTATIONS.items():
        mutants.append(_run_mutant(name, original, before, after))
    killed = sum(1 for mutant in mutants if bool(mutant["killed"]))
    total = len(mutants)
    payload = {
        "schema_version": "archive-govt-nz.mutation/v1",
        "source": SOURCE_RELATIVE.as_posix(),
        "mutants": mutants,
        "killed": killed,
        "total": total,
        "status": "passed" if killed == total else "failed",
    }
    print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    return 0 if killed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
