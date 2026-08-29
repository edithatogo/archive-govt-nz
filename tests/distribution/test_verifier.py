"""Test suite for RemoteReadbackVerifier."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.distribution.publisher import (
    DistributionPublisher,
    DistributionTarget,
)
from archive_govt_nz.distribution.verifier import RemoteReadbackVerifier

if TYPE_CHECKING:
    from pathlib import Path


def test_verify_hf_package_structure(tmp_path: Path) -> None:
    """Test verification of Hugging Face package structure."""
    pq_path = tmp_path / "dummy.parquet"
    pq_path.write_bytes(b"PAR1dummypq")

    staging = tmp_path / "staged_hf"
    DistributionPublisher.build_hf_dataset_package("gazette", pq_path, staging)

    digests = RemoteReadbackVerifier.verify_hf_package_structure(staging)
    assert "README.md" in digests
    assert "croissant.json" in digests
    assert "dcat.jsonld" in digests
    assert "data/corpus.parquet" in digests
    assert len(digests["data/corpus.parquet"]) == 64

    (staging / "croissant.json").unlink()
    with pytest.raises(FileNotFoundError, match=r"croissant\.json"):
        RemoteReadbackVerifier.verify_hf_package_structure(staging)


def test_verify_publication_receipt(tmp_path: Path) -> None:
    """Test verification of PublicationReceipt stats."""
    f1 = tmp_path / "f1.txt"
    f1.write_text("hello")
    f2 = tmp_path / "f2.txt"
    f2.write_text("world")

    bundle_zip = tmp_path / "bundle.zip"
    receipt = DistributionPublisher.publish_dry_run(
        target=DistributionTarget.ZENODO,
        remote_identifier="zenodo.12345",
        files=[f1, f2],
        output_bundle_path=bundle_zip,
    )

    assert (
        RemoteReadbackVerifier.verify_local_bundle_fixity(
            bundle_zip, receipt.sha256_bundle_root
        )
        is True
    )
    assert RemoteReadbackVerifier.verify_publication_receipt(receipt, [f1, f2]) is True
    assert (
        RemoteReadbackVerifier.verify_local_bundle_fixity(
            tmp_path / "missing.zip", receipt.sha256_bundle_root
        )
        is False
    )
