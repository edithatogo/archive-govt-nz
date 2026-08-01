"""Auditable source alternatives and tombstone re-probe scheduling.

The policy deliberately raises on malformed configuration: an invalid allowlist
must never silently broaden capture scope.
"""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false

# Configuration validation intentionally uses concise exception messages.
# ruff: noqa: EM101, TRY003

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any, cast
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
    prior: Mapping[str, object] | None = None,
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
    prior_rows = _prior_tombstones(prior)
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
        previous = prior_rows.get(resource_id, {})
        attempts = previous.get("attempt_count", 0)
        if not isinstance(attempts, int) or attempts < 0:
            attempts = 0
        tombstones.append(
            {
                "resource_id": resource_id,
                "state": "tombstone-required",
                "reason": item.get("reason", "no eligible secure source"),
                "observed_at": now.isoformat(),
                "next_probe_at": (now + interval).isoformat(),
                "attempt_count": attempts + 1,
                "retry_state": "scheduled",
                "retention": "preserve-prior-history",
            }
        )
    return {
        "schema_version": "archive-govt-nz.tombstone-reprobe/v1",
        "generated_at": now.isoformat(),
        "interval_seconds": int(interval.total_seconds()),
        "tombstones": tombstones,
    }


def _prior_tombstones(
    prior: Mapping[str, object] | None,
) -> dict[str, Mapping[str, object]]:
    if prior is None:
        return {}
    raw_prior: Any = prior.get("tombstones", [])
    if not isinstance(raw_prior, list):
        raise TypeError("prior tombstones must be an array")
    return {
        row["resource_id"]: row
        for row in raw_prior
        if isinstance(row, dict) and isinstance(row.get("resource_id"), str)
    }


def validate_tombstone_reprobe_receipt(
    receipt: Mapping[str, object], *, expected_count: int | None = None
) -> None:
    """Validate a re-probe receipt before it is published as evidence."""
    if receipt.get("schema_version") != "archive-govt-nz.tombstone-reprobe/v1":
        raise ValueError("unexpected re-probe schema")
    raw_rows = receipt.get("tombstones")
    if not isinstance(raw_rows, list):
        raise TypeError("tombstones must be an array")
    rows = cast("list[object]", raw_rows)
    if expected_count is not None and len(rows) != expected_count:
        raise ValueError("unexpected tombstone count")
    ids: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise TypeError("tombstone rows must be objects")
        resource_id = row.get("resource_id")
        if not isinstance(resource_id, str) or not resource_id or resource_id in ids:
            raise ValueError("tombstone resource IDs must be unique non-empty strings")
        ids.add(resource_id)
        if row.get("state") != "tombstone-required":
            raise ValueError("invalid tombstone state")
        if row.get("retry_state") != "scheduled":
            raise ValueError("invalid retry state")
        if not isinstance(row.get("attempt_count"), int) or row["attempt_count"] < 1:
            raise ValueError("invalid attempt count")


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
