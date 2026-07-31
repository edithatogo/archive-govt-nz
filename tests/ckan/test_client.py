"""Bounded asynchronous CKAN HTTP-client contracts."""

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

import httpx
import pytest
from archive_govt_nz.ckan.client import (
    ActionObservation,
    BoundedCkanClient,
    CapabilityObservation,
    CkanClientConfig,
    CkanResponseTooLargeError,
)

from archive_govt_nz.ckan.envelope import CkanTransportError

Sleep = Callable[[float], Awaitable[None]]
OBSERVED_AT = datetime(2026, 7, 31, 4, 30, tzinfo=UTC)


def make_config(*, max_response_bytes: int = 4096) -> CkanClientConfig:
    """Create a deterministic bounded client configuration."""
    return CkanClientConfig(
        base_url="https://catalogue.data.govt.nz",
        user_agent=(
            "archive-govt-nz/0.1.0 "
            "(+https://github.com/edithatogo/archive-govt-nz)"
        ),
        timeout_seconds=7.0,
        max_attempts=3,
        base_backoff_seconds=0.5,
        jitter_seconds=0.0,
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
    assert len(observation.raw_sha256) == 64
