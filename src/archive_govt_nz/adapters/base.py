"""Base capture adapter interface, contracts, and error handling."""

from __future__ import annotations

import abc
import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from archive_govt_nz.core.manifests import CaptureEvent, PreservationRecord

if TYPE_CHECKING:
    from archive_govt_nz.core.identity import SourceIdentity
    from archive_govt_nz.object_store import ContentAddressedStore


@dataclass(frozen=True, slots=True)
class AdapterCaptureResult:
    """Outcome of an adapter capture execution cycle."""

    source_identity: SourceIdentity
    status: str
    bytes_captured: int
    objects_created: int
    records: tuple[PreservationRecord, ...]
    error_message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    captured_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_capture_event(self, agent_name: str) -> CaptureEvent:
        """Convert capture result into a verifiable CaptureEvent audit record."""
        event_id = f"evt:{self.source_identity.source_id}:{self.captured_at}"
        prov_id = (
            f"prov:act:{hashlib.sha256(event_id.encode('utf-8')).hexdigest()[:16]}"
        )
        return CaptureEvent(
            event_id=event_id,
            source_id=self.source_identity.source_id,
            status=self.status,
            agent=agent_name,
            bytes_captured=self.bytes_captured,
            objects_created=self.objects_created,
            prov_activity_id=prov_id,
            timestamp=self.captured_at,
            error_message=self.error_message,
        )


class AsyncBaseCaptureAdapter(abc.ABC):
    """Abstract asynchronous base adapter for all source capture integrations."""

    def __init__(self, store: ContentAddressedStore) -> None:
        """Initialize adapter with target content-addressed store."""
        self._store = store

    @property
    @abc.abstractmethod
    def adapter_name(self) -> str:
        """Identifier and version of this capture adapter."""
        ...

    @abc.abstractmethod
    async def capture(self, identity: SourceIdentity) -> AdapterCaptureResult:
        """Execute capture for the specified source identity."""
        ...

    def store_payload(
        self, payload: bytes, media_type: str, uri: str = ""
    ) -> PreservationRecord:
        """Store payload bytes in CAS and construct a PreservationRecord."""
        receipt = self._store.put_bytes(payload)
        record_id = f"rec:{receipt.sha256[:16]}"
        return PreservationRecord(
            record_id=record_id,
            sha256=receipt.sha256,
            size_bytes=receipt.byte_count,
            media_type=media_type,
            uri=uri,
        )
