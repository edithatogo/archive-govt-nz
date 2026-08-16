"""Test suite for BlueskyCaptureAdapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.adapters.bluesky import BlueskyCaptureAdapter
from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.anyio
async def test_bluesky_capture_success(tmp_path: Path) -> None:
    """Validate successful Bluesky author feed capture."""
    store = ContentAddressedStore(tmp_path / "cas")

    def handler(request: httpx.Request) -> httpx.Response:
        assert "actor=minhealthnz.bsky.social" in str(request.url)
        return httpx.Response(
            200,
            headers={"content-type": "application/json"},
            content=b'{"feed": [{"post": {"uri": "at://did:plc:123/app.bsky.feed.post/456"}}]}',
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = BlueskyCaptureAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.BLUESKY,
            agency_slug="moh",
            target="minhealthnz.bsky.social",
            source_id="bluesky:moh:minhealthnz.bsky.social",
            uri="bluesky://moh/minhealthnz.bsky.social",
        )
        result = await adapter.capture(identity)

    assert result.status == "success"
    assert result.bytes_captured > 0
    assert len(result.records) == 1
    assert result.records[0].media_type == "application/json"


@pytest.mark.anyio
async def test_bluesky_capture_rate_limited(tmp_path: Path) -> None:
    """Validate Bluesky rate limit 429 response."""
    store = ContentAddressedStore(tmp_path / "cas")
    transport = httpx.MockTransport(lambda _req: httpx.Response(429))
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = BlueskyCaptureAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.BLUESKY,
            agency_slug="moh",
            target="minhealthnz.bsky.social",
            source_id="bluesky:moh:minhealthnz.bsky.social",
            uri="bluesky://moh/minhealthnz.bsky.social",
        )
        result = await adapter.capture(identity)

    assert result.status == "rate_limited"


@pytest.mark.anyio
async def test_bluesky_wrong_type(tmp_path: Path) -> None:
    """Validate non-bluesky source rejection."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = BlueskyCaptureAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.WEB,
        agency_slug="moh",
        target="health.govt.nz",
        source_id="web:moh:health.govt.nz",
        uri="web://moh/health.govt.nz",
    )
    result = await adapter.capture(identity)
    assert result.status == "failed"
