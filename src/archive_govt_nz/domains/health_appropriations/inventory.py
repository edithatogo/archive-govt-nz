"""Typed, fail-closed source census contracts for health appropriations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from urllib.parse import urlsplit, urlunsplit


class Disposition(StrEnum):
    """Exhaustive source observation outcomes."""

    CAPTURED = "captured"
    UNCHANGED = "unchanged"
    SUPERSEDED = "superseded"
    UNAVAILABLE = "unavailable"
    WITHDRAWN = "withdrawn"
    RESTRICTED = "restricted"
    CORRUPT = "corrupt"
    RETRYABLE = "retryable"
    DUPLICATE = "duplicate"
    OUT_OF_SCOPE = "out_of_scope"
    DISCOVERED = "discovered"


def normalize_url(value: str) -> str:
    """Canonicalize a public HTTP locator without dropping its query."""
    parsed = urlsplit(value.strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("invalid_source_url")
    host = parsed.hostname.lower()
    port = parsed.port
    if port and not (
        (parsed.scheme.lower() == "http" and port == 80)
        or (parsed.scheme.lower() == "https" and port == 443)
    ):
        host = f"{host}:{port}"
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), host, path, parsed.query, ""))


@dataclass(frozen=True, slots=True)
class SourceInventoryRecord:
    """One source candidate at a declared observation cutoff."""

    source_id: str
    family: str
    title: str
    url: str
    observed_at: str
    cutoff: str
    disposition: Disposition
    media_type: str | None = None
    vintage: str | None = None
    rights_uri: str | None = None
    object_sha256: str | None = None
    predecessor_source_id: str | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        """Reject ambiguous or internally inconsistent observations."""
        if not self.source_id or not self.family or not self.title:
            raise ValueError("missing_source_identity")
        object.__setattr__(self, "url", normalize_url(self.url))
        if self.object_sha256 is not None and (
            len(self.object_sha256) != 64
            or any(char not in "0123456789abcdef" for char in self.object_sha256)
        ):
            raise ValueError("invalid_source_digest")
        object_states = {Disposition.CAPTURED, Disposition.UNCHANGED}
        if self.disposition in object_states and self.object_sha256 is None:
            raise ValueError("captured_source_missing_digest")
        if (
            self.disposition is Disposition.SUPERSEDED
            and not self.predecessor_source_id
        ):
            raise ValueError("superseded_source_missing_predecessor")
        if self.disposition not in object_states and not self.reason:
            raise ValueError("non_object_disposition_missing_reason")

    @property
    def record_id(self) -> str:
        """Return a stable identity for this exact normalized observation."""
        payload = json.dumps(
            asdict(self), sort_keys=True, separators=(",", ":"), default=str
        ).encode()
        return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def validate_inventory(records: list[SourceInventoryRecord]) -> None:
    """Require unique source IDs and one explicit disposition per item."""
    identifiers = [record.source_id for record in records]
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("duplicate_source_disposition")
    known = set(identifiers)
    for record in records:
        predecessor = record.predecessor_source_id
        if predecessor is not None and predecessor not in known:
            raise ValueError("unknown_predecessor")
