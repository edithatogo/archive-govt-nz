"""Bounded asynchronous CKAN HTTP-client contracts."""

import asyncio
import hashlib
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import UTC, datetime

import httpx
import pytest

from archive_govt_nz.ckan.client import (
    ActionObservation,
    BoundedCkanClient,
    CapabilityObservation,
    CkanClientConfig,
    CkanClientConfigurationError,
    CkanResponseTooLargeError,
)
from archive_govt_nz.ckan.envelope import (
    CkanProtocolError,
    CkanTransportError,
    TransportFailureError,
)

Sleep = Callable[[float], Awaitable[None]]
OBSERVED_AT = datetime(2026, 7, 31, 4, 30, tzinfo=UTC)


def make_config(  # noqa: PLR0913
    *,
    base_url: str = "https://catalogue.data.govt.nz",
    user_agent: str = (
        "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"
    ),
    timeout_seconds: float = 7.0,
    max_attempts: int = 3,
    base_backoff_seconds: float = 0.5,
    jitter_seconds: float = 0.0,
    max_response_bytes: int = 4096,
) -> CkanClientConfig:
    """Create a deterministic bounded client configuration."""
    return CkanClientConfig(
        base_url=base_url,
        user_agent=user_agent,
        timeout_seconds=timeout_seconds,
        max_attempts=max_attempts,
        base_backoff_seconds=base_backoff_seconds,
        jitter_seconds=jitter_seconds,
        max_response_bytes=max_response_bytes,
    )


def run_action(
    handler: httpx.AsyncBaseTransport,
    *,
    config: CkanClientConfig | None = None,
    sleep: Sleep | None = None,
) -> ActionObservation:
    """Run one deterministic status action."""

    async def execute() -> ActionObservation:
        async with BoundedCkanClient(
            config or make_config(),
            transport=handler,
            sleep=sleep,
            clock=lambda: OBSERVED_AT,
            jitter=lambda: 0.0,
        ) as client:
            return await client.action("status_show")

    return asyncio.run(execute())


def test_action_uses_versioned_path_identifiable_agent_and_json_body() -> None:
    """Requests identify the archive and target the CKAN Action API v3."""
    observed: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        observed.append(request)
        return httpx.Response(
            200,
            json={"success": True, "result": {"ckan_version": "2.10.9"}},
        )

    result = run_action(httpx.MockTransport(handler))

    assert result.response.result["ckan_version"] == "2.10.9"
    assert observed[0].url == (
        "https://catalogue.data.govt.nz/api/3/action/status_show"
    )
    assert observed[0].headers["user-agent"].startswith("archive-govt-nz/")
    assert json.loads(observed[0].content) == {}


def test_retryable_statuses_use_bounded_exponential_backoff() -> None:
    """Only the configured attempts run and delays are deterministic and bounded."""
    statuses = iter([503, 503, 200])
    delays: list[float] = []

    async def handler(_: httpx.Request) -> httpx.Response:
        status = next(statuses)
        document = (
            {"success": True, "result": {"ckan_version": "2.10.9"}}
            if status == 200
            else {"success": False, "error": {"__type": "Service Error"}}
        )
        return httpx.Response(status, json=document)

    async def sleep(delay: float) -> None:
        delays.append(delay)

    result = run_action(httpx.MockTransport(handler), sleep=sleep)

    assert delays == [0.5, 1.0]
    assert [attempt.status_code for attempt in result.attempts] == [503, 503, 200]
    assert result.attempt_count == 3


def test_retry_budget_raises_last_classified_failure() -> None:
    """Exhaustion cannot loop indefinitely or convert failure into partial success."""
    requests = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(
            503,
            json={"success": False, "error": {"__type": "Service Error"}},
        )

    with pytest.raises(CkanTransportError) as raised:
        run_action(httpx.MockTransport(handler), sleep=_no_sleep)

    assert raised.value.retryable is True
    assert requests == 3


async def _no_sleep(_: float) -> None:
    """Skip elapsed time in deterministic retry tests."""


def test_configuration_rejects_every_removed_safety_bound() -> None:
    """Every resource control fails closed with only its field identifier."""
    invalid_factories = (
        lambda: make_config(base_url="file:///private"),
        lambda: make_config(user_agent=" "),
        lambda: make_config(timeout_seconds=0),
        lambda: make_config(max_attempts=0),
        lambda: make_config(base_backoff_seconds=-1),
        lambda: make_config(jitter_seconds=-1),
        lambda: make_config(max_response_bytes=0),
    )

    observed_fields: list[str] = []
    for factory in invalid_factories:
        with pytest.raises(CkanClientConfigurationError) as raised:
            factory()
        observed_fields.append(raised.value.field)

    assert observed_fields == [
        "base_url_scheme",
        "user_agent",
        "timeout_seconds",
        "max_attempts",
        "base_backoff_seconds",
        "jitter_seconds",
        "max_response_bytes",
    ]


def test_invalid_action_name_cannot_escape_the_versioned_path() -> None:
    """Action names are identifiers, never caller-controlled URL paths."""

    async def execute() -> None:
        async with BoundedCkanClient(
            make_config(),
            transport=httpx.MockTransport(lambda _: httpx.Response(200)),
        ) as client:
            await client.action("../private")

    with pytest.raises(CkanClientConfigurationError) as raised:
        asyncio.run(execute())

    assert raised.value.field == "action_name"


def test_timeout_retries_without_recording_private_exception_text() -> None:
    """Timeout attempts carry a bounded class and no source exception detail."""
    attempts = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            private_detail = "private network path"
            raise httpx.ReadTimeout(private_detail, request=request)
        return httpx.Response(
            200,
            json={"success": True, "result": {"ckan_version": "2.10.9"}},
        )

    result = run_action(httpx.MockTransport(handler), sleep=_no_sleep)

    assert result.attempts[0].error_class == "timeout"
    assert "private network path" not in repr(result.attempts)


def test_network_failure_retries_but_unknown_http_failure_is_terminal() -> None:
    """Only explicitly classified pre-response failures receive retry budget."""
    requests = 0

    async def network_then_success(request: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        if requests == 1:
            detail = "private network path"
            raise httpx.ConnectError(detail, request=request)
        return httpx.Response(200, json={"success": True, "result": {}})

    result = run_action(httpx.MockTransport(network_then_success), sleep=_no_sleep)
    assert result.attempts[0].error_class == "network_error"

    async def unknown(request: httpx.Request) -> httpx.Response:
        detail = "private decoder detail"
        raise httpx.DecodingError(detail, request=request)

    with pytest.raises(TransportFailureError) as raised:
        run_action(httpx.MockTransport(unknown), sleep=_no_sleep)

    assert raised.value.error_class == "transport_failure"
    assert raised.value.retryable is False
    assert "private decoder detail" not in str(raised.value)


def test_terminal_http_status_is_not_retried() -> None:
    """A terminal status consumes exactly one source request."""
    requests = 0

    async def handler(_: httpx.Request) -> httpx.Response:
        nonlocal requests
        requests += 1
        return httpx.Response(
            404,
            json={"success": False, "error": {"__type": "Not Found"}},
        )

    with pytest.raises(CkanTransportError) as raised:
        run_action(httpx.MockTransport(handler), sleep=_no_sleep)

    assert raised.value.retryable is False
    assert requests == 1


def test_raw_response_hash_and_redacted_transport_receipt_are_preserved() -> None:
    """The exact body is retained with safe, deterministic transport metadata."""
    body = b'{"success":true,"result":{"ckan_version":"2.10.9"}}'

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=body,
            headers={
                "Content-Type": "application/json",
                "ETag": '"stable-etag"',
                "Set-Cookie": "private-cookie",
            },
        )

    result = run_action(httpx.MockTransport(handler))

    assert result.raw_body == body
    assert result.raw_sha256 == hashlib.sha256(body).hexdigest()
    assert result.observed_at == OBSERVED_AT
    assert result.response_headers == {
        "content-type": "application/json",
        "etag": '"stable-etag"',
    }
    assert "private-cookie" not in repr(result)


def test_response_limit_fails_before_accepting_oversized_body() -> None:
    """A response larger than the configured bound is never interpreted."""

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"success": True, "result": {"value": "x" * 256}},
        )

    with pytest.raises(CkanResponseTooLargeError) as raised:
        run_action(
            httpx.MockTransport(handler),
            config=make_config(max_response_bytes=64),
        )

    assert raised.value.limit_bytes == 64


class ChunkStream(httpx.AsyncByteStream):
    """Deterministic unbuffered response stream."""

    def __init__(self, *chunks: bytes) -> None:
        """Retain bounded fixture chunks."""
        self._chunks = chunks

    async def __aiter__(self) -> AsyncIterator[bytes]:
        """Yield fixture chunks without pre-buffering."""
        for chunk in self._chunks:
            yield chunk


def test_unbuffered_streams_are_read_incrementally_and_bounded() -> None:
    """The live transport path accepts bounded chunks and rejects excess."""
    body = b'{"success":true,"result":{}}'

    async def bounded(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=ChunkStream(body[:10], body[10:]))

    assert run_action(httpx.MockTransport(bounded)).raw_body == body

    async def oversized(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=ChunkStream(b"x" * 40, b"y" * 40))

    with pytest.raises(CkanResponseTooLargeError):
        run_action(
            httpx.MockTransport(oversized),
            config=make_config(max_response_bytes=64),
        )


def test_invalid_content_length_defers_to_stream_limit() -> None:
    """Malformed length metadata cannot bypass the incremental byte bound."""
    body = b'{"success":true,"result":{}}'

    async def invalid_length(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"Content-Length": "unknown"},
            stream=ChunkStream(body),
        )

    assert run_action(httpx.MockTransport(invalid_length)).raw_body == body

    async def invalid_buffered_length(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            content=b"x" * 80,
            headers={"Content-Length": "unknown"},
        )

    with pytest.raises(CkanResponseTooLargeError):
        run_action(
            httpx.MockTransport(invalid_buffered_length),
            config=make_config(max_response_bytes=64),
        )


@pytest.mark.parametrize("body", [b"not-json", b"[]"])
def test_malformed_raw_documents_fail_as_protocol_errors(body: bytes) -> None:
    """Invalid JSON and non-object JSON cannot become Action evidence."""

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=body)

    with pytest.raises(CkanProtocolError):
        run_action(httpx.MockTransport(handler))


def test_status_observation_records_capability_and_catalogue_identity() -> None:
    """Status observations provide stable capability evidence."""

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "success": True,
                "result": {
                    "ckan_version": "2.10.9",
                    "site_url": "https://catalogue.data.govt.nz",
                },
            },
        )

    async def execute() -> CapabilityObservation:
        async with BoundedCkanClient(
            make_config(),
            transport=httpx.MockTransport(handler),
            clock=lambda: OBSERVED_AT,
            jitter=lambda: 0.0,
        ) as client:
            return await client.observe_capability()

    observation = asyncio.run(execute())

    assert observation.catalogue_url == "https://catalogue.data.govt.nz"
    assert observation.action_api_version == "3"
    assert observation.ckan_version == "2.10.9"
    assert observation.site_url == "https://catalogue.data.govt.nz"
    assert observation.observed_at == OBSERVED_AT
    assert observation.raw_body.startswith(b'{"success"')
    assert len(observation.raw_sha256) == 64
    assert observation.attempts[0].status_code == 200
    assert observation.response_headers["content-type"].startswith("application/json")


@pytest.mark.parametrize(
    "result",
    [
        {"site_url": "https://catalogue.data.govt.nz"},
        {"ckan_version": "2.10.9"},
    ],
)
def test_capability_requires_both_string_identity_fields(
    result: dict[str, object],
) -> None:
    """Incomplete status results cannot be recorded as capability evidence."""

    async def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": True, "result": result})

    async def execute() -> CapabilityObservation:
        async with BoundedCkanClient(
            make_config(),
            transport=httpx.MockTransport(handler),
        ) as client:
            return await client.observe_capability()

    with pytest.raises(CkanProtocolError):
        asyncio.run(execute())


def test_default_clock_sleep_and_jitter_dependencies_are_operational() -> None:
    """Production defaults run a zero-delay retry and emit aware UTC evidence."""
    statuses = iter([503, 200])

    async def handler(_: httpx.Request) -> httpx.Response:
        status = next(statuses)
        document: dict[str, object] = (
            {"success": True, "result": {}}
            if status == 200
            else {"success": False, "error": {"__type": "Service Error"}}
        )
        return httpx.Response(status, json=document)

    async def execute() -> ActionObservation:
        async with BoundedCkanClient(
            make_config(
                max_attempts=2,
                base_backoff_seconds=0,
                jitter_seconds=0,
            ),
            transport=httpx.MockTransport(handler),
        ) as client:
            return await client.action("status_show")

    result = asyncio.run(execute())

    assert result.observed_at.tzinfo is UTC
