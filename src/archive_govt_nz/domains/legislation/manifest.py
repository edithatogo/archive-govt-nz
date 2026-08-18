"""Source and transformation manifest compilation for legislation packages."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from archive_govt_nz.domains.legislation.models import LegislationRecord


def build_legislation_manifest(
    records: list[LegislationRecord],
    run_id: str = "",
) -> dict[str, Any]:
    """Compile an immutable source manifest from a set of legislation records."""
    entries = []
    hasher = hashlib.sha256()

    for r in sorted(records, key=lambda x: x.document_id):
        entry = {
            "document_id": r.document_id,
            "work_id": r.work_id,
            "title": r.title,
            "legislation_type": r.legislation_type.value,
            "status": r.status.value,
            "raw_sha256": r.raw_cas_hash_sha256,
            "raw_blake3": r.raw_cas_hash_blake3,
            "byte_size": r.byte_size,
            "canonical_uri": r.canonical_uri,
            "sections_count": len(r.sections),
            "schedules_count": len(r.schedules),
        }
        entries.append(entry)
        hasher.update(json.dumps(entry, sort_keys=True).encode("utf-8"))

    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": "archive-govt-nz.legislation-manifest/v1",
        "generated_at": now_iso,
        "run_id": run_id or f"run-leg-{now_iso}",
        "total_records": len(records),
        "manifest_sha256": hasher.hexdigest(),
        "records": entries,
    }
