"""New Zealand Legislation API and bulk acquisition capture adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.adapters.base import (
    AdapterCaptureResult,
    AsyncBaseCaptureAdapter,
)
from archive_govt_nz.core.identity import SourceType
from archive_govt_nz.domains.legislation.api import (
    HTTP_NOT_MODIFIED,
    HTTP_OK,
    HTTP_TOO_MANY_REQUESTS,
    NZLegislationApiClient,
)
from archive_govt_nz.domains.legislation.normalise import (
    normalise_legislation_payload,
)

if TYPE_CHECKING:
    from archive_govt_nz.core.identity import SourceIdentity
    from archive_govt_nz.object_store import ContentAddressedStore


class NZLegislationAdapter(AsyncBaseCaptureAdapter):
    """Adapter for official NZ Legislation XML/HTML capture using API client."""

    def __init__(
        self,
        store: ContentAddressedStore,
        api_client: NZLegislationApiClient | None = None,
    ) -> None:
        """Initialize adapter with store and legislation API client."""
        super().__init__(store)
        self._api_client = api_client or NZLegislationApiClient()

    @property
    def adapter_name(self) -> str:
        """Adapter name and version."""
        return "archive-govt-nz/capture/legislation:0.1.0"

    async def capture(
        self,
        identity: SourceIdentity,
        *,
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> AdapterCaptureResult:
        """Fetch legislation document and store raw payload in CAS via client."""
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

        try:
            (
                status_code,
                content,
                headers,
            ) = await self._api_client.get_document_raw_async(
                url, etag=etag, last_modified=last_modified
            )

            response_metadata = {
                "http_status": str(status_code),
                "etag": headers.get("etag"),
                "last_modified": headers.get("last-modified"),
            }

            if status_code == HTTP_TOO_MANY_REQUESTS:
                return AdapterCaptureResult(
                    source_identity=identity,
                    status="rate_limited",
                    bytes_captured=0,
                    objects_created=0,
                    records=(),
                    error_message="rate limited by legislation source",
                    metadata=response_metadata,
                )

            if status_code == HTTP_NOT_MODIFIED:
                return AdapterCaptureResult(
                    source_identity=identity,
                    status="not_modified",
                    bytes_captured=0,
                    objects_created=0,
                    records=(),
                    metadata=response_metadata,
                )

            if status_code != HTTP_OK:
                return AdapterCaptureResult(
                    source_identity=identity,
                    status="failed",
                    bytes_captured=0,
                    objects_created=0,
                    records=(),
                    error_message=f"HTTP {status_code}",
                    metadata=response_metadata,
                )

            media_type = headers.get("content-type", "application/xml")
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
                metadata=response_metadata,
            )
        except Exception as err:  # noqa: BLE001
            return AdapterCaptureResult(
                source_identity=identity,
                status="failed",
                bytes_captured=0,
                objects_created=0,
                records=(),
                error_message=str(err),
            )
