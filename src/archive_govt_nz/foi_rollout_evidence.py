"""Verify that materialized rollout rows point at existing evidence."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


def verify_rollout(rollout_path: Path, evidence_dir: Path) -> dict[str, Any]:
    """Check evidence references and summary counts without inferring coverage."""
    rollout = json.loads(rollout_path.read_text(encoding="utf-8"))
    entities = rollout["entities"]
    sources = rollout["sources"]
    entity_ids = [row["entity_id"] for row in entities]
    source_ids = [row["source_id"] for row in sources]
    missing_evidence = []
    for row in sources:
        reference = row["capture_evidence"]
        if (
            reference != "separate_pilot_receipt_required"
            and not (evidence_dir / reference).is_file()
        ):
            missing_evidence.append(
                {"source_id": row["source_id"], "evidence": reference}
            )
    summary = rollout["summary"]
    calculated = {
        "entities": len(entities),
        "sources": len(sources),
        "entities_requiring_broader_discovery": sum(
            row["broader_discovery_required"] for row in entities
        ),
        "entities_without_named_sources": sum(
            not row["source_ids"] for row in entities
        ),
        "public_raw_complete_countries_verified": sum(
            row["country_complete"] for row in entities
        ),
    }
    duplicate_entities = len(entity_ids) != len(set(entity_ids))
    duplicate_sources = len(source_ids) != len(set(source_ids))
    return {
        "schema_version": "archive-govt-nz.foi-rollout-integrity/v1",
        "rollout": str(rollout_path),
        "duplicate_entity_ids": sorted(
            {value for value in entity_ids if entity_ids.count(value) > 1}
        ),
        "duplicate_source_ids": sorted(
            {value for value in source_ids if source_ids.count(value) > 1}
        ),
        "missing_evidence": missing_evidence,
        "summary_matches": summary == calculated,
        "calculated_summary": calculated,
        "valid": not (
            missing_evidence
            or summary != calculated
            or duplicate_entities
            or duplicate_sources
        ),
    }
