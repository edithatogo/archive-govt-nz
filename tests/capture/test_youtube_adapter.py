"""Test suite for YouTubeCaptureAdapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.adapters.youtube import YouTubeCaptureAdapter
from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.anyio
async def test_youtube_capture_success(tmp_path: Path) -> None:
    """Validate successful YouTube channel feed capture."""
    store = ContentAddressedStore(tmp_path / "cas")

    def handler(request: httpx.Request) -> httpx.Response:
        assert "channel_id=UC123456" in str(request.url)
        return httpx.Response(
            200,
            headers={"content-type": "application/xml"},
            content=b"<feed><title>NZ Parliament YouTube</title></feed>",
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = YouTubeCaptureAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.YOUTUBE,
            agency_slug="parliament",
            target="UC123456",
            source_id="youtube:parliament:UC123456",
            uri="youtube://parliament/UC123456",
        )
        result = await adapter.capture(identity)

    assert result.status == "success"
    assert result.bytes_captured > 0
    assert len(result.records) == 1
    assert result.records[0].media_type == "application/xml"


@pytest.mark.anyio
async def test_youtube_capture_rate_limited(tmp_path: Path) -> None:
    """Validate YouTube rate limit 429 response."""
    store = ContentAddressedStore(tmp_path / "cas")
    transport = httpx.MockTransport(lambda _req: httpx.Response(429))
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = YouTubeCaptureAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.YOUTUBE,
            agency_slug="parliament",
            target="UC123456",
            source_id="youtube:parliament:UC123456",
            uri="youtube://parliament/UC123456",
        )
        result = await adapter.capture(identity)

    assert result.status == "rate_limited"


@pytest.mark.anyio
async def test_youtube_wrong_type(tmp_path: Path) -> None:
    """Validate non-youtube source rejection."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = YouTubeCaptureAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.WEB,
        agency_slug="parliament",
        target="parliament.nz",
        source_id="web:parliament:parliament.nz",
        uri="web://parliament/parliament.nz",
    )
    result = await adapter.capture(identity)
    assert result.status == "failed"
