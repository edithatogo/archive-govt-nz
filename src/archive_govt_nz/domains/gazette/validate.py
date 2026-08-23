"""Validation rules and structural assertions for gazette records."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

_HASH_REGEX = re.compile(r"^[0-9a-f]{64}$")
_MIN_YEAR = 1840
_MAX_YEAR = 2100
_SCHEMA_VERSION = "archive-govt-nz.gazette/v1"


def _validate_identity_fields(record: dict[str, Any], errors: list[str]) -> None:
    """Validate required identity and classification fields."""
    if not str(record.get("notice_id", "")).strip():
        errors.append("notice_id must not be empty")

    if not str(record.get("issue_number", "")).strip():
        errors.append("issue_number must not be empty")

    if not str(record.get("title", "")).strip():
        errors.append("title must not be empty")

    if record.get("schema_version") != _SCHEMA_VERSION:
        errors.append(f"schema_version must be '{_SCHEMA_VERSION}'")


def _validate_year(record: dict[str, Any], errors: list[str]) -> None:
    """Validate the gazette year bounds and type."""
    year = record.get("year")
    if not isinstance(year, int) or isinstance(year, bool):
        errors.append("year must be an integer")
    elif not _MIN_YEAR <= year <= _MAX_YEAR:
        errors.append(f"year must be between {_MIN_YEAR} and {_MAX_YEAR}")


def _validate_fixity_and_uri(record: dict[str, Any], errors: list[str]) -> None:
    """Validate hash fixity and canonical URI scheme."""
    if not _HASH_REGEX.match(str(record.get("raw_cas_hash_sha256", ""))):
        errors.append("raw_cas_hash_sha256 must be a valid 64-character hex hash")

    canonical_uri = str(record.get("canonical_uri", ""))
    if not canonical_uri.startswith(("http://", "https://")):
        errors.append("canonical_uri must be a valid HTTP or HTTPS URI")


def _validate_retrieval_chronology(record: dict[str, Any], errors: list[str]) -> None:
    """Validate retrieval timestamp format and chronology."""
    retrieval_ts = str(record.get("retrieval_timestamp", ""))
    normalised = (
        f"{retrieval_ts[:-1]}+00:00" if retrieval_ts.endswith("Z") else retrieval_ts
    )
    try:
        retrieved = datetime.fromisoformat(normalised)
    except ValueError:
        errors.append("retrieval_timestamp must be an ISO-8601 date-time")
    else:
        if retrieved > datetime.now(tz=UTC):
            errors.append("retrieval_timestamp must not be in the future")


def validate_gazette_record(record: dict[str, Any]) -> list[str]:
    """Validate a normalised gazette record dict against schema-consistent rules.

    Returns a list of human-readable findings; an empty list means valid.
    """
    errors: list[str] = []
    _validate_identity_fields(record, errors)
    _validate_year(record, errors)
    _validate_fixity_and_uri(record, errors)
    _validate_retrieval_chronology(record, errors)
    return errors
