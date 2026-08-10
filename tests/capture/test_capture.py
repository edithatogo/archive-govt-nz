"""Bounded streaming capture contracts."""

from pathlib import Path

import httpx
import pytest

from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
from archive_govt_nz.object_store import ContentAddressedStore


@pytest.mark.anyio
async def test_capture_streams_to_object_store(tmp_path: Path) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "text/csv"}, content=b"a,b\n1,2\n"
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await capture_url(
            client, "https://example.test/data", ContentAddressedStore(tmp_path)
        )
    assert result.receipt.byte_count == 8
    assert result.content_type == "text/csv"
    assert result.attempts == 1
    assert result.redirects == 0
    assert [item.outcome for item in result.attempt_receipts] == ["captured"]


@pytest.mark.anyio
async def test_capture_rejects_declared_oversize(tmp_path: Path) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-length": "99"}, content=b"small")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CaptureError) as raised:
            await capture_url(
                client,
                "https://example.test/data",
                ContentAddressedStore(tmp_path),
                CaptureConfig(max_bytes=10),
            )
    assert raised.value.error_class == "size_limit"


@pytest.mark.anyio
async def test_capture_follows_bounded_redirects_and_validates(tmp_path: Path) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/start":
            return httpx.Response(302, headers={"location": "/final"})
        return httpx.Response(200, headers={"etag": "v1"}, content=b"ok")

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        result = await capture_url(
            client,
            "https://example.test/start",
            ContentAddressedStore(tmp_path),
            CaptureConfig(expected_etag="v1"),
        )
    assert result.url.endswith("/final")
    assert result.redirects == 1
    assert [item.outcome for item in result.attempt_receipts] == [
        "redirect",
        "captured",
    ]


@pytest.mark.anyio
async def test_capture_rejects_partial_content_ranges(tmp_path: Path) -> None:
    """HTTP 206 responses are explicit unsupported range outcomes."""

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            206,
            headers={"content-length": "3"},
            content=b"abc",
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CaptureError) as raised:
            await capture_url(
                client,
                "https://example.test/range",
                ContentAddressedStore(tmp_path),
            )
    assert raised.value.error_class == "unsupported_range"
    assert raised.value.attempts[0].outcome == "unsupported_range"


@pytest.mark.anyio
async def test_capture_rejects_redirect_loop(tmp_path: Path) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "/loop"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CaptureError) as raised:
            await capture_url(
                client,
                "https://example.test/loop",
                ContentAddressedStore(tmp_path),
                CaptureConfig(max_redirects=1),
            )
    assert raised.value.error_class == "redirect_limit"
    assert raised.value.attempts[-1].outcome == "redirect_limit"


@pytest.mark.anyio
async def test_capture_error_receipt_redacts_transport_details(tmp_path: Path) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        detail = "private transport detail"
        raise httpx.ReadTimeout(detail, request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(CaptureError) as raised:
            await capture_url(
                client,
                "https://example.test/data?token=secret",
                ContentAddressedStore(tmp_path),
            )

    assert raised.value.error_class == "transport_retryable"
    assert "token=[REDACTED]" in raised.value.attempts[0].url
    assert "private transport detail" not in str(raised.value)
