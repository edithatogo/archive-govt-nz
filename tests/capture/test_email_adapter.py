"""Test suite for EmailCaptureAdapter."""

from __future__ import annotations

from pathlib import Path

import pytest

from archive_govt_nz.adapters.email import EmailCaptureAdapter
from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.object_store import ContentAddressedStore


@pytest.mark.anyio
async def test_email_capture_unchanged_on_poll(tmp_path: Path) -> None:
    """Validate polling email returns unchanged status."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = EmailCaptureAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.EMAIL,
        agency_slug="treasury",
        target="newsletter@treasury.govt.nz",
        source_id="email:treasury:newsletter@treasury.govt.nz",
        uri="email://treasury/newsletter@treasury.govt.nz",
    )
    result = await adapter.capture(identity)
    assert result.status == "unchanged"


@pytest.mark.anyio
async def test_email_capture_wrong_type(tmp_path: Path) -> None:
    """Validate non-email source rejection."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = EmailCaptureAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.WEB,
        agency_slug="treasury",
        target="treasury.govt.nz",
        source_id="web:treasury:treasury.govt.nz",
        uri="web://treasury/treasury.govt.nz",
    )
    result = await adapter.capture(identity)
    assert result.status == "failed"


def test_email_ingest_payload(tmp_path: Path) -> None:
    """Validate direct ingestion of raw email newsletter payload."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = EmailCaptureAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.EMAIL,
        agency_slug="treasury",
        target="newsletter@treasury.govt.nz",
        source_id="email:treasury:newsletter@treasury.govt.nz",
        uri="email://treasury/newsletter@treasury.govt.nz",
    )
    eml = "From: news@treasury.govt.nz\nSubject: Treasury Update\n\nRelease notes."
    result = adapter.ingest_email_payload(
        identity, eml, metadata={"subject": "Treasury Update"}
    )

    assert result.status == "success"
    assert result.bytes_captured > 0
    assert result.objects_created == 2  # raw eml + metadata JSON
    assert len(result.records) == 2


def test_email_ingest_wrong_type(tmp_path: Path) -> None:
    """Validate wrong source type for ingest."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = EmailCaptureAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.WEB,
        agency_slug="treasury",
        target="treasury.govt.nz",
        source_id="web:treasury:treasury.govt.nz",
        uri="web://treasury/treasury.govt.nz",
    )
    result = adapter.ingest_email_payload(identity, "content")
    assert result.status == "failed"
