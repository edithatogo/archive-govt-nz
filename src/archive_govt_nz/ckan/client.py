"""Bounded asynchronous CKAN Action API transport."""

import hashlib
import json
import random
import re
from collections.abc import Awaitable, Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Self, cast

import anyio
import httpx

from archive_govt_nz.ckan.envelope import (
    ActionResponse,
    CkanError,
    CkanProtocolError,
    CkanTransportError,
    JsonObject,
    TransportFailureError,
    interpret_action_response,
)

type Clock = Callable[[], datetime]
type Jitter = Callable[[], float]
type Sleep = Callable[[float], Awaitable[None]]

_ACTION_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_FIELD_ACTION_NAME = "action_name"
_FIELD_BACKOFF = "base_backoff_seconds"
_FIELD_BASE_URL_SCHEME = "base_url_scheme"
_FIELD_JITTER = "jitter_seconds"
_FIELD_MAX_ATTEMPTS = "max_attempts"
_FIELD_MAX_RESPONSE = "max_response_bytes"
_FIELD_TIMEOUT = "timeout_seconds"
_FIELD_USER_AGENT = "user_agent"
_SAFE_RESPONSE_HEADERS = frozenset(
    {
        "content-type",
        "etag",
        "last-modified",
        "retry-after",
    }
)


class CkanResponseTooLargeError(CkanError):
    """A response exceeded its configured in-memory metadata bound."""

    def __init__(self, limit_bytes: int) -> None:
        """Create a bounded diagnostic without retaining response content."""
        self.limit_bytes = limit_bytes
        super().__init__("response_too_large", retryable=False)


class CkanClientConfigurationError(ValueError):
    """A required client safety bound is absent or invalid."""

    def __init__(self, field: str) -> None:
        """Identify the invalid field without retaining its value."""
        self.field = field
        super().__init__(field)


def _configuration_error(field: str) -> CkanClientConfigurationError:
    """Build a value-redacted configuration error."""
    return CkanClientConfigurationError(field)


@dataclass(frozen=True, slots=True)
class CkanClientConfig:
    """Explicit resource and retry bounds for one CKAN catalogue."""

    base_url: str
    user_agent: str
    timeout_seconds: float
    max_attempts: int
    base_backoff_seconds: float
    jitter_seconds: float
    max_response_bytes: int

    def __post_init__(self) -> None:
        """Reject configurations that could remove a safety bound."""
        if not self.base_url.startswith(("https://", "http://")):
            raise _configuration_error(_FIELD_BASE_URL_SCHEME)
        if not self.user_agent.strip():
            raise _configuration_error(_FIELD_USER_AGENT)
        if self.timeout_seconds <= 0:
            raise _configuration_error(_FIELD_TIMEOUT)
        if self.max_attempts < 1:
            raise _configuration_error(_FIELD_MAX_ATTEMPTS)
        if self.base_backoff_seconds < 0:
            raise _configuration_error(_FIELD_BACKOFF)
        if self.jitter_seconds < 0:
            raise _configuration_error(_FIELD_JITTER)
        if self.max_response_bytes < 1:
            raise _configuration_error(_FIELD_MAX_RESPONSE)


@dataclass(frozen=True, slots=True)
class TransportAttempt:
    """Safe evidence for one bounded HTTP attempt."""

    attempt: int
    status_code: int | None
    error_class: str | None
    observed_at: datetime


@dataclass(frozen=True, slots=True)
class ActionObservation:
    """A validated Action result with its exact received bytes and receipts."""

    response: ActionResponse
    raw_body: bytes
    raw_sha256: str
    observed_at: datetime
    attempts: tuple[TransportAttempt, ...]
    response_headers: Mapping[str, str]

    @property
    def attempt_count(self) -> int:
        """Return the exact number of attempts represented by the receipt."""
        return len(self.attempts)


@dataclass(frozen=True, slots=True)
class CapabilityObservation:
    """Stable catalogue identity and deployed CKAN capability evidence."""

    catalogue_url: str
    action_api_version: str
    ckan_version: str
    site_url: str
    observed_at: datetime
    raw_sha256: str


def _utc_now() -> datetime:
    """Return an aware UTC observation timestamp."""
    return datetime.now(tz=UTC)


def _random_unit_interval() -> float:
    """Return nondeterministic jitter isolated behind an injectable boundary."""
    return random.SystemRandom().random()


class BoundedCkanClient:
    """Async CKAN client with bounded attempts, time, and response bytes."""

    def __init__(
        self,
        config: CkanClientConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
        sleep: Sleep | None = None,
        clock: Clock = _utc_now,
        jitter: Jitter = _random_unit_interval,
    ) -> None:
        """Create a client without performing network activity."""
        self._config = config
        self._sleep = sleep or anyio.sleep
        self._clock = clock
        self._jitter = jitter
        self._client = httpx.AsyncClient(
            base_url=config.base_url.rstrip("/"),
            headers={
                "Accept": "application/json",
                "Accept-Encoding": "identity",
                "User-Agent": config.user_agent,
            },
            timeout=httpx.Timeout(config.timeout_seconds),
            follow_redirects=False,
            transport=transport,
        )

    async def __aenter__(self) -> Self:
        """Enter the client context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: object,
    ) -> None:
        """Close transport resources regardless of request outcome."""
        del exc_type, exc_value, traceback
        await self._client.aclose()

    async def action(
        self,
        action: str,
        params: Mapping[str, object] | None = None,
    ) -> ActionObservation:
        """Call one versioned CKAN Action endpoint under explicit bounds."""
        if _ACTION_NAME.fullmatch(action) is None:
            raise _configuration_error(_FIELD_ACTION_NAME)

        attempts: list[TransportAttempt] = []
        attempt_number = 0
        while True:
            attempt_number += 1
            observed_at = self._clock()
            try:
                status_code, raw_body, response_headers = await self._request(
                    action,
                    params,
                )
                document = self._decode_document(raw_body)
                response = interpret_action_response(status_code, document)
            except CkanTransportError as error:
                attempts.append(
                    TransportAttempt(
                        attempt=attempt_number,
                        status_code=error.status_code,
                        error_class=error.error_class,
                        observed_at=observed_at,
                    )
                )
                if not error.retryable or not self._has_retry(attempt_number):
                    raise
                await self._backoff(attempt_number)
                continue
            except httpx.HTTPError as error:
                classified = self._classify_httpx_failure(error)
                attempts.append(
                    TransportAttempt(
                        attempt=attempt_number,
                        status_code=None,
                        error_class=classified.error_class,
                        observed_at=observed_at,
                    )
                )
                if not classified.retryable or not self._has_retry(attempt_number):
                    raise classified from None
                await self._backoff(attempt_number)
                continue

            attempts.append(
                TransportAttempt(
                    attempt=attempt_number,
                    status_code=status_code,
                    error_class=None,
                    observed_at=observed_at,
                )
            )
            return ActionObservation(
                response=response,
                raw_body=raw_body,
                raw_sha256=hashlib.sha256(raw_body).hexdigest(),
                observed_at=observed_at,
                attempts=tuple(attempts),
                response_headers=response_headers,
            )

    async def observe_capability(self) -> CapabilityObservation:
        """Observe catalogue identity through CKAN's status Action."""
        observation = await self.action("status_show")
        ckan_version = observation.response.result.get("ckan_version")
        site_url = observation.response.result.get("site_url")
        if not isinstance(ckan_version, str) or not isinstance(site_url, str):
            raise CkanProtocolError
        return CapabilityObservation(
            catalogue_url=self._config.base_url.rstrip("/"),
            action_api_version="3",
            ckan_version=ckan_version,
            site_url=site_url,
            observed_at=observation.observed_at,
            raw_sha256=observation.raw_sha256,
        )

    async def _request(
        self,
        action: str,
        params: Mapping[str, object] | None,
    ) -> tuple[int, bytes, Mapping[str, str]]:
        request = self._client.build_request(
            "POST",
            f"/api/3/action/{action}",
            json=dict(params or {}),
        )
        response = await self._client.send(request, stream=True)
        try:
            self._reject_large_content_length(response.headers)
            raw_body = await self._read_bounded(response)
            safe_headers = {
                name.lower(): value
                for name, value in response.headers.items()
                if name.lower() in _SAFE_RESPONSE_HEADERS
            }
            return response.status_code, raw_body, safe_headers
        finally:
            await response.aclose()

    def _reject_large_content_length(self, headers: httpx.Headers) -> None:
        value = headers.get("content-length")
        if value is None:
            return
        try:
            content_length = int(value)
        except ValueError:
            return
        if content_length > self._config.max_response_bytes:
            raise CkanResponseTooLargeError(self._config.max_response_bytes)

    async def _read_bounded(self, response: httpx.Response) -> bytes:
        if response.is_stream_consumed:
            raw_body = response.content
            if len(raw_body) > self._config.max_response_bytes:
                raise CkanResponseTooLargeError(self._config.max_response_bytes)
            return raw_body

        chunks: list[bytes] = []
        received = 0
        async for chunk in response.aiter_raw():
            received += len(chunk)
            if received > self._config.max_response_bytes:
                raise CkanResponseTooLargeError(self._config.max_response_bytes)
            chunks.append(chunk)
        return b"".join(chunks)

    @staticmethod
    def _decode_document(raw_body: bytes) -> JsonObject:
        try:
            document = json.loads(raw_body)
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise CkanProtocolError from None
        if not isinstance(document, dict):
            raise CkanProtocolError
        return cast("JsonObject", document)

    @staticmethod
    def _classify_httpx_failure(error: httpx.HTTPError) -> TransportFailureError:
        if isinstance(error, httpx.TimeoutException):
            return TransportFailureError("timeout", retryable=True)
        if isinstance(error, httpx.NetworkError):
            return TransportFailureError("network_error", retryable=True)
        return TransportFailureError("transport_failure", retryable=False)

    def _has_retry(self, attempt_number: int) -> bool:
        return attempt_number < self._config.max_attempts

    async def _backoff(self, attempt_number: int) -> None:
        exponential = self._config.base_backoff_seconds * 2 ** (attempt_number - 1)
        jitter = self._config.jitter_seconds * self._jitter()
        await self._sleep(exponential + jitter)
