"""Deterministic policy and receipts for lawful archive redundancy."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from pathlib import Path

_ARCHIVE_HOST = "web.archive.org"
_DEFAULT_SOURCE_HOSTS = frozenset(
    {
        "catalogue.data.govt.nz",
        "data.govt.nz",
        "nzdmo.govt.nz",
        "treasury.govt.nz",
        "www.nzdmo.govt.nz",
        "www.treasury.govt.nz",
    }
)
_SNAPSHOT_STATES = frozenset(
    {"captured", "failed", "submitted", "unavailable", "verified"}
)


class RedundancyError(ValueError):
    """A redundancy trust, integrity, or receipt invariant failed."""

    def __init__(self, error_class: str) -> None:
        """Expose a bounded error class without sensitive values."""
        self.error_class = error_class
        super().__init__(error_class)


def _error(error_class: str) -> RedundancyError:
    """Build a bounded redundancy exception."""
    return RedundancyError(error_class)


@dataclass(frozen=True, slots=True)
class RedundancyPolicy:
    """Trust and resource bounds for redundancy operations."""

    allowed_source_hosts: frozenset[str] = _DEFAULT_SOURCE_HOSTS
    max_object_bytes: int = 64 * 1024 * 1024
    max_submissions: int = 5
    request_timeout_seconds: float = 45.0

    def __post_init__(self) -> None:
        """Reject configurations that remove a safety bound."""
        if not self.allowed_source_hosts:
            raise _error("empty_source_allowlist")
        if self.max_object_bytes < 1:
            raise _error("invalid_object_limit")
        if self.max_submissions < 0:
            raise _error("invalid_submission_limit")
        if self.request_timeout_seconds <= 0:
            raise _error("invalid_timeout")


@dataclass(frozen=True, slots=True)
class RedundancyObservation:
    """One source and mirror observation for deterministic classification."""

    resource_id: str
    source_url: str
    official_available: bool | None
    snapshot_state: str
    content_match: bool | None = None
    snapshot_url: str | None = None
    sha256: str | None = None
    bytes: int | None = None

    def __post_init__(self) -> None:
        """Validate stable identifiers and closed state values."""
        if not self.resource_id.strip():
            raise _error("missing_resource_id")
        if self.snapshot_state not in _SNAPSHOT_STATES:
            raise _error("unknown_snapshot_state")


@dataclass(frozen=True, slots=True)
class RedundancyReport:
    """Canonical redundancy report and content identity."""

    document: dict[str, object]
    canonical_json: bytes
    sha256: str


def validate_snapshot_url(url: str) -> bool:
    """Accept only credential-free HTTPS Internet Archive snapshot URLs."""
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError as error:
        raise _error("unsafe_snapshot_url") from error
    if (
        parsed.scheme != "https"
        or parsed.hostname != _ARCHIVE_HOST
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or not parsed.path.startswith("/web/")
    ):
        raise _error("unsafe_snapshot_url")
    return True


def validate_submission_url(url: str, policy: RedundancyPolicy) -> bool:
    """Accept credential-free HTTPS source URLs on the configured allowlist."""
    try:
        parsed = urlparse(url)
        port = parsed.port
    except ValueError as error:
        raise _error("source_host_not_allowed") from error
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise _error("unsafe_source_url")
    if port not in {None, 443}:
        raise _error("unsafe_source_url")
    if parsed.hostname not in policy.allowed_source_hosts:
        raise _error("source_host_not_allowed")
    return True


def verify_captured_object(
    path: Path, expected_sha256: str, expected_size: int
) -> bool:
    """Verify a captured object without loading it wholly into memory."""
    if not path.is_file():
        raise _error("object_missing")
    if path.stat().st_size != expected_size:
        raise _error("object_size_mismatch")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != expected_sha256:
        raise _error("object_hash_mismatch")
    return True


def classify_redundancy(
    *,
    official_available: bool | None,
    snapshot_state: str,
    content_match: bool | None,
) -> str:
    """Classify source and mirror evidence without inferring unsupported identity."""
    if snapshot_state not in _SNAPSHOT_STATES:
        raise _error("unknown_snapshot_state")
    if snapshot_state in {"captured", "verified"}:
        captured_states: dict[tuple[bool | None, bool | None], str] = {
            (True, True): "redundant-identical",
            (True, False): "conflict",
            (True, None): "independent-backup-uncompared",
            (False, True): "historical-backup",
            (False, False): "historical-backup",
            (False, None): "historical-backup",
            (None, True): "independent-backup-source-unverified",
            (None, False): "independent-backup-source-unverified",
            (None, None): "independent-backup-source-unverified",
        }
        return captured_states[(official_available, content_match)]
    non_capture_states = {
        "submitted": "pending-verification",
        "failed": "failed",
        "unavailable": {
            True: "official-only",
            False: "unavailable",
            None: "source-unverified",
        }[official_available],
    }
    return str(non_capture_states[snapshot_state])


def build_redundancy_report(
    observations: list[RedundancyObservation], *, observed_at: str
) -> RedundancyReport:
    """Build a stable report whose ordering is independent of discovery order."""
    records = [
        {
            "resource_id": item.resource_id,
            "source_url": item.source_url,
            "official_available": item.official_available,
            "snapshot_state": item.snapshot_state,
            "content_match": item.content_match,
            "snapshot_url": item.snapshot_url,
            "sha256": item.sha256,
            "bytes": item.bytes,
            "classification": classify_redundancy(
                official_available=item.official_available,
                snapshot_state=item.snapshot_state,
                content_match=item.content_match,
            ),
        }
        for item in observations
    ]
    records.sort(
        key=lambda item: (
            str(item["resource_id"]),
            str(item["source_url"]),
            str(item["snapshot_state"]),
        )
    )
    document: dict[str, object] = {
        "schema_version": "archive-govt-nz.redundancy/v1",
        "observed_at": observed_at,
        "record_count": len(records),
        "records": records,
    }
    canonical = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode()
    return RedundancyReport(
        document=document,
        canonical_json=canonical,
        sha256=hashlib.sha256(canonical).hexdigest(),
    )
