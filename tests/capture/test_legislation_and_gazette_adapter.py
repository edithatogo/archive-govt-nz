"""Test suite for NZLegislationAdapter and NZGazetteAdapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.adapters.nz_gazette import NZGazetteAdapter
from archive_govt_nz.adapters.nz_legislation import NZLegislationAdapter
from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.anyio
async def test_legislation_capture_success(tmp_path: Path) -> None:
    """Validate successful legislation document capture."""
    store = ContentAddressedStore(tmp_path / "cas")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/xml"},
            content=(
                b"<act><heading>Test Act 2026</heading>"
                b"<section id='s1'><heading>S1</heading>Text</section></act>"
            ),
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = NZLegislationAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.LEGISLATION,
            agency_slug="pco",
            target="https://www.legislation.govt.nz/act/public/2026/0001/latest/whole.xml",
            source_id="act-2026-1",
            uri="legislation://pco/act-2026-1",
        )
        result = await adapter.capture(identity)

    assert result.status == "success"
    assert result.bytes_captured > 0
    assert len(result.records) == 1
    assert result.records[0].record_id.startswith("rec:")
    assert result.records[0].media_type == "text/xml"


@pytest.mark.anyio
async def test_legislation_capture_rate_limited(tmp_path: Path) -> None:
    """Validate legislation rate limiting."""
    store = ContentAddressedStore(tmp_path / "cas")
    transport = httpx.MockTransport(lambda _req: httpx.Response(429))
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = NZLegislationAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.LEGISLATION,
            agency_slug="pco",
            target="https://www.legislation.govt.nz/act/public/2026/0001/latest/whole.xml",
            source_id="act-2026-1",
            uri="legislation://pco/act-2026-1",
        )
        result = await adapter.capture(identity)

    assert result.status == "rate_limited"


@pytest.mark.anyio
async def test_legislation_capture_wrong_type(tmp_path: Path) -> None:
    """Validate wrong source type handling."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = NZLegislationAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.FEED,
        agency_slug="pco",
        target="https://example.com/feed",
        source_id="feed-1",
        uri="feed://pco/feed-1",
    )
    result = await adapter.capture(identity)
    assert result.status == "failed"


@pytest.mark.anyio
async def test_gazette_capture_success(tmp_path: Path) -> None:
    """Validate successful gazette notice capture."""
    store = ContentAddressedStore(tmp_path / "cas")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=(
                b"<html><body><h1>Gazette Notice 2026-001</h1>"
                b"<p>Content</p></body></html>"
            ),
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = NZGazetteAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.GAZETTE,
            agency_slug="dia",
            target="https://gazette.govt.nz/notice/id/2026-001",
            source_id="notice-2026-001",
            uri="gazette://dia/notice-2026-001",
        )
        result = await adapter.capture(identity)

    assert result.status == "success"
    assert result.bytes_captured > 0
    assert len(result.records) == 1
    assert result.records[0].record_id.startswith("rec:")
    assert result.records[0].media_type == "text/html"
