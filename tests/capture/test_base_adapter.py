"""Test suite for AsyncBaseCaptureAdapter and AdapterCaptureResult."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.adapters.base import (
    AdapterCaptureResult,
    AsyncBaseCaptureAdapter,
)
from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


class DummyAdapter(AsyncBaseCaptureAdapter):
    """Concrete dummy adapter for testing base class behavior."""

    @property
    def adapter_name(self) -> str:
        """Return dummy adapter name."""
        return "archive-govt-nz/capture/dummy:0.1.0"

    async def capture(self, identity: SourceIdentity) -> AdapterCaptureResult:
        """Capture dummy payload."""
        rec = self.store_payload(b"dummy-content", media_type="text/plain")
        return AdapterCaptureResult(
            source_identity=identity,
            status="success",
            bytes_captured=13,
            objects_created=1,
            records=(rec,),
        )


@pytest.mark.anyio
async def test_dummy_adapter_capture_and_event(tmp_path: Path) -> None:
    """Validate dummy adapter store_payload and to_capture_event."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = DummyAdapter(store)
    identity = SourceIdentity(
        source_type=SourceType.WEB,
        agency_slug="dummy",
        target="example.com",
        source_id="web:dummy:example.com",
        uri="web://dummy/example.com",
    )

    result = await adapter.capture(identity)
    assert result.status == "success"
    assert result.bytes_captured == 13
    assert len(result.records) == 1
    record = result.records[0]
    assert record.record_id == f"rec:{record.sha256[:16]}"

    event = result.to_capture_event(adapter.adapter_name)
    assert event.source_id == identity.source_id
    assert event.status == "success"
    assert event.bytes_captured == 13
    assert event.agent == adapter.adapter_name
