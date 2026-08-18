"""New Zealand Legislation API and bulk acquisition capture adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from archive_govt_nz.adapters.base import (
    AdapterCaptureResult,
    AsyncBaseCaptureAdapter,
)
from archive_govt_nz.core.identity import SourceType
from archive_govt_nz.domains.legislation.normalise import normalise_legislation_payload

if TYPE_CHECKING:
    from archive_govt_nz.core.identity import SourceIdentity
    from archive_govt_nz.object_store import ContentAddressedStore

HTTP_OK = 200
HTTP_TOO_MANY_REQUESTS = 429


class NZLegislationAdapter(AsyncBaseCaptureAdapter):
    """Adapter for official NZ Legislation XML/HTML capture."""

    def __init__(
        self,
        store: ContentAddressedStore,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize adapter with store and optional HTTP client."""
        super().__init__(store)
        self._client = client

    @property
    def adapter_name(self) -> str:
        """Adapter name and version."""
        return "archive-govt-nz/capture/legislation:0.1.0"

    async def capture(self, identity: SourceIdentity) -> AdapterCaptureResult:
        """Fetch legislation document and store raw payload in CAS."""
        if identity.source_type != SourceType.LEGISLATION:
            return AdapterCaptureResult(
                source_identity=identity,
                status="failed",
                bytes_captured=0,
                objects_created=0,
                records=(),
                error_message=f"unsupported source type: {identity.source_type}",
            )

        url = identity.target
        headers = {
            "User-Agent": (
                "archive-govt-nz/0.1.0 (Legislation Preservation Bot; "
                "+https://github.com/edithatogo/archive-govt-nz)"
            )
        }

        try:
            client = self._client or httpx.AsyncClient(timeout=30.0)
            try:
                response = await client.get(url, headers=headers)
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
                    error_message="rate limited by legislation source",
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
            media_type = response.headers.get("content-type", "application/xml")
            preservation_rec = self.store_payload(
                content, media_type=media_type, uri=url
            )

            # Normalise document to verify structure
            _ = normalise_legislation_payload(
                content,
                identity.source_id,
                identity.source_id,
                url,
            )

            return AdapterCaptureResult(
                source_identity=identity,
                status="success",
                bytes_captured=len(content),
                objects_created=1,
                records=(preservation_rec,),
            )
        except (httpx.HTTPError, OSError) as err:
            return AdapterCaptureResult(
                source_identity=identity,
                status="failed",
                bytes_captured=0,
                objects_created=0,
                records=(),
                error_message=str(err),
            )
