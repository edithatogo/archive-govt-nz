"""Bounded streaming retrieval into the immutable object store."""

from __future__ import annotations

from collections.abc import AsyncIterable
from dataclasses import dataclass
from time import monotonic
from urllib.parse import urljoin

import httpx

from archive_govt_nz.ckan.redaction import redact_url
from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreReceipt


class CaptureError(RuntimeError):
    """Fail-closed capture outcome with a stable class."""

    def __init__(
        self, error_class: str, attempts: tuple[CaptureAttempt, ...] = ()
    ) -> None:
        self.error_class = error_class
        self.attempts = attempts
        super().__init__(error_class)


@dataclass(frozen=True, slots=True)
class CaptureConfig:
    """Transfer bounds applied before and during a response stream."""

    max_bytes: int = 512 * 1024 * 1024
    chunk_bytes: int = 1024 * 1024
    timeout_seconds: float = 60.0
    max_duration_seconds: float | None = None
    max_redirects: int = 3
    expected_etag: str | None = None
    expected_last_modified: str | None = None

    def __post_init__(self) -> None:
        if (
            self.max_bytes < 1
            or self.chunk_bytes < 1
            or self.timeout_seconds <= 0
            or self.max_redirects < 0
            or (
                self.max_duration_seconds is not None and self.max_duration_seconds <= 0
            )
        ):
            raise ValueError("invalid_capture_bound")


@dataclass(frozen=True, slots=True)
class CaptureAttempt:
    """Redacted deterministic receipt for one bounded HTTP attempt."""

    url: str
    status_code: int | None
    outcome: str
    elapsed_seconds: float


@dataclass(frozen=True, slots=True)
class CaptureResult:
    """Bounded response evidence and the promoted immutable object."""

    url: str
    status_code: int
    content_type: str | None
    receipt: ObjectStoreReceipt
    attempts: int = 1
    redirects: int = 0
    elapsed_seconds: float = 0.0
    attempt_receipts: tuple[CaptureAttempt, ...] = ()


async def capture_url(  # noqa: PLR0915
    client: httpx.AsyncClient,
    url: str,
    store: ContentAddressedStore,
    config: CaptureConfig = CaptureConfig(),
) -> CaptureResult:
    """Stream one URL, enforcing status, length, and byte limits."""
    current_url = url
    started = monotonic()
    attempt_receipts: list[CaptureAttempt] = []
    max_duration = config.max_duration_seconds or config.timeout_seconds
    for redirect_count in range(config.max_redirects + 1):
        if monotonic() - started >= max_duration:
            raise CaptureError("timeout", tuple(attempt_receipts))
        try:
            async with client.stream(
                "GET",
                current_url,
                follow_redirects=False,
                timeout=config.timeout_seconds,
            ) as response:
                if response.is_redirect:
                    location = response.headers.get("location")
                    if location is None or redirect_count >= config.max_redirects:
                        attempt_receipts.append(
                            CaptureAttempt(
                                redact_url(current_url),
                                response.status_code,
                                "redirect_limit",
                                monotonic() - started,
                            )
                        )
                        raise CaptureError("redirect_limit", tuple(attempt_receipts))
                    attempt_receipts.append(
                        CaptureAttempt(
                            redact_url(current_url),
                            response.status_code,
                            "redirect",
                            monotonic() - started,
                        )
                    )
                    current_url = urljoin(current_url, location)
                    continue
                if response.status_code in {429, 500, 502, 503, 504}:
                    attempt_receipts.append(
                        CaptureAttempt(
                            redact_url(current_url),
                            response.status_code,
                            "retryable_status",
                            monotonic() - started,
                        )
                    )
                    raise CaptureError("retryable_status", tuple(attempt_receipts))
                if response.status_code >= 400:
                    attempt_receipts.append(
                        CaptureAttempt(
                            redact_url(current_url),
                            response.status_code,
                            "terminal_status",
                            monotonic() - started,
                        )
                    )
                    raise CaptureError("terminal_status", tuple(attempt_receipts))
                length = response.headers.get("content-length")
                if length is not None and int(length) > config.max_bytes:
                    attempt_receipts.append(
                        CaptureAttempt(
                            redact_url(current_url),
                            response.status_code,
                            "size_limit",
                            monotonic() - started,
                        )
                    )
                    raise CaptureError("size_limit", tuple(attempt_receipts))
                if (
                    config.expected_etag is not None
                    and response.headers.get("etag") != config.expected_etag
                ):
                    attempt_receipts.append(
                        CaptureAttempt(
                            redact_url(current_url),
                            response.status_code,
                            "validator_mismatch",
                            monotonic() - started,
                        )
                    )
                    raise CaptureError("validator_mismatch", tuple(attempt_receipts))
                if (
                    config.expected_last_modified is not None
                    and response.headers.get("last-modified")
                    != config.expected_last_modified
                ):
                    attempt_receipts.append(
                        CaptureAttempt(
                            redact_url(current_url),
                            response.status_code,
                            "validator_mismatch",
                            monotonic() - started,
                        )
                    )
                    raise CaptureError("validator_mismatch", tuple(attempt_receipts))

                async def chunks():
                    total = 0
                    async for chunk in response.aiter_bytes(config.chunk_bytes):
                        if monotonic() - started >= max_duration:
                            raise CaptureError("timeout", tuple(attempt_receipts))
                        total += len(chunk)
                        if total > config.max_bytes:
                            raise CaptureError("size_limit")
                        yield chunk

                receipt = store.put_stream(await _collect(chunks()))
                attempt_receipts.append(
                    CaptureAttempt(
                        redact_url(current_url),
                        response.status_code,
                        "captured",
                        monotonic() - started,
                    )
                )
                return CaptureResult(
                    current_url,
                    response.status_code,
                    response.headers.get("content-type"),
                    receipt,
                    redirect_count + 1,
                    redirect_count,
                    monotonic() - started,
                    tuple(attempt_receipts),
                )
        except CaptureError:
            raise
        except httpx.TimeoutException, httpx.NetworkError:
            attempt_receipts.append(
                CaptureAttempt(
                    redact_url(current_url),
                    None,
                    "transport_retryable",
                    monotonic() - started,
                )
            )
            raise CaptureError("transport_retryable", tuple(attempt_receipts)) from None
        except ValueError, httpx.HTTPError:
            attempt_receipts.append(
                CaptureAttempt(
                    redact_url(current_url),
                    None,
                    "capture_failed",
                    monotonic() - started,
                )
            )
            raise CaptureError("capture_failed", tuple(attempt_receipts)) from None
    raise CaptureError("redirect_limit", tuple(attempt_receipts))


async def _collect(chunks: AsyncIterable[bytes]) -> list[bytes]:
    """Bridge async bounded chunks to the synchronous object-store contract."""
    values: list[bytes] = []
    async for chunk in chunks:
        values.append(chunk)
    return values
