"""Explicit, fail-closed dispatch from immutable Bronze bytes to adapters."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Literal
from zipfile import BadZipFile

from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    HealthAdapter,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.formats import inventory_workbook

if TYPE_CHECKING:
    from collections.abc import Callable

MediaType = str

_MEDIA_TYPES = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/csv",
        "application/pdf",
        "application/vnd.sqlite3",
    }
)
_SQLITE = b"SQLite format 3\x00"


@dataclass(frozen=True, slots=True)
class AdapterRegistration:
    """An explicit source/layout adapter binding, never a guessed mapping."""

    adapter_id: str
    version: str
    media_type: MediaType
    adapter: HealthAdapter
    layout_probe: Callable[[bytes], bool] | None = None


@dataclass(frozen=True, slots=True)
class AdapterSelection:
    """Auditable decision binding the selected adapter to exact Bronze bytes."""

    schema_version: str
    source_sha256: str
    declared_media_type: str
    detected_media_type: str | None
    adapter_id: str | None
    adapter_version: str | None
    status: Literal["selected", "preserved_only"]
    reason: str | None
    considered_adapter_ids: tuple[str, ...] = ()
    matched_adapter_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DispatchResult:
    """Adapter output paired with the decision that selected it."""

    selection: AdapterSelection
    output: AdapterOutput


def _detect(payload: bytes, declared: str) -> str | None:
    detected: str | None = None
    if payload.startswith(b"PK\x03\x04"):
        try:
            inventory_workbook(BytesIO(payload))
        except BadZipFile, OSError, ValueError, KeyError, TypeError, EOFError:
            detected = None
        else:
            detected = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    elif payload.startswith(b"%PDF-"):
        detected = "application/pdf"
    elif payload.startswith(_SQLITE):
        detected = "application/vnd.sqlite3"
    elif declared == "text/csv":
        try:
            text = payload.decode("utf-8-sig", errors="strict")
        except UnicodeDecodeError:
            detected = None
        else:
            if "\x00" not in text:
                detected = "text/csv"
    return detected


def _validate_inputs(
    bronze: bytes, source_sha256: str, registrations: tuple[AdapterRegistration, ...]
) -> str:
    if type(bronze) is not bytes:
        message = "bronze_bytes_required"
        raise TypeError(message)
    if re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None:
        message = "invalid_source_sha256"
        raise ValueError(message)
    actual = hashlib.sha256(bronze).hexdigest()
    if actual != source_sha256:
        message = "source_hash_mismatch"
        raise ValueError(message)
    if type(registrations) is not tuple:
        message = "registrations_tuple_required"
        raise TypeError(message)
    ids: set[str] = set()
    for item in registrations:
        if type(item) is not AdapterRegistration:
            message = "invalid_adapter_registration"
            raise TypeError(message)
        if (
            not item.adapter_id.strip()
            or not item.version.strip()
            or item.media_type not in _MEDIA_TYPES
            or item.adapter_id in ids
            or (item.layout_probe is not None and not callable(item.layout_probe))
        ):
            message = "invalid_adapter_registration"
            raise ValueError(message)
        ids.add(item.adapter_id)
    return actual


def _select_adapter(
    declared: str,
    detected: str | None,
    payload: bytes,
    registrations: tuple[AdapterRegistration, ...],
) -> tuple[
    AdapterRegistration | None,
    str | None,
    tuple[str, ...],
    tuple[str, ...],
]:
    if detected is None:
        return None, "unrecognized_or_invalid_payload", (), ()
    if detected != declared:
        return None, "declared_media_type_mismatch", (), ()
    candidates = sorted(
        (row for row in registrations if row.media_type == detected),
        key=lambda row: row.adapter_id,
    )
    if not candidates:
        return None, "no_registered_adapter", (), ()
    considered = tuple(row.adapter_id for row in candidates)
    if len(candidates) == 1:
        candidate = candidates[0]
        if candidate.layout_probe is None:
            return candidate, None, considered, ()
    elif any(row.layout_probe is None for row in candidates):
        return None, "adapter_selection_ambiguous", considered, ()
    return _probe_candidates(candidates, payload, considered)


def _probe_candidates(
    candidates: list[AdapterRegistration],
    payload: bytes,
    considered: tuple[str, ...],
) -> tuple[
    AdapterRegistration | None,
    str | None,
    tuple[str, ...],
    tuple[str, ...],
]:
    matches: list[AdapterRegistration] = []
    for candidate in candidates:
        if candidate.layout_probe is None:
            return None, "adapter_selection_ambiguous", considered, ()
        probe_result = candidate.layout_probe(payload)
        if type(probe_result) is not bool:
            message = "invalid_layout_probe_result"
            raise TypeError(message)
        if probe_result:
            matches.append(candidate)
    matched_ids = tuple(row.adapter_id for row in matches)
    if not matches:
        return None, "no_matching_layout", considered, matched_ids
    if len(matches) != 1:
        return None, "adapter_selection_ambiguous", considered, matched_ids
    return matches[0], None, considered, matched_ids


def dispatch_bronze(
    bronze: bytes,
    *,
    source_sha256: str,
    media_type: str,
    registrations: tuple[AdapterRegistration, ...],
) -> DispatchResult:
    """Run only an explicitly registered adapter matching verified bytes.

    A missing handler, malformed media type, unrecognized payload, or type
    mismatch yields a located ``preserved_only`` disposition. This router does
    not interpret CSV dialects, workbook layouts, PDF tables, or SQLite facts.
    Those semantics belong to the registered adapter and its own contracts.
    """
    actual = _validate_inputs(bronze, source_sha256, registrations)
    detected = _detect(bronze, media_type) if media_type in _MEDIA_TYPES else None
    selected, reason, considered, matched = _select_adapter(
        media_type, detected, bronze, registrations
    )

    if selected is None:
        output = preserved_only(
            source_coordinate="bronze:sha256:" + actual,
            reason=reason or "no_registered_adapter",
        )
        selection = AdapterSelection(
            "archive-govt-nz.health-adapter-selection/v1",
            actual,
            media_type,
            detected,
            None,
            None,
            "preserved_only",
            reason,
            considered,
            matched,
        )
        return DispatchResult(selection, output)

    output = selected.adapter.extract(bronze, source_sha256=actual)
    if type(output) is not AdapterOutput:
        message = "invalid_adapter_output"
        raise TypeError(message)
    selection = AdapterSelection(
        "archive-govt-nz.health-adapter-selection/v1",
        actual,
        media_type,
        detected,
        selected.adapter_id,
        selected.version,
        "selected",
        None,
        considered,
        matched,
    )
    return DispatchResult(selection, output)
