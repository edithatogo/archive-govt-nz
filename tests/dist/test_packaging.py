"""Tests for the publication packaging engine, RO-Crate, and Croissant metadata."""

from __future__ import annotations

import json
from pathlib import Path

from archive_govt_nz.dist.packaging import (
    PublicationItem,
    TargetPlatformConfig,
    build_publication_manifest,
    compute_bundle_root_digest,
    compute_file_fixity,
    generate_croissant_metadata,
    generate_ro_crate_metadata,
    save_publication_manifest,
)


def test_compute_file_fixity(tmp_path: Path) -> None:
    """Compute sha256 and blake3 digests for test file."""
    test_file = tmp_path / "sample.txt"
    test_file.write_text("Hello NZ Open Government Archive\n", encoding="utf-8")

    sha256, blake3_hex, size = compute_file_fixity(test_file)
    assert len(sha256) == 64
    assert len(blake3_hex) == 64
    assert size == len("Hello NZ Open Government Archive\n")


def test_compute_bundle_root_digest() -> None:
    """Compute deterministic bundle root digest regardless of item ordering."""
    item1 = PublicationItem(
        item_path="data/silver/a.parquet",
        sha256="1" * 64,
        blake3="2" * 64,
        size_bytes=100,
        media_type="application/vnd.apache.parquet",
    )
    item2 = PublicationItem(
        item_path="data/silver/b.parquet",
        sha256="3" * 64,
        blake3="4" * 64,
        size_bytes=200,
        media_type="application/vnd.apache.parquet",
    )

    root1 = compute_bundle_root_digest([item1, item2])
    root2 = compute_bundle_root_digest([item2, item1])
    empty_root = compute_bundle_root_digest([])
    assert root1 == root2
    assert root1 != empty_root
    assert len(root1) == 64


def test_generate_ro_crate_and_croissant_metadata() -> None:
    """Generate compliant RO-Crate and Croissant metadata graphs."""
    item = PublicationItem(
        item_path="data/silver/legislation/corpus.parquet",
        sha256="a" * 64,
        blake3="b" * 64,
        size_bytes=1024,
        media_type="application/vnd.apache.parquet",
        domain="legislation",
    )

    ro_crate = generate_ro_crate_metadata("NZ Corpus", "2026.08.24", [item])
    assert ro_crate["@context"] == "https://w3id.org/ro/crate/1.1/context"
    assert len(ro_crate["@graph"]) == 3

    croissant = generate_croissant_metadata("NZ Corpus", "2026.08.24", [item])
    assert croissant["@type"] == "sc:Dataset"
    assert len(croissant["distribution"]) == 1


def test_build_and_save_publication_manifest(tmp_path: Path) -> None:
    """Build, validate, and persist a full PublicationManifest."""
    item = PublicationItem(
        item_path="data/silver/gazette/corpus.parquet",
        sha256="c" * 64,
        blake3="d" * 64,
        size_bytes=2048,
        media_type="application/vnd.apache.parquet",
        domain="gazette",
    )
    platform = TargetPlatformConfig(
        platform="huggingface",
        target_identifier="datasets/nz/gazette",
        enabled=True,
    )

    manifest = build_publication_manifest(
        manifest_id="manifest-001",
        bundle_name="NZ Gazette Release",
        version="2026.08.24",
        items=[item],
        platforms=[platform],
    )

    assert manifest.schema_version == "archive-govt-nz.publication-manifest/v2"
    assert manifest.bundle_name == "NZ Gazette Release"
    assert len(manifest.bundle_root_sha256) == 64
    assert manifest.ro_crate is not None
    assert manifest.croissant is not None

    out_file = tmp_path / "manifest.json"
    save_publication_manifest(manifest, out_file)
    assert out_file.exists()

    loaded = json.loads(out_file.read_text(encoding="utf-8"))
    assert loaded["manifest_id"] == "manifest-001"
    assert loaded["items"][0]["domain"] == "gazette"
