"""Read-only, fail-closed verification of a local health release candidate."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn

from archive_govt_nz.domains.health_appropriations.inventory import Disposition

_SCHEMA = "archive-govt-nz.health-hf-candidate/v1"
_DATASET = "edithatogo/nz-health-appropriations"
_REVISION_LENGTH = 40
_TERMINAL_DISPOSITIONS = frozenset(Disposition) - {
    Disposition.DISCOVERED,
    Disposition.RETRYABLE,
}
_REQUIRED_METADATA = frozenset(
    {
        "README.md",
        "metadata/croissant.json",
        "metadata/dcat.json",
        "metadata/prov.json",
        "metadata/rights.json",
        "metadata/source-census.json",
        "ro-crate-metadata.json",
    }
)


@dataclass(frozen=True)
class ReleaseExpectation:
    """Exact pins and freshness boundary for one readiness decision."""

    manifest_sha256: str
    assurance_path: Path
    assurance_sha256: str
    code_revision: str
    as_of: datetime
    maximum_age: timedelta


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _relative(raw: object) -> PurePosixPath:
    if not isinstance(raw, str):
        _fail("unsafe_candidate_path")
    path = PurePosixPath(raw)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        _fail("unsafe_candidate_path")
    return path


def _verify_files(root: Path, records: object) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        _fail("candidate_manifest_invalid")
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        relative = _relative(record.get("path") if isinstance(record, dict) else None)
        key = relative.as_posix()
        if key in indexed or key == "MANIFEST.json":
            _fail("candidate_manifest_invalid")
        path = root.joinpath(*relative.parts)
        prefixes = [
            root.joinpath(*relative.parts[:index])
            for index in range(1, len(relative.parts) + 1)
        ]
        try:
            confined = path.resolve(strict=True).is_relative_to(
                root.resolve(strict=True)
            )
        except OSError:
            confined = False
        if (
            any(prefix.is_symlink() for prefix in prefixes)
            or not confined
            or not path.is_file()
        ):
            _fail("candidate_file_missing")
        if path.stat().st_size != record.get("bytes") or _sha256(path) != record.get(
            "sha256"
        ):
            _fail("candidate_file_mismatch")
        indexed[key] = record
    return indexed


def _validate_closure(
    root: Path, manifest_path: Path, indexed: dict[str, dict[str, Any]]
) -> None:
    entries = list(root.rglob("*"))
    if any(path.is_symlink() for path in entries):
        _fail("candidate_file_set_mismatch")
    actual = {
        path.relative_to(root).as_posix()
        for path in entries
        if path.is_file() and path != manifest_path
    }
    expected_directories = {
        parent.as_posix()
        for relative in map(PurePosixPath, indexed)
        for parent in relative.parents
        if parent != PurePosixPath(".")
    }
    actual_directories = {
        path.relative_to(root).as_posix() for path in entries if path.is_dir()
    }
    if actual != set(indexed) or actual_directories != expected_directories:
        _fail("candidate_file_set_mismatch")


def verify_candidate(root: Path, *, expected_manifest_sha256: str) -> dict[str, Any]:
    """Verify exact bytes and release gates without changing candidate state."""
    if root.is_symlink() or not root.is_dir():
        _fail("unsafe_candidate_root")
    manifest_path = root / "MANIFEST.json"
    if (
        manifest_path.is_symlink()
        or not manifest_path.is_file()
        or _sha256(manifest_path) != expected_manifest_sha256
    ):
        _fail("candidate_manifest_mismatch")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != _SCHEMA or manifest.get("dataset") != _DATASET:
        _fail("candidate_identity_mismatch")
    if (
        manifest.get("rights_gate") != "passed_for_included_resources"
        or manifest.get("source_disposition_gate") != "passed"
        or manifest.get("candidate_state")
        != "release_candidate_pending_exact_manifest_approval"
    ):
        _fail("candidate_release_gate_failed")

    indexed = _verify_files(root, manifest.get("files"))

    _validate_closure(root, manifest_path, indexed)
    if not set(indexed) >= _REQUIRED_METADATA:
        _fail("candidate_metadata_incomplete")

    rights = json.loads((root / "metadata/rights.json").read_text(encoding="utf-8"))
    resources = rights.get("resources", [])
    if not isinstance(resources, list) or any(
        not isinstance(row, dict)
        or not all(
            row.get(key)
            for key in (
                "path",
                "license",
                "rights_evidence",
                "attribution",
                "eligibility",
            )
        )
        or row["eligibility"] != "verified_eligible"
        for row in resources
    ):
        _fail("candidate_rights_mismatch")
    rights_paths = [_relative(row["path"]).as_posix() for row in resources]
    originals = sorted(path for path in indexed if path.startswith("original/"))
    if sorted(rights_paths) != originals or len(rights_paths) != len(set(rights_paths)):
        _fail("candidate_rights_mismatch")
    census = json.loads(
        (root / "metadata/source-census.json").read_text(encoding="utf-8")
    )
    census_rows = census.get("records")
    if (
        not isinstance(census_rows, list)
        or not census_rows
        or any(
            not isinstance(row, dict)
            or row.get("disposition") not in _TERMINAL_DISPOSITIONS
            for row in census_rows
        )
    ):
        _fail("candidate_source_disposition_incomplete")
    return {
        "schema_version": "archive-govt-nz.health-candidate-verification/v1",
        "status": "passed",
        "dataset": _DATASET,
        "manifest_sha256": expected_manifest_sha256,
        "files_verified": len(indexed),
        "originals_with_rights": len(originals),
        "publication_performed": False,
    }


def verify_release_readiness(
    root: Path,
    expectation: ReleaseExpectation,
) -> dict[str, Any]:
    """Bind candidate bytes to fresh, exact parity and recovery evidence."""
    candidate = verify_candidate(
        root, expected_manifest_sha256=expectation.manifest_sha256
    )
    if (
        expectation.assurance_path.is_symlink()
        or not expectation.assurance_path.is_file()
        or _sha256(expectation.assurance_path) != expectation.assurance_sha256
    ):
        _fail("candidate_assurance_mismatch")
    evidence = json.loads(expectation.assurance_path.read_text(encoding="utf-8"))
    revision = evidence.get("code_revision")
    if (
        revision != expectation.code_revision
        or not isinstance(revision, str)
        or len(revision) != _REVISION_LENGTH
        or any(char not in "0123456789abcdef" for char in revision)
        or evidence.get("candidate_manifest_sha256") != expectation.manifest_sha256
    ):
        _fail("candidate_revision_unpinned")
    if evidence.get("parity") != "passed" or evidence.get("recovery") != "passed":
        _fail("candidate_assurance_failed")
    try:
        validated_at = datetime.fromisoformat(evidence["validated_at"])
    except KeyError, TypeError, ValueError:
        _fail("candidate_assurance_time_invalid")
    if validated_at.tzinfo is None or validated_at.utcoffset() != timedelta(0):
        _fail("candidate_assurance_time_invalid")
    if expectation.as_of.tzinfo is None or expectation.as_of.utcoffset() != timedelta(
        0
    ):
        _fail("candidate_assurance_time_invalid")
    age = expectation.as_of.astimezone(UTC) - validated_at.astimezone(UTC)
    if age < timedelta(0) or age > expectation.maximum_age:
        _fail("candidate_assurance_stale")
    return {
        **candidate,
        "assurance_sha256": expectation.assurance_sha256,
        "code_revision": revision,
        "parity": "passed",
        "recovery": "passed",
        "validated_at": evidence["validated_at"],
    }
