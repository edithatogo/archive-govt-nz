"""Bounded streaming retrieval into the immutable object store."""

from __future__ import annotations

from dataclasses import dataclass

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

    def __post_init__(self) -> None:
        if self.max_bytes < 1 or self.chunk_bytes < 1 or self.timeout_seconds <= 0:
            raise ValueError("invalid_capture_bound")


@dataclass(frozen=True, slots=True)
class CaptureResult:
    """Bounded response evidence and the promoted immutable object."""

    url: str
    status_code: int
    content_type: str | None
    receipt: ObjectStoreReceipt


async def capture_url(
    client: httpx.AsyncClient,
    url: str,
    store: ContentAddressedStore,
    config: CaptureConfig = CaptureConfig(),
) -> CaptureResult:
    """Stream one URL, enforcing status, length, and byte limits."""
    try:
        async with client.stream("GET", url, follow_redirects=False) as response:
            if response.status_code in {429, 500, 502, 503, 504}:
                raise CaptureError("retryable_status")
            if response.status_code >= 400:
                raise CaptureError("terminal_status")
            length = response.headers.get("content-length")
            if length is not None and int(length) > config.max_bytes:
                raise CaptureError("size_limit")

            async def chunks():
                total = 0
                async for chunk in response.aiter_bytes(config.chunk_bytes):
                    total += len(chunk)
                    if total > config.max_bytes:
                        raise CaptureError("size_limit")
                    yield chunk

            receipt = store.put_stream(await _collect(chunks()))
            return CaptureResult(url, response.status_code, response.headers.get("content-type"), receipt)
    except CaptureError:
        raise
    except (httpx.TimeoutException, httpx.NetworkError):
        raise CaptureError("transport_retryable") from None
    except (ValueError, httpx.HTTPError):
        raise CaptureError("capture_failed") from None


async def _collect(chunks):
    """Bridge async bounded chunks to the synchronous object-store contract."""
    values = []
    async for chunk in chunks:
        values.append(chunk)
    return values
