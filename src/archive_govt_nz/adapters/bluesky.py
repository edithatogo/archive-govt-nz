"""Bluesky / AT Protocol public author feed capture adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from archive_govt_nz.adapters.base import (
    AdapterCaptureResult,
    AsyncBaseCaptureAdapter,
)
from archive_govt_nz.core.identity import SourceType

if TYPE_CHECKING:
    from archive_govt_nz.core.identity import SourceIdentity
    from archive_govt_nz.object_store import ContentAddressedStore

HTTP_OK = 200
HTTP_TOO_MANY_REQUESTS = 429
ATPROTO_XRPC_FEED_ENDPOINT = (
    "https://public.api.bsky.app/xrpc/app.bsky.feed.getAuthorFeed"
)


class BlueskyCaptureAdapter(AsyncBaseCaptureAdapter):
    """Adapter for archiving public Bluesky accounts via AT Protocol XRPC API."""

    def __init__(
        self,
        store: ContentAddressedStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize Bluesky adapter."""
        super().__init__(store)
        self._client = client

    @property
    def adapter_name(self) -> str:
        """Adapter name and version."""
        return "archive-govt-nz/capture/bluesky:0.1.0"

    async def capture(self, identity: SourceIdentity) -> AdapterCaptureResult:
        """Fetch author feed and store payload in CAS."""
        if identity.source_type != SourceType.BLUESKY:
            return AdapterCaptureResult(
                source_identity=identity,
                status="failed",
                bytes_captured=0,
                objects_created=0,
                records=(),
                error_message=f"unsupported source type: {identity.source_type}",
            )

        actor_handle = identity.target
        params = {"actor": actor_handle, "limit": 50}
        headers = {
            "User-Agent": (
                "archive-govt-nz/0.1.0 (Government Archival Bot; "
                "+https://github.com/edithatogo/archive-govt-nz)"
            )
        }

        try:
            client = self._client or httpx.AsyncClient(timeout=30.0)
            try:
                response = await client.get(
                    ATPROTO_XRPC_FEED_ENDPOINT, params=params, headers=headers
                )
            finally:
                if self._client is None:
                    await client.aclose()

            if response.status_code == HTTP_TOO_MANY_REQUESTS:
                return AdapterCaptureResult(
                    source_identity=identity,
                    status="rate_limited",
                    bytes_captured=0,
                    objects_created=0,
                    records=(),
                    error_message="rate limited (429)",
                )

            if response.status_code != HTTP_OK:
                return AdapterCaptureResult(
                    source_identity=identity,
                    status="failed",
                    bytes_captured=0,
                    objects_created=0,
                    records=(),
                    error_message=f"HTTP {response.status_code}",
                )

            content = response.content
            record = self.store_payload(
                content,
                media_type="application/json",
                uri=f"{ATPROTO_XRPC_FEED_ENDPOINT}?actor={actor_handle}",
            )

            return AdapterCaptureResult(
                source_identity=identity,
                status="success",
                bytes_captured=len(content),
                objects_created=1,
                records=(record,),
            )

        except (httpx.HTTPError, OSError) as exc:
            return AdapterCaptureResult(
                source_identity=identity,
                status="failed",
                bytes_captured=0,
                objects_created=0,
                records=(),
                error_message=str(exc),
            )
