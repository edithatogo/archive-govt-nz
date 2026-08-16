"""Test suite for XCaptureAdapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.adapters.x_twitter import XCaptureAdapter
from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.anyio
async def test_x_capture_success(tmp_path: Path) -> None:
    """Validate successful X profile capture."""
    store = ContentAddressedStore(tmp_path / "cas")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html><body>X Timeline</body></html>",
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = XCaptureAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.X,
            agency_slug="treasury",
            target="nztreasury",
            source_id="x:treasury:nztreasury",
            uri="x://treasury/nztreasury",
        )
        result = await adapter.capture(identity)

    assert result.status == "success"
    assert result.bytes_captured > 0
    assert len(result.records) == 1


@pytest.mark.anyio
async def test_x_capture_rate_limited(tmp_path: Path) -> None:
    """Validate X rate limit 429 response."""
    store = ContentAddressedStore(tmp_path / "cas")
    transport = httpx.MockTransport(lambda _req: httpx.Response(429))
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = XCaptureAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.X,
            agency_slug="treasury",
            target="nztreasury",
            source_id="x:treasury:nztreasury",
            uri="x://treasury/nztreasury",
        )
        result = await adapter.capture(identity)

    assert result.status == "rate_limited"


@pytest.mark.anyio
async def test_x_wrong_type(tmp_path: Path) -> None:
    """Validate non-x source rejection."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = XCaptureAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.WEB,
        agency_slug="treasury",
        target="treasury.govt.nz",
        source_id="web:treasury:treasury.govt.nz",
        uri="web://treasury/treasury.govt.nz",
    )
    result = await adapter.capture(identity)
    assert result.status == "failed"
