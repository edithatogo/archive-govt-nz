"""Bind the fixed Crown admission to independently pinned retained census bytes."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.fiscal_crown_literals import (
    SOURCE_URL,
    VINTAGE,
)
from archive_govt_nz.domains.health_appropriations.rebuild import _json
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

MAX_RECEIPT_BYTES = 1024 * 1024


def _require(value: object) -> None:
    if not value:
        message = "crown_receipt_contract"
        raise ValueError(message)


def read_crown_receipt(path: Path, pin: str) -> str:
    """Read one capped pinned snapshot without creating archive state."""
    _require(not any(part.is_symlink() for part in (path, *path.parents)))
    return verified_snapshot(path, pin, max_bytes=MAX_RECEIPT_BYTES).decode("utf-8")


def parse_crown_receipt(payload: bytes, pin: str, source_sha256: str) -> dict[str, Any]:
    """Join exactly one retained census row, not a new capture/rights assertion.

    Vintage is the fixed admission profile selected by the exact title/family/URL.
    The timestamp must agree with that existing admission; return the receipt's
    original timestamp spelling rather than synthesizing another observation ID.
    """
    _require(len(payload) <= MAX_RECEIPT_BYTES)
    _require(hashlib.sha256(payload).hexdigest() == pin)
    document = _json(payload)
    _require(document["schema_version"] == "archive-govt-nz.health-source-census/v1")
    rows = document["records"]
    _require(isinstance(rows, list) and all(isinstance(row, dict) for row in rows))
    _require(
        type(document["record_count"]) is int and document["record_count"] == len(rows)
    )
    matches = [
        row
        for row in rows
        if (
            row.get("object_sha256") == source_sha256
            or row.get("url") == SOURCE_URL
            or row.get("source_id") == "fiscal_time_series-007"
        )
    ]
    _require(len(matches) == 1)
    row = matches[0]
    _require(
        all(
            row.get(key) == value
            for key, value in {
                "source_id": "fiscal_time_series-007",
                "object_sha256": source_sha256,
                "url": SOURCE_URL,
                "family": "fiscal_time_series",
                "title": "Historical fiscal indicators 1972-2025",
                "disposition": "captured",
            }.items()
        )
    )
    observed = row["observed_at"]
    _require(isinstance(observed, str))
    _require(
        datetime.fromisoformat(observed)
        == datetime.fromisoformat("2026-08-29T09:00:17+00:00")
    )
    return {
        "sha256": source_sha256,
        "object_id": "sha256:" + source_sha256,
        "locator": row["url"],
        "vintage": VINTAGE,
        "observed_at": observed,
    }
