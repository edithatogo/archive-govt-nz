"""Auditable source alternatives and tombstone re-probe scheduling.

The policy deliberately raises on malformed configuration: an invalid allowlist
must never silently broaden capture scope.
"""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false

# Configuration validation intentionally uses concise exception messages.
# ruff: noqa: EM101, TRY003

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

if TYPE_CHECKING:
    from collections.abc import Mapping


def load_allowlist(document: Mapping[str, object]) -> dict[str, tuple[str, ...]]:
    """Validate an explicit publisher-owned HTTPS alternative allowlist."""
    raw: Any = document.get("alternatives", {})
    if not isinstance(raw, dict):
        raise TypeError("alternatives must be an object")
    result: dict[str, tuple[str, ...]] = {}
    for resource_id, values in raw.items():
        if not isinstance(resource_id, str) or not isinstance(values, list):
            raise TypeError("allowlist keys and values must be strings and arrays")
        checked: list[str] = []
        for value in values:
            if not isinstance(value, str):
                raise TypeError("allowlist URLs must be strings")
            parsed = urlparse(value)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError("allowlist URLs must be absolute HTTPS URLs")
            if value not in checked:
                checked.append(value)
        result[resource_id] = tuple(checked)
    return result


def schedule_tombstone_reprobe(
    probe: Mapping[str, object],
    *,
    now: datetime,
    interval: timedelta = timedelta(days=7),
) -> dict[str, object]:
    """Return a deterministic receipt for each inaccessible resource."""
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    raw: Any = probe.get("results", [])
    if not isinstance(raw, list):
        raise TypeError("probe results must be an array")
    tombstones: list[dict[str, object]] = []
    for item in raw:
        if not isinstance(item, dict) or item.get("state") != "tombstone-required":
            continue
        resource_id = item.get("resource_id")
        if not isinstance(resource_id, str) or not resource_id:
            continue
        tombstones.append(
            {
                "resource_id": resource_id,
                "state": "tombstone-required",
                "reason": item.get("reason", "no eligible secure source"),
                "observed_at": now.isoformat(),
                "next_probe_at": (now + interval).isoformat(),
                "retention": "preserve-prior-history",
            }
        )
    return {
        "schema_version": "archive-govt-nz.tombstone-reprobe/v1",
        "generated_at": now.isoformat(),
        "interval_seconds": int(interval.total_seconds()),
        "tombstones": tombstones,
    }


def utc_now() -> datetime:
    """Provide an injectable timezone-aware clock for callers."""
    return datetime.now(UTC)
