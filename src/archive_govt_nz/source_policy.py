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

HTTP_OK = 200

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
    if interval <= timedelta(0) or interval > timedelta(days=365):
        raise ValueError("interval must be positive and no greater than 365 days")
    raw: Any = probe.get("results", [])
    if not isinstance(raw, list):
        raise TypeError("probe results must be an array")
    tombstones: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict) or item.get("state") != "tombstone-required":
            continue
        resource_id = item.get("resource_id")
        if not isinstance(resource_id, str) or not resource_id:
            continue
        if resource_id in seen:
            continue
        seen.add(resource_id)
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


def classify_metadata_fallback(
    resource: Mapping[str, object],
    *,
    package_status: int | None,
    datastore_status: int | None,
) -> dict[str, object]:
    """Classify CKAN metadata/DataStore reachability without promoting payloads.

    CKAN API responses are diagnostic representations only.  Even a successful
    ``package_show`` or DataStore response cannot make a blocked download URL
    eligible for capture; callers must still pass the source through secure
    resolution and payload policy checks.
    """
    resource_id = resource.get("resource_id")
    if not isinstance(resource_id, str) or not resource_id:
        raise ValueError("resource_id is required")
    package_ok = package_status == HTTP_OK
    datastore_ok = datastore_status == HTTP_OK
    if datastore_ok:
        state = "datastore-diagnostic-available"
    elif package_ok:
        state = "metadata-diagnostic-available"
    else:
        state = "metadata-diagnostic-unavailable"
    return {
        "resource_id": resource_id,
        "state": state,
        "package_status": package_status,
        "datastore_status": datastore_status,
        "payload_eligible": False,
        "eligibility_reason": (
            "metadata/DataStore diagnostics never promote payload eligibility"
        ),
    }


def utc_now() -> datetime:
    """Provide an injectable timezone-aware clock for callers."""
    return datetime.now(UTC)
