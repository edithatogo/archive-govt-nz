"""Deterministic offline replay engine for archived payloads."""

from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING, Any

from archive_govt_nz.object_store import ObjectStoreError

if TYPE_CHECKING:
    from archive_govt_nz.core.manifests import PreservationRecord
    from archive_govt_nz.object_store import ContentAddressedStore


class DeterministicReplayEngine:
    """Offline deterministic parser and replayer for archived byte streams."""

    @staticmethod
    def verify_record_fixity(
        store: ContentAddressedStore, record: PreservationRecord
    ) -> bool:
        """Verify that record content in CAS matches its declared SHA-256 fixity."""
        object_id = f"sha256:{record.sha256}"
        try:
            receipt = store.verify(object_id)
        except ObjectStoreError, OSError:
            return False
        else:
            return (
                receipt.sha256 == record.sha256
                and receipt.byte_count == record.size_bytes
            )

    @staticmethod
    def replay_json_payload(raw_bytes: bytes) -> dict[str, Any]:
        """Parse raw JSON payload deterministically."""
        data = json.loads(raw_bytes.decode("utf-8"))
        if not isinstance(data, dict):
            return {"data": data}
        return data

    @staticmethod
    def replay_feed_payload(raw_bytes: bytes) -> dict[str, Any]:
        """Parse raw XML/RSS/Atom feed payload deterministically."""
        root = ET.fromstring(raw_bytes.decode("utf-8"))  # noqa: S314
        title_elem = root.find(".//title")
        title = title_elem.text if title_elem is not None else ""
        items = root.findall(".//item") or root.findall(".//entry") or []
        return {
            "root_tag": root.tag,
            "title": title,
            "item_count": len(items),
        }

    @classmethod
    def replay_payload(cls, raw_bytes: bytes, media_type: str) -> dict[str, Any]:
        """Replay payload based on media type."""
        norm_type = media_type.lower().strip()
        if "json" in norm_type:
            return cls.replay_json_payload(raw_bytes)
        if "xml" in norm_type or "rss" in norm_type or "atom" in norm_type:
            return cls.replay_feed_payload(raw_bytes)
        return {
            "media_type": media_type,
            "byte_count": len(raw_bytes),
            "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        }
