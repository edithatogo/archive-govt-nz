"""Cold isolated metadata-application mutants; never edits repository sources."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(
    "src/archive_govt_nz/domains/health_appropriations/metadata_application.py"
)
TEST = "tests/domains/health_appropriations/test_metadata_application.py"
MUTANTS = {
    "metadata_root_casefold": (
        'str(value).split("/", 1)[0].casefold() not in _METADATA_ROOTS',
        'str(value).split("/", 1)[0] not in _METADATA_ROOTS',
    ),
    "metadata_root_descendants": (
        'str(value).split("/", 1)[0].casefold() not in _METADATA_ROOTS',
        "str(value).casefold() not in _METADATA_ROOTS",
    ),
    "metadata_directory_reservation": (
        '"readme.md", "metadata"',
        '"readme.md", "metadata-disabled"',
    ),
    "croissant_binding": (
        "json.dumps(croissant, sort_keys=True) == json.dumps(expected, sort_keys=True)",
        "True",
    ),
    "crate_binding": (
        'json.dumps(manifest["ro_crate"], sort_keys=True)\n        == json.dumps(expected_crate, sort_keys=True)',
        "True",
    ),
    "metadata_pin": ("_require(hashlib.sha256(payload).hexdigest() == pin)", "pass"),
    "duplicate_json": ("_require(key not in result)", "pass"),
    "json_bound": ("len(payload) <= MAX_JSON", "len(payload) < MAX_JSON"),
    "path_reserved": ('part.split(".")[0].upper() not in _RESERVED', "True"),
    "item_bound": ("len(records) <= MAX_ITEMS", "len(records) < MAX_ITEMS"),
    "payload_bound": (
        'row["size_bytes"] <= MAX_PAYLOAD',
        'row["size_bytes"] < MAX_PAYLOAD',
    ),
    "payload_total": ("total <= MAX_TOTAL", "total < MAX_TOTAL"),
    "payload_sha": (
        '_require(hashlib.sha256(payload).hexdigest() == row["sha256"])',
        "pass",
    ),
    "payload_blake3": (
        '_require(blake3.blake3(payload).hexdigest() == row["blake3"])',
        "pass",
    ),
    "bundle_root": (
        '_require(compute_bundle_root_digest(items) == manifest["bundle_root_sha256"])',
        "pass",
    ),
    "domain": ('_require(row["domain"] == "health_appropriations")', "pass"),
    "rights_binding": (
        '_require(row["payload_sha256"] == expected[row["path"]])',
        "pass",
    ),
    "rights_duplicate": ('and row["path"] not in seen', "and True"),
    "rights_schema": (
        'document["schema_version"]\n        == "archive-govt-nz.health-metadata-rights-assertions/v1"',
        "True",
    ),
    "rights_licence": ('_require(row["license"] is None)', "pass"),
    "rights_evidence": ('_pin(row["evidence_sha256"])', "pass"),
    "dataset_identity": (
        '_require(manifest["bundle_name"] == "nz-health-appropriations")',
        "pass",
    ),
    "manifest_version": (
        '_require(manifest["schema_version"] == SCHEMA_VERSION)',
        "pass",
    ),
    "targets": ('_require(manifest["platforms"] == [])', "pass"),
    "timestamp_zone": ("_require(timestamp.utcoffset() is not None)", "pass"),
    "timestamp_unknown": (
        '_require(not manifest["created_at"].endswith("-00:00"))',
        "pass",
    ),
    "approval": (
        '"publication_approval": "not_granted"',
        '"publication_approval": "granted"',
    ),
    "conformance": ('"full_conformance": False', '"full_conformance": True'),
}


def run(needle: str, replacement: str) -> int:
    """Run the scoped test file on a temporary source copy."""
    original = (ROOT / SOURCE).read_text(encoding="utf-8")
    if needle and original.count(needle) != 1:
        message = "mutation target not unique"
        raise ValueError(message)
    with tempfile.TemporaryDirectory(prefix="health-metadata-mutant-") as directory:
        root = Path(directory)
        shutil.copytree(
            ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__")
        )
        (root / SOURCE).write_text(
            original.replace(needle, replacement, 1) if needle else original,
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                "-m",
                "pytest",
                TEST,
                "-q",
                "--no-cov",
                "-p",
                "no:cacheprovider",
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
    """Require baseline success and pytest test failures for every mutant."""
    baseline = run("", "")
    if baseline:
        return baseline
    results = {name: run(*mutation) for name, mutation in MUTANTS.items()}
    print(json.dumps({"baseline": baseline, "mutants": results}, sort_keys=True))  # noqa: T201
    return 0 if all(code == 1 for code in results.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
