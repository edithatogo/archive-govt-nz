"""Cross-target release reconciliation tests."""

import hashlib
import tarfile
from pathlib import Path

from archive_govt_nz.release_reconciliation import (
    reconcile_release_records,
    verify_release_archive,
)


def test_reconciliation_requires_all_remote_receipts() -> None:
    """Matching package and complete remote receipts produce a reconciled state."""
    report = reconcile_release_records(
        {"package": {"sha256": "abc"}},
        {"revision": "hf-revision"},
        {
            "package_sha256": "abc",
            "state": "published",
            "doi": "10.5281/zenodo.7",
            "file_size": 10,
            "zenodo_checksum": "md5:abc",
        },
    )
    assert report.state == "reconciled"
    assert all(check.state in {"matched", "verified"} for check in report.checks)


def test_reconciliation_fails_closed_on_hash_drift_or_missing_receipt() -> None:
    """A drift or incomplete remote record cannot be called reconciled."""
    report = reconcile_release_records(
        {"package": {"sha256": "abc"}},
        {},
        {"package_sha256": "different", "state": "published"},
    )
    assert report.state == "incomplete"
    assert {check.state for check in report.checks} >= {"drifted", "unavailable"}


def test_reconciliation_reports_missing_package_hashes() -> None:
    """A receipt without either package hash remains unavailable."""
    report = reconcile_release_records({}, {}, {})
    assert report.checks[0].state == "unavailable"


def test_recovery_verification_checks_checksum_and_layer_closure(
    tmp_path: Path,
) -> None:
    """A recovered package must contain raw, object, and derivative layers."""
    archive = tmp_path / "release.tar"
    with tarfile.open(archive, "w") as handle:
        for name in (
            "raw/package_search.json",
            "objects/sha256/aa/hash",
            "derivatives/datasets.parquet",
        ):
            source = tmp_path / name.replace("/", "_")
            source.write_bytes(b"x")
            handle.add(source, arcname=name)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    check = verify_release_archive(
        archive, digest, ("raw/", "objects/", "derivatives/")
    )
    assert check.state == "verified"


def test_recovery_verification_reports_missing_drift_invalid_and_incomplete(
    tmp_path: Path,
) -> None:
    """Recovery evidence distinguishes each bounded failure class."""
    missing = verify_release_archive(tmp_path / "missing.tar", "a" * 64, ("raw/",))
    assert missing.state == "unavailable"
    archive = tmp_path / "plain.tar"
    archive.write_bytes(b"not a tar")
    drift = verify_release_archive(archive, "a" * 64, ("raw/",))
    assert drift.state == "drifted"
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    invalid = verify_release_archive(archive, digest, ("raw/",))
    assert invalid.state == "invalid"
    incomplete_archive = tmp_path / "incomplete.tar"
    with tarfile.open(incomplete_archive, "w") as handle:
        handle.add(archive, arcname="raw/only.json")
    incomplete_digest = hashlib.sha256(incomplete_archive.read_bytes()).hexdigest()
    incomplete = verify_release_archive(
        incomplete_archive, incomplete_digest, ("raw/", "objects/")
    )
    assert incomplete.state == "incomplete"
    unsafe_archive = tmp_path / "unsafe.tar"
    with tarfile.open(unsafe_archive, "w") as handle:
        handle.add(archive, arcname="../unsafe")
    unsafe_digest = hashlib.sha256(unsafe_archive.read_bytes()).hexdigest()
    unsafe = verify_release_archive(unsafe_archive, unsafe_digest, ("raw/",))
    assert unsafe.state == "invalid"
