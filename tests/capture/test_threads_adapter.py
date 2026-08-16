"""Test suite for ThreadsCaptureAdapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.adapters.threads import ThreadsCaptureAdapter
from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.anyio
async def test_threads_capture_success(tmp_path: Path) -> None:
    """Validate successful Threads profile capture."""
    store = ContentAddressedStore(tmp_path / "cas")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html><body>Threads Profile</body></html>",
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = ThreadsCaptureAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.THREADS,
            agency_slug="moh",
            target="minhealthnz",
            source_id="threads:moh:minhealthnz",
            uri="threads://moh/minhealthnz",
        )
        result = await adapter.capture(identity)

    assert result.status == "success"
    assert result.bytes_captured > 0
    assert len(result.records) == 1


@pytest.mark.anyio
async def test_threads_capture_rate_limited(tmp_path: Path) -> None:
    """Validate Threads rate limit 429 response."""
    store = ContentAddressedStore(tmp_path / "cas")
    transport = httpx.MockTransport(lambda _req: httpx.Response(429))
    async with httpx.AsyncClient(transport=transport) as client:
        adapter = ThreadsCaptureAdapter(store, client=client)
        identity = SourceIdentity(
            source_type=SourceType.THREADS,
            agency_slug="moh",
            target="minhealthnz",
            source_id="threads:moh:minhealthnz",
            uri="threads://moh/minhealthnz",
        )
        result = await adapter.capture(identity)

    assert result.status == "rate_limited"


@pytest.mark.anyio
async def test_threads_wrong_type(tmp_path: Path) -> None:
    """Validate non-threads source rejection."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = ThreadsCaptureAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.WEB,
        agency_slug="moh",
        target="health.govt.nz",
        source_id="web:moh:health.govt.nz",
        uri="web://moh/health.govt.nz",
    )
    result = await adapter.capture(identity)
    assert result.status == "failed"
