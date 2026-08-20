"""Comprehensive test suite for NZLegislationApiClient."""

from __future__ import annotations

import httpx
import pytest

from archive_govt_nz.domains.legislation.api import (
    HTTP_NOT_MODIFIED,
    HTTP_OK,
    NZLegislationApiClient,
)


def test_api_client_headers_with_key() -> None:
    """Test headers with API key and conditional request."""
    client = NZLegislationApiClient(api_key="secret-123")
    headers = client._headers(
        etag='"etag-xyz"', last_modified="Mon, 18 Aug 2026 12:00:00 GMT"
    )
    assert headers["X-Api-Key"] == "secret-123"
    assert headers["If-None-Match"] == '"etag-xyz"'
    assert headers["If-Modified-Since"] == "Mon, 18 Aug 2026 12:00:00 GMT"


def test_api_client_pacing() -> None:
    """Test deterministic pacing invokes sleep_fn."""
    slept: list[float] = []
    curr_time = 100.0

    def mock_time() -> float:
        return curr_time

    def mock_sleep(d: float) -> None:
        slept.append(d)

    client = NZLegislationApiClient(
        min_interval_seconds=0.5, time_fn=mock_time, sleep_fn=mock_sleep
    )
    client._last_request_at = 99.8
    client._pace()
    assert len(slept) == 1
    assert abs(slept[0] - 0.3) < 1e-5


def test_api_client_get_document_raw_200() -> None:
    """Test successful 200 XML retrieval."""

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "application/xml"}, content=b"<act/>"
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = NZLegislationApiClient(client=http_client, sleep_fn=lambda _: None)

    status, content, headers = client.get_document_raw(
        "https://api.legislation.govt.nz/v0/act/1"
    )
    assert status == HTTP_OK
    assert content == b"<act/>"
    assert headers["content-type"] == "application/xml"


@pytest.mark.anyio
async def test_api_client_get_document_raw_async_200() -> None:
    """Test async successful 200 XML retrieval."""

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, headers={"content-type": "application/xml"}, content=b"<act/>"
        )

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    client = NZLegislationApiClient(async_client=async_client)

    status, content, headers = await client.get_document_raw_async(
        "https://api.legislation.govt.nz/v0/act/1"
    )
    assert status == HTTP_OK
    assert content == b"<act/>"
    assert headers["content-type"] == "application/xml"


@pytest.mark.anyio
async def test_api_client_get_document_raw_async_retries() -> None:
    """Test async 429 retry and 500 retry."""
    calls = 0

    def handler(_req: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "1"})
        if calls == 2:
            return httpx.Response(403, text="Rate limit burst exceeded")
        if calls == 3:
            return httpx.Response(500, text="Server error")
        return httpx.Response(200, content=b"<act/>")

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    client = NZLegislationApiClient(async_client=async_client, max_retries=4)

    status, content, _ = await client.get_document_raw_async(
        "https://api.legislation.govt.nz/v0/act/1"
    )
    assert status == HTTP_OK
    assert content == b"<act/>"
    assert calls == 4


def test_api_client_get_document_raw_304() -> None:
    """Test 304 Not Modified."""

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(304, headers={"ETag": '"abc"'})

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = NZLegislationApiClient(client=http_client, sleep_fn=lambda _: None)

    status, content, _ = client.get_document_raw(
        "https://api.legislation.govt.nz/v0/act/1", etag='"abc"'
    )
    assert status == HTTP_NOT_MODIFIED
    assert content == b""


def test_api_client_get_document_raw_403_burst_then_success() -> None:
    """Test 403 burst mitigation retry."""
    calls = 0

    def handler(_req: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(403, text="Rate limit burst limit exceeded")
        return httpx.Response(200, content=b"<act/>")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = NZLegislationApiClient(client=http_client, sleep_fn=lambda _: None)

    status, content, _ = client.get_document_raw(
        "https://api.legislation.govt.nz/v0/act/1"
    )
    assert status == HTTP_OK
    assert content == b"<act/>"
    assert calls == 2


def test_api_client_get_document_raw_429_with_retry_after() -> None:
    """Test 429 with Retry-After header."""
    calls = 0

    def handler(_req: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(429, headers={"Retry-After": "3"})
        return httpx.Response(200, content=b"<act/>")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = NZLegislationApiClient(client=http_client, sleep_fn=lambda _: None)

    status, content, _ = client.get_document_raw(
        "https://api.legislation.govt.nz/v0/act/1"
    )
    assert status == HTTP_OK
    assert content == b"<act/>"
    assert calls == 2


def test_api_client_get_document_raw_500_exhaustion() -> None:
    """Test 500 server error retry exhaustion."""

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="Internal Error")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = NZLegislationApiClient(
        client=http_client, max_retries=1, sleep_fn=lambda _: None
    )

    status, _, _ = client.get_document_raw("https://api.legislation.govt.nz/v0/act/1")
    assert status == 500


def test_api_client_get_document_raw_transport_error() -> None:
    """Test transport error retry and exhaustion."""
    calls = 0

    def handler(_req: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            msg = "Connection failed"
            raise httpx.ConnectError(msg)
        return httpx.Response(200, content=b"<act/>")

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = NZLegislationApiClient(client=http_client, sleep_fn=lambda _: None)

    status, content, _ = client.get_document_raw(
        "https://api.legislation.govt.nz/v0/act/1"
    )
    assert status == HTTP_OK
    assert content == b"<act/>"


def test_api_client_rate_limit_state() -> None:
    """Test rate limit remaining tracking."""

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={
                "X-RateLimit-Remaining": "15",
                "X-RateLimit-Reset": "1700000000",
            },
            content=b"<act/>",
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = NZLegislationApiClient(client=http_client, sleep_fn=lambda _: None)

    client.get_document_raw("https://api.legislation.govt.nz/v0/act/1")
    assert client.last_rate_limit_remaining == 15
    assert client.last_rate_limit_reset == 1700000000


def test_api_client_iter_search_works() -> None:
    """Test search pagination and traversal."""

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "results": [
                    {"work_id": "act-1", "title": "Act 1"},
                    {"work_id": "act-2", "title": "Act 2"},
                ]
            },
        )

    transport = httpx.MockTransport(handler)
    http_client = httpx.Client(transport=transport)
    client = NZLegislationApiClient(client=http_client, sleep_fn=lambda _: None)

    works = list(client.iter_search_works("Search", max_results=2))
    assert len(works) == 2
    assert works[0]["work_id"] == "act-1"


@pytest.mark.parametrize("status_code", [401, 403, 429, 500])
def test_api_client_search_http_failure_is_not_empty_state(status_code: int) -> None:
    """Authentication and transport failures cannot become empty discovery."""

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, json={"error": "bounded"})

    client = NZLegislationApiClient(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep_fn=lambda _: None,
    )
    with pytest.raises(OSError, match=f"HTTP {status_code}"):
        list(client.iter_search_works("act"))


@pytest.mark.parametrize(
    ("response", "error"),
    [
        (httpx.Response(200, content=b"not-json"), ValueError),
        (httpx.Response(200, json={"results": {"work_id": "act-1"}}), TypeError),
    ],
)
def test_api_client_search_malformed_success_fails_closed(
    response: httpx.Response, error: type[Exception]
) -> None:
    """Malformed HTTP 200 payloads are not evidence of an empty inventory."""

    def handler(_req: httpx.Request) -> httpx.Response:
        return response

    client = NZLegislationApiClient(
        client=httpx.Client(transport=httpx.MockTransport(handler)),
        sleep_fn=lambda _: None,
    )
    with pytest.raises(error):
        list(client.iter_search_works("act"))
