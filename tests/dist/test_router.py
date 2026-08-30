"""Tests for PublicationRouter multi-target routing and credential handling."""

from __future__ import annotations

import os
from unittest.mock import patch

from archive_govt_nz.dist.packaging import (
    PublicationItem,
    PublicationManifest,
    TargetPlatformConfig,
    build_publication_manifest,
)
from archive_govt_nz.dist.router import PublicationRouter


def _sample_manifest() -> PublicationManifest:
    item = PublicationItem(
        item_path="data/silver/health/corpus.parquet",
        sha256="e" * 64,
        blake3="f" * 64,
        size_bytes=4096,
        media_type="application/vnd.apache.parquet",
        domain="health",
    )
    platforms = [
        TargetPlatformConfig(platform="huggingface", target_identifier="nz/health"),
        TargetPlatformConfig(platform="zenodo", target_identifier="12345"),
        TargetPlatformConfig(platform="osf", target_identifier="osf-nz-01"),
    ]
    return build_publication_manifest(
        manifest_id="test-pub-01",
        bundle_name="Health Bundle",
        version="2026.08.24",
        items=[item],
        platforms=platforms,
    )


def test_router_check_preflight_credentials() -> None:
    """Preflight check identifies present and missing credentials."""
    manifest = _sample_manifest()
    router = PublicationRouter()

    with patch.dict(os.environ, {"HF_TOKEN": "secret", "ZENODO_TOKEN": ""}, clear=True):
        creds = router.check_preflight_credentials(manifest)
        assert creds["huggingface"] is True
        assert creds["zenodo"] is False
        assert creds["osf"] is False


def test_router_publish_manifest_dry_run() -> None:
    """Dry-run cannot issue external publication identifiers."""
    manifest = _sample_manifest()
    router = PublicationRouter()

    receipts = router.publish_manifest(manifest, dry_run=True)
    assert len(receipts) == 3
    for r in receipts:
        assert r.status == "dry_run"
        assert r.doi is None
        assert r.commit_pinned_url is None
        assert r.file_count == 1
        assert r.total_bytes == 4096
        assert len(r.sha256_bundle_root) == 64
        d = r.to_dict()
        assert d["schema_version"] == "archive-govt-nz.publication-receipt/v1"


def test_router_publish_manifest_live_missing_creds() -> None:
    """Live publish without credentials produces failed receipts."""
    manifest = _sample_manifest()
    router = PublicationRouter()

    with patch.dict(os.environ, {}, clear=True):
        receipts = router.publish_manifest(manifest, dry_run=False)
        assert len(receipts) == 3
        for r in receipts:
            assert r.status == "failed"


def test_router_publish_manifest_live_with_creds() -> None:
    """Credentials alone never establish a remote publication."""
    manifest = _sample_manifest()
    router = PublicationRouter()

    env = {
        "HF_TOKEN": "hf_valid_token",
        "ZENODO_TOKEN": "zenodo_valid_token",
        "OSF_TOKEN": "osf_valid_token",
    }
    with patch.dict(os.environ, env, clear=True):
        receipts = router.publish_manifest(manifest, dry_run=False)
        assert len(receipts) == 3
        for r in receipts:
            assert r.status == "failed"
            assert r.file_count == 0
            assert r.total_bytes == 0
            assert r.doi is None
            assert r.commit_pinned_url is None
