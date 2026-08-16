"""Email newsletter and inbound webhook payload capture adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from archive_govt_nz.adapters.base import (
    AdapterCaptureResult,
    AsyncBaseCaptureAdapter,
)
from archive_govt_nz.core.identity import SourceType

if TYPE_CHECKING:
    from archive_govt_nz.core.identity import SourceIdentity
    from archive_govt_nz.object_store import ContentAddressedStore


class EmailCaptureAdapter(AsyncBaseCaptureAdapter):
    """Adapter for processing and preserving inbound email newsletters."""

    def __init__(self, store: ContentAddressedStore) -> None:
        """Initialize Email adapter."""
        super().__init__(store)

    @property
    def adapter_name(self) -> str:
        """Adapter name and version."""
        return "archive-govt-nz/capture/email:0.1.0"

    async def capture(self, identity: SourceIdentity) -> AdapterCaptureResult:
        """Process identity for email capture (requires payload ingest)."""
        if identity.source_type != SourceType.EMAIL:
            return AdapterCaptureResult(
                source_identity=identity,
                status="failed",
                bytes_captured=0,
                objects_created=0,
                records=(),
                error_message=f"unsupported source type: {identity.source_type}",
            )

        return AdapterCaptureResult(
            source_identity=identity,
            status="unchanged",
            bytes_captured=0,
            objects_created=0,
            records=(),
            error_message=None,
        )

    def ingest_email_payload(
        self,
        identity: SourceIdentity,
        raw_eml: bytes | str,
        metadata: dict[str, Any] | None = None,
    ) -> AdapterCaptureResult:
        """Ingest and store an inbound email message payload directly into CAS."""
        if identity.source_type != SourceType.EMAIL:
            return AdapterCaptureResult(
                source_identity=identity,
                status="failed",
                bytes_captured=0,
                objects_created=0,
                records=(),
                error_message=f"unsupported source type: {identity.source_type}",
            )

        payload_bytes = raw_eml.encode("utf-8") if isinstance(raw_eml, str) else raw_eml
        record = self.store_payload(
            payload_bytes,
            media_type="message/rfc822",
            uri=f"email://{identity.agency_slug}/{identity.target}",
        )

        records = [record]
        if metadata:
            meta_bytes = json.dumps(metadata, sort_keys=True).encode("utf-8")
            meta_record = self.store_payload(
                meta_bytes,
                media_type="application/json",
                uri=f"email://{identity.agency_slug}/{identity.target}#metadata",
            )
            records.append(meta_record)

        total_bytes = sum(r.size_bytes for r in records)
        return AdapterCaptureResult(
            source_identity=identity,
            status="success",
            bytes_captured=total_bytes,
            objects_created=len(records),
            records=tuple(records),
        )
