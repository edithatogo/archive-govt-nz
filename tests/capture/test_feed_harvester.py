"""Test suite for FeedCaptureAdapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.adapters.feeds import FeedCaptureAdapter
from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.anyio
async def test_feed_capture_success(tmp_path: Path) -> None:
    """Validate successful feed capture."""
    store = ContentAddressedStore(tmp_path / "cas")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/rss+xml"},
            content=b"<rss><channel><title>Health News</title></channel></rss>",
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = FeedCaptureAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.FEED,
            agency_slug="moh",
            target="https://health.govt.nz/news/feed",
            source_id="feed:moh:https://health.govt.nz/news/feed",
            uri="feed://moh/https://health.govt.nz/news/feed",
        )
        result = await adapter.capture(identity)

    assert result.status == "success"
    assert result.bytes_captured > 0
    assert len(result.records) == 1
    assert result.records[0].media_type == "application/rss+xml"


@pytest.mark.anyio
async def test_feed_capture_rate_limited(tmp_path: Path) -> None:
    """Validate rate limit 429 handling."""
    store = ContentAddressedStore(tmp_path / "cas")
    transport = httpx.MockTransport(lambda _req: httpx.Response(429))
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = FeedCaptureAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.FEED,
            agency_slug="moh",
            target="https://health.govt.nz/news/feed",
            source_id="feed:moh:https://health.govt.nz/news/feed",
            uri="feed://moh/https://health.govt.nz/news/feed",
        )
        result = await adapter.capture(identity)

    assert result.status == "rate_limited"


@pytest.mark.anyio
async def test_feed_capture_wrong_source_type(tmp_path: Path) -> None:
    """Validate graceful rejection of non-feed source types."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = FeedCaptureAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.X,
        agency_slug="moh",
        target="minhealthnz",
        source_id="x:moh:minhealthnz",
        uri="x://moh/minhealthnz",
    )
    result = await adapter.capture(identity)
    assert result.status == "failed"
