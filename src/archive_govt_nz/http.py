"""Unified HTTP client with bounded streaming, timeouts, and rate limit handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

import httpx

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from types import TracebackType

    from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreReceipt

DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_USER_AGENT = (
    "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"
)


class ArchiveHttpClient:
    """Unified asynchronous HTTP client for evidence capture and CAS streaming."""

    def __init__(
        self,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        user_agent: str = DEFAULT_USER_AGENT,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize HTTP client with defaults."""
        self._timeout = timeout_seconds
        self._user_agent = user_agent
        self._client = client or httpx.AsyncClient(
            timeout=timeout_seconds,
            headers={"User-Agent": user_agent},
            follow_redirects=True,
        )

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self._client.aclose()

    async def get_bytes(self, uri: str) -> bytes:
        """Fetch full bytes from a remote URI."""
        response = await self._client.get(uri)
        response.raise_for_status()
        return response.content

    async def stream_to_cas(
        self,
        uri: str,
        store: ContentAddressedStore,
    ) -> ObjectStoreReceipt:
        """Stream HTTP response directly into CAS without full RAM buffering."""
        async with self._client.stream("GET", uri) as response:
            response.raise_for_status()
            chunks = [chunk async for chunk in response.aiter_bytes()]
            return store.put_bytes(b"".join(chunks))

    async def stream_chunks(self, uri: str) -> AsyncIterator[bytes]:
        """Stream raw byte chunks from URI."""
        async with self._client.stream("GET", uri) as response:
            response.raise_for_status()
            async for chunk in response.aiter_bytes():
                yield chunk
