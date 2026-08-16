"""Test suite for DeterministicReplayEngine."""

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.core.manifests import PreservationRecord
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.replay import DeterministicReplayEngine

if TYPE_CHECKING:
    from pathlib import Path


def test_replay_json_payload() -> None:
    """Validate deterministic JSON payload replay."""
    payload = b'{"items": [1, 2, 3], "status": "ok"}'
    res = DeterministicReplayEngine.replay_payload(payload, "application/json")
    assert res["status"] == "ok"
    assert res["items"] == [1, 2, 3]


def test_replay_feed_payload() -> None:
    """Validate deterministic RSS feed replay."""
    xml_content = (
        b"<rss><channel><title>Health Updates</title>"
        b"<item><title>News 1</title></item></channel></rss>"
    )
    res = DeterministicReplayEngine.replay_payload(xml_content, "application/rss+xml")
    assert res["title"] == "Health Updates"
    assert res["item_count"] == 1


def test_replay_generic_payload() -> None:
    """Validate generic raw payload replay."""
    payload = b"plain text data"
    res = DeterministicReplayEngine.replay_payload(payload, "text/plain")
    assert res["media_type"] == "text/plain"
    assert res["byte_count"] == 15


def test_verify_record_fixity(tmp_path: Path) -> None:
    """Validate fixity check on CAS store."""
    store = ContentAddressedStore(tmp_path / "cas")
    receipt = store.put_bytes(b"content")

    record = PreservationRecord(
        record_id="rec-1",
        sha256=receipt.sha256,
        size_bytes=receipt.byte_count,
        media_type="text/plain",
    )
    assert DeterministicReplayEngine.verify_record_fixity(store, record) is True

    # Bad record
    bad_record = PreservationRecord(
        record_id="rec-2",
        sha256="0000000000000000000000000000000000000000000000000000000000000000",
        size_bytes=7,
        media_type="text/plain",
    )
    assert DeterministicReplayEngine.verify_record_fixity(store, bad_record) is False
