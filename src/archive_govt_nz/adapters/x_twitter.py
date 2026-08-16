"""X / Twitter public post and syndication capture adapter."""

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


class XCaptureAdapter(AsyncBaseCaptureAdapter):
    """Adapter for archiving public X/Twitter profiles and syndication feeds."""

    def __init__(
        self,
        store: ContentAddressedStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize X capture adapter."""
        super().__init__(store)
        self._client = client

    @property
    def adapter_name(self) -> str:
        """Adapter name and version."""
        return "archive-govt-nz/capture/x:0.1.0"

    async def capture(self, identity: SourceIdentity) -> AdapterCaptureResult:
        """Fetch syndication/profile data and store payload in CAS."""
        if identity.source_type != SourceType.X:
            return AdapterCaptureResult(
                source_identity=identity,
                status="failed",
                bytes_captured=0,
                objects_created=0,
                records=(),
                error_message=f"unsupported source type: {identity.source_type}",
            )

        handle = identity.target.lstrip("@")
        syndication_url = (
            f"https://syndication.twitter.com/srv/timeline-profile/screen-name/{handle}"
        )
        headers = {
            "User-Agent": (
                "archive-govt-nz/0.1.0 (Government Archival Bot; "
                "+https://github.com/edithatogo/archive-govt-nz)"
            )
        }

        try:
            client = self._client or httpx.AsyncClient(timeout=30.0)
            try:
                response = await client.get(syndication_url, headers=headers)
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
                content, media_type="text/html", uri=syndication_url
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
