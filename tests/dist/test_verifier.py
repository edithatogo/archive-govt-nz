"""Tests for PublicationVerifier manifest integrity and local fixity verification."""

from __future__ import annotations

from pathlib import Path

from archive_govt_nz.dist.packaging import (
    PublicationItem,
    PublicationManifest,
    TargetPlatformConfig,
    build_publication_manifest,
    compute_file_fixity,
)
from archive_govt_nz.dist.verifier import PublicationVerifier


def test_verifier_manifest_integrity() -> None:
    """Verifier confirms valid Merkle root and detects corrupted root digest."""
    item = PublicationItem(
        item_path="data/silver/test.parquet",
        sha256="1" * 64,
        blake3="2" * 64,
        size_bytes=100,
        media_type="application/vnd.apache.parquet",
    )
    manifest = build_publication_manifest(
        manifest_id="test-ver-01",
        bundle_name="Test Bundle",
        version="2026.08.24",
        items=[item],
        platforms=[TargetPlatformConfig(platform="zenodo", target_identifier="123")],
    )

    verifier = PublicationVerifier()
    rep = verifier.verify_manifest_integrity(manifest)
    assert rep.is_valid is True
    assert rep.items_checked == 1
    assert len(rep.errors) == 0

    # Corrupt root
    corrupt_manifest = PublicationManifest(
        schema_version=manifest.schema_version,
        manifest_id=manifest.manifest_id,
        bundle_name=manifest.bundle_name,
        version=manifest.version,
        created_at=manifest.created_at,
        bundle_root_sha256="0" * 64,
        items=manifest.items,
        platforms=manifest.platforms,
    )
    rep_corrupt = verifier.verify_manifest_integrity(corrupt_manifest)
    assert rep_corrupt.is_valid is False
    assert len(rep_corrupt.errors) == 1


def test_verifier_local_files(tmp_path: Path) -> None:
    """Verifier checks file contents against manifest hashes and detects mismatches."""
    rel_path = "data/silver/file1.txt"
    abs_file = tmp_path / rel_path
    abs_file.parent.mkdir(parents=True, exist_ok=True)
    abs_file.write_text("Valid Payload Content\n", encoding="utf-8")

    sha256, blake3_hex, size = compute_file_fixity(abs_file)
    item = PublicationItem(
        item_path=rel_path,
        sha256=sha256,
        blake3=blake3_hex,
        size_bytes=size,
        media_type="text/plain",
    )
    manifest = build_publication_manifest(
        manifest_id="test-ver-02",
        bundle_name="File Bundle",
        version="2026.08.24",
        items=[item],
        platforms=[],
    )

    verifier = PublicationVerifier()
    rep = verifier.verify_local_files(manifest, base_dir=tmp_path)
    assert rep.is_valid is True
    assert rep.items_passed == 1

    # Corrupt file content
    abs_file.write_text("Corrupted Content\n", encoding="utf-8")
    rep_corrupt = verifier.verify_local_files(manifest, base_dir=tmp_path)
    assert rep_corrupt.is_valid is False
    assert rep_corrupt.items_passed == 0
    assert len(rep_corrupt.errors) >= 1
