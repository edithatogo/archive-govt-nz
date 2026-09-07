"""Validate pinned bounded catalogue dispositions, never programme completion."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Any

from archive_govt_nz.foi_canonical import build_source_index

if TYPE_CHECKING:
    from pathlib import Path


def validate_canonical_dispositions(seeds: Path, track: Path) -> dict[str, Any]:
    """Replay every canonical input before issuing an offline scoped receipt.

    No caller-supplied catalogue or success flags are accepted. The canonical
    builder validates seed pins, retained receipts, candidate/linked/navigation
    replay and exact entity/source joins. Unknown and blocked outcomes remain
    valid dispositions, not capture or publication evidence.
    """
    files = build_source_index(seeds, track)
    catalogue = json.loads(files["registry.json"])
    return {
        "schema_version": "archive-govt-nz.foi-catalogue-disposition-validation/v1",
        "scope": "catalogue_disposition_validation",
        "status": "passed",
        "catalogue_schema_version": catalogue["schema_version"],
        "seed_provenance": catalogue["provenance"]["seeds"],
        "canonical_inputs": catalogue["provenance"]["canonical_join"]["inputs"],
        "provenance_sha256": hashlib.sha256(
            json.dumps(
                catalogue["provenance"], sort_keys=True, separators=(",", ":")
            ).encode()
        ).hexdigest(),
        "coverage": catalogue["coverage"],
        "files": {
            name: {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
            for name, data in sorted(files.items())
        },
        "separate_gates": {
            "exhaustive_discovery": "not_established",
            "capture_completion": "not_validated",
            "publication": "not_validated",
            "programme_completion": "not_assessed",
            "ac04_acceptance": "parent_audit_required",
        },
    }
