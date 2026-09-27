"""Stable schema and exact-layout fingerprint comparison for source adapters."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import pyarrow as pa

if TYPE_CHECKING:
    from collections.abc import Mapping

_HASH_LENGTH = 64
_SCHEMA_ERROR = "arrow_schema_required"
_SNAPSHOT_ERROR = "invalid_fingerprint_snapshot"


def _digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def schema_fingerprint(schema: pa.Schema) -> str:
    """Fingerprint the serialized Arrow schema, including metadata and types."""
    if type(schema) is not pa.Schema:
        raise TypeError(_SCHEMA_ERROR)
    return _digest(schema.serialize().to_pybytes())


def layout_fingerprint(layout: Mapping[str, object]) -> str:
    """Fingerprint a caller-provided exact layout contract canonically."""
    payload = json.dumps(
        layout,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return _digest(payload)


def compare_fingerprints(
    before: Mapping[str, str], after: Mapping[str, str]
) -> dict[str, object]:
    """Report deterministic additions, removals and changed fingerprints."""
    for snapshot in (before, after):
        if any(
            not isinstance(key, str)
            or not key
            or not isinstance(value, str)
            or len(value) != _HASH_LENGTH
            or any(char not in "0123456789abcdef" for char in value)
            for key, value in snapshot.items()
        ):
            raise ValueError(_SNAPSHOT_ERROR)
    changes = []
    for key in sorted(before.keys() | after.keys()):
        if key not in before:
            changes.append({"key": key, "change": "added"})
        elif key not in after:
            changes.append({"key": key, "change": "removed"})
        elif before[key] != after[key]:
            changes.append({"key": key, "change": "changed"})
    return {
        "schema_version": "archive-govt-nz.health-schema-layout-drift/v1",
        "status": "matching" if not changes else "drift",
        "changes": changes,
        "normalization_approval": "not_granted",
    }
