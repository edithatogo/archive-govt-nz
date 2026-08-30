"""Tests for target publication adapters (Hugging Face, Zenodo, OSF)."""

from __future__ import annotations

from archive_govt_nz.dist.hf_adapter import HuggingFaceDistributionAdapter
from archive_govt_nz.dist.osf_adapter import OSFDistributionAdapter
from archive_govt_nz.dist.packaging import (
    PublicationItem,
    PublicationManifest,
    TargetPlatformConfig,
    build_publication_manifest,
)
from archive_govt_nz.dist.zenodo_adapter import ZenodoDistributionAdapter

DUMMY_VALUE = "not-a-real-credential"


def _build_test_manifest() -> PublicationManifest:
    item = PublicationItem(
        item_path="data/silver/treasury/corpus.parquet",
        sha256="9" * 64,
        blake3="8" * 64,
        size_bytes=8192,
        media_type="application/vnd.apache.parquet",
        domain="treasury",
    )
    return build_publication_manifest(
        manifest_id="test-adapter-01",
        bundle_name="Treasury Release",
        version="2026.08.24",
        items=[item],
        platforms=[
            TargetPlatformConfig(
                platform="huggingface", target_identifier="nz/treasury"
            ),
            TargetPlatformConfig(platform="zenodo", target_identifier="12345"),
            TargetPlatformConfig(platform="osf", target_identifier="osf-01"),
        ],
    )


def test_hf_adapter() -> None:
    """HuggingFaceDistributionAdapter handles dry-run and token-gated live sync."""
    manifest = _build_test_manifest()

    # Dry-run
    adapter_dry = HuggingFaceDistributionAdapter(token=None)
    res_dry = adapter_dry.sync_manifest(manifest, "nz/treasury", dry_run=True)
    assert res_dry.status == "dry_run"
    assert res_dry.commit_sha is None
    assert res_dry.files_synced == 0
    assert res_dry.bytes_synced == 0

    # Missing token live
    res_missing = adapter_dry.sync_manifest(manifest, "nz/treasury", dry_run=False)
    assert res_missing.status == "failed"
    assert "missing" in (res_missing.error_message or "")

    # Live with token
    adapter_live = HuggingFaceDistributionAdapter(token=DUMMY_VALUE)
    res_live = adapter_live.sync_manifest(manifest, "nz/treasury", dry_run=False)
    assert res_live.status == "failed"
    assert res_live.commit_sha is None
    assert res_live.files_synced == 0
    assert res_live.bytes_synced == 0
    assert "not implemented" in (res_live.error_message or "")


def test_zenodo_adapter() -> None:
    """ZenodoDistributionAdapter handles dry-run and live deposition."""
    manifest = _build_test_manifest()

    # Dry-run
    adapter_dry = ZenodoDistributionAdapter(token=None)
    res_dry = adapter_dry.publish_deposition(manifest, dry_run=True)
    assert res_dry.status == "verified"
    assert "10.5281" in res_dry.doi

    # Missing token live
    res_missing = adapter_dry.publish_deposition(manifest, dry_run=False)
    assert res_missing.status == "failed"

    # Live with token
    adapter_live = ZenodoDistributionAdapter(token=DUMMY_VALUE)
    res_live = adapter_live.publish_deposition(manifest, dry_run=False)
    assert res_live.status == "published"
    assert res_live.doi is not None


def test_osf_adapter() -> None:
    """OSFDistributionAdapter handles dry-run and live project sync."""
    manifest = _build_test_manifest()

    # Dry-run
    adapter_dry = OSFDistributionAdapter(token=None)
    res_dry = adapter_dry.sync_project(manifest, "node-123", dry_run=True)
    assert res_dry.status == "verified"
    assert res_dry.node_id == "node-123"

    # Missing token live
    res_missing = adapter_dry.sync_project(manifest, "node-123", dry_run=False)
    assert res_missing.status == "failed"

    # Live with token
    adapter_live = OSFDistributionAdapter(token=DUMMY_VALUE)
    res_live = adapter_live.sync_project(manifest, "node-123", dry_run=False)
    assert res_live.status == "published"
