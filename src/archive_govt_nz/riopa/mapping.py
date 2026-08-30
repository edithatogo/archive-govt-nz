"""Fail-closed mapping of immutable archive receipts into RIOPA records.

This module accepts already archived receipt data only.  It deliberately does
not fetch, refresh, or infer any source, rights, or legal-status information.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Mapping

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED = {
    "receipt_id",
    "archive_id",
    "source_url",
    "revision",
    "sha256",
    "object_id",
    "status",
    "rights",
    "capability",
    "source_health",
    "legal_status",
    "observed_at",
}


class RiopaMappingError(ValueError):
    """A receipt cannot safely be represented as a RIOPA record."""

    def __init__(self, error_class: str) -> None:
        self.error_class = error_class
        super().__init__(error_class)


def map_archive_receipt(
    receipt: Mapping[str, Any],
    *,
    expected_revision: str | None = None,
    expected_sha256: str | None = None,
) -> dict[str, Any]:
    """Map one archived receipt to deterministic RIOPA source/capture records.

    Identity is derived from canonical source metadata and the content digest;
    no live endpoint is contacted.  A partial/failed capture is retained as a
    quarantined record, while stale revisions, digest drift, and malformed
    content-addressed identifiers raise immediately.
    """
    missing = sorted(_REQUIRED - receipt.keys())
    if missing:
        raise RiopaMappingError("missing_" + missing[0])
    digest = receipt["sha256"]
    object_id = receipt["object_id"]
    if not isinstance(digest, str) or not _SHA256.fullmatch(digest):
        raise RiopaMappingError("invalid_sha256")
    if not isinstance(object_id, str) or object_id != f"sha256:{digest}":
        raise RiopaMappingError(
            "invalid_object_id" if not isinstance(object_id, str) else "digest_mismatch"
        )
    revision = receipt["revision"]
    if expected_revision is not None and revision != expected_revision:
        raise RiopaMappingError("stale_revision")
    if expected_sha256 is not None and digest != expected_sha256:
        raise RiopaMappingError("digest_mismatch")

    source_identity = _canonical_bytes(
        {
            "archive_id": receipt["archive_id"],
            "source_url": receipt["source_url"],
            "revision": revision,
        }
    )
    capture_identity = _canonical_bytes(
        {
            "receipt_id": receipt["receipt_id"],
            "object_id": object_id,
            "revision": revision,
        }
    )
    source_id = f"sha256:{hashlib.sha256(source_identity).hexdigest()}"
    capture_id = f"sha256:{hashlib.sha256(capture_identity).hexdigest()}"

    status, reason = _qualification(receipt)
    result: dict[str, Any] = {
        "schema_version": "archive-govt-nz.riopa-source-capture/v1",
        "source": {
            "source_id": source_id,
            "archive_id": receipt["archive_id"],
            "source_url": receipt["source_url"],
            "revision": revision,
        },
        "capture": {
            "capture_id": capture_id,
            "receipt_id": receipt["receipt_id"],
            "object_id": object_id,
            "sha256": digest,
            "observed_at": receipt["observed_at"],
            "status": receipt["status"],
        },
        "boundaries": {
            "rights": receipt["rights"],
            "capability": receipt["capability"],
            "source_health": receipt["source_health"],
            "legal_status": receipt["legal_status"],
        },
        "status": status,
    }
    if reason is not None:
        result["quarantine_reason"] = reason
    return result


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def _qualification(receipt: Mapping[str, Any]) -> tuple[str, str | None]:
    if receipt["status"] in {"partial", "failed", "negative", "unavailable"}:
        return "quarantined", f"{receipt['status']}_capture"
    rights = receipt["rights"]
    if not isinstance(rights, Mapping) or rights.get("status") != "resolved":
        return "quarantined", "rights_unresolved"
    return "eligible", None


__all__ = ["RiopaMappingError", "map_archive_receipt"]
