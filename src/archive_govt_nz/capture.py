"""Bounded streaming retrieval into the immutable object store."""

from __future__ import annotations

from collections.abc import AsyncIterable
from dataclasses import dataclass
from time import monotonic
from urllib.parse import urljoin

import httpx

from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreReceipt


class CaptureError(RuntimeError):
    """Fail-closed capture outcome with a stable class."""

    def __init__(self, error_class: str) -> None:
        self.error_class = error_class
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
                self.max_duration_seconds is not None
                and self.max_duration_seconds <= 0
            )
        ):
            raise ValueError("invalid_capture_bound")


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


async def capture_url(
    client: httpx.AsyncClient,
    url: str,
    store: ContentAddressedStore,
    config: CaptureConfig = CaptureConfig(),
) -> CaptureResult:
    """Stream one URL, enforcing status, length, and byte limits."""
    current_url = url
    started = monotonic()
    max_duration = config.max_duration_seconds or config.timeout_seconds
    for redirect_count in range(config.max_redirects + 1):
        if monotonic() - started >= max_duration:
            raise CaptureError("timeout")
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
                        raise CaptureError("redirect_limit")
                    current_url = urljoin(current_url, location)
                    continue
                if response.status_code in {429, 500, 502, 503, 504}:
                    raise CaptureError("retryable_status")
                if response.status_code >= 400:
                    raise CaptureError("terminal_status")
                length = response.headers.get("content-length")
                if length is not None and int(length) > config.max_bytes:
                    raise CaptureError("size_limit")
                if (
                    config.expected_etag is not None
                    and response.headers.get("etag") != config.expected_etag
                ):
                    raise CaptureError("validator_mismatch")
                if (
                    config.expected_last_modified is not None
                    and response.headers.get("last-modified")
                    != config.expected_last_modified
                ):
                    raise CaptureError("validator_mismatch")

                async def chunks():
                    total = 0
                    async for chunk in response.aiter_bytes(config.chunk_bytes):
                        if monotonic() - started >= max_duration:
                            raise CaptureError("timeout")
                        total += len(chunk)
                        if total > config.max_bytes:
                            raise CaptureError("size_limit")
                        yield chunk

                receipt = store.put_stream(await _collect(chunks()))
                return CaptureResult(
                    current_url,
                    response.status_code,
                    response.headers.get("content-type"),
                    receipt,
                    redirect_count + 1,
                    redirect_count,
                    monotonic() - started,
                )
        except CaptureError:
            raise
        except httpx.TimeoutException, httpx.NetworkError:
            raise CaptureError("transport_retryable") from None
        except ValueError, httpx.HTTPError:
            raise CaptureError("capture_failed") from None
    raise CaptureError("redirect_limit")


async def _collect(chunks: AsyncIterable[bytes]) -> list[bytes]:
    """Bridge async bounded chunks to the synchronous object-store contract."""
    values: list[bytes] = []
    async for chunk in chunks:
        values.append(chunk)
    return values
