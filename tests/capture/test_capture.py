"""Bounded streaming capture contracts."""

from pathlib import Path

import httpx
import pytest

from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
from archive_govt_nz.object_store import ContentAddressedStore


@pytest.mark.anyio
async def test_capture_streams_to_object_store(tmp_path: Path) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "text/csv"}, content=b"a,b\n1,2\n")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await capture_url(client, "https://example.test/data", ContentAddressedStore(tmp_path))
    assert result.receipt.byte_count == 8
    assert result.content_type == "text/csv"


@pytest.mark.anyio
async def test_capture_rejects_declared_oversize(tmp_path: Path) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-length": "99"}, content=b"small")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CaptureError) as raised:
            await capture_url(client, "https://example.test/data", ContentAddressedStore(tmp_path), CaptureConfig(max_bytes=10))
    assert raised.value.error_class == "size_limit"
