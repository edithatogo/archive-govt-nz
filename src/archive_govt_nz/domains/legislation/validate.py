"""Validation rules and structural assertions for legislation records."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from archive_govt_nz.domains.legislation.models import LegislationRecord

_HASH_REGEX = re.compile(r"^[0-9a-f]{64}$")


def validate_legislation_record(record: LegislationRecord) -> list[str]:
    """Validate record integrity against schema and domain consistency rules."""
    errors: list[str] = []

    if not record.document_id.strip():
        errors.append("document_id must not be empty")

    if not record.work_id.strip():
        errors.append("work_id must not be empty")

    if not record.title.strip():
        errors.append("title must not be empty")

    if not _HASH_REGEX.match(record.raw_cas_hash_sha256):
        errors.append("raw_cas_hash_sha256 must be a valid 64-character hex hash")

    if not _HASH_REGEX.match(record.raw_cas_hash_blake3):
        errors.append("raw_cas_hash_blake3 must be a valid 64-character hex hash")

    if not (
        record.canonical_uri.startswith("http://")
        or record.canonical_uri.startswith("https://")
    ):
        errors.append("canonical_uri must be a valid HTTP or HTTPS URI")

    # Verify section ID uniqueness
    seen_sec_ids = set()
    for sec in record.sections:
        if sec.section_id in seen_sec_ids:
            errors.append(f"duplicate section_id found: {sec.section_id}")
        seen_sec_ids.add(sec.section_id)

    return errors
