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
