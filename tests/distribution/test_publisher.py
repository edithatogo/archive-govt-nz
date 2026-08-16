"""Test suite for DistributionPublisher and multi-target distribution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.distribution.publisher import (
    DistributionPublisher,
    DistributionTarget,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_prepare_release_bundle_and_receipt(tmp_path: Path) -> None:
    """Validate release bundle zip and publication receipt creation."""
    f1 = tmp_path / "data1.txt"
    f2 = tmp_path / "data2.txt"
    f1.write_bytes(b"File 1 content")
    f2.write_bytes(b"File 2 content")

    bundle_zip = tmp_path / "release.zip"
    sha, count, total_bytes = DistributionPublisher.prepare_release_bundle(
        [f1, f2], bundle_zip
    )
    assert bundle_zip.is_file()
    assert count == 2
    assert total_bytes == len(b"File 1 content") + len(b"File 2 content")
    assert len(sha) == 64

    receipt = DistributionPublisher.create_publication_receipt(
        target=DistributionTarget.HUGGINGFACE,
        remote_identifier="edithatogo/nz-govt-archive",
        bundle_sha256=sha,
        bundle_stats=(count, total_bytes),
    )
    assert receipt.target_platform == "huggingface"
    assert receipt.file_count == 2
    assert receipt.status == "published"


def test_publish_dry_run(tmp_path: Path) -> None:
    """Validate publish_dry_run packaging."""
    f1 = tmp_path / "sample.parquet"
    f1.write_bytes(b"PAR1dummydata")
    bundle_zip = tmp_path / "dry_run_bundle.zip"

    receipt = DistributionPublisher.publish_dry_run(
        target=DistributionTarget.ZENODO,
        remote_identifier="10.5281/zenodo.123456",
        files=[f1],
        output_bundle_path=bundle_zip,
    )
    assert receipt.target_platform == "zenodo"
    assert receipt.status == "verified"
    assert receipt.file_count == 1
