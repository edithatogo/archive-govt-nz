"""Verify that materialized rollout rows point at existing evidence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _evidence_exists(reference: str, evidence_dir: Path) -> bool:
    if reference == "separate_pilot_receipt_required":
        return True
    relative = Path(reference)
    root = evidence_dir.resolve()
    path = root / relative
    return (
        not relative.is_absolute()
        and ".." not in relative.parts
        and path.resolve().is_relative_to(root)
        and path.is_file()
    )


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
        if not _evidence_exists(reference, evidence_dir):
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
    duplicate_entity_source_links = sorted(
        row["entity_id"]
        for row in entities
        if len(row["source_ids"]) != len(set(row["source_ids"]))
    )
    entity_by_id = {row["entity_id"]: row for row in entities}
    source_by_id = {row["source_id"]: row for row in sources}
    dangling_entity_sources = sorted(
        {
            source_id
            for row in entities
            for source_id in row["source_ids"]
            if source_id not in source_by_id
        }
    )
    unreferenced_sources = sorted(
        set(source_by_id)
        - {source_id for row in entities for source_id in row["source_ids"]}
    )
    cross_entity_sources = sorted(
        {
            source_id
            for source_id, source in source_by_id.items()
            if source.get("entity_id") not in entity_by_id
            or source_id not in entity_by_id[source["entity_id"]].get("source_ids", [])
        }
        | {
            source_id
            for entity in entities
            for source_id in entity["source_ids"]
            if source_id in source_by_id
            and source_by_id[source_id].get("entity_id") != entity["entity_id"]
        }
    )
    return {
        "schema_version": "archive-govt-nz.foi-rollout-integrity/v1",
        "rollout": str(rollout_path),
        "duplicate_entity_ids": sorted(
            {value for value in entity_ids if entity_ids.count(value) > 1}
        ),
        "duplicate_source_ids": sorted(
            {value for value in source_ids if source_ids.count(value) > 1}
        ),
        "dangling_entity_sources": dangling_entity_sources,
        "duplicate_entity_source_links": duplicate_entity_source_links,
        "unreferenced_sources": unreferenced_sources,
        "cross_entity_sources": cross_entity_sources,
        "missing_evidence": missing_evidence,
        "summary_matches": summary == calculated,
        "calculated_summary": calculated,
        "valid": not (
            missing_evidence
            or summary != calculated
            or duplicate_entities
            or duplicate_sources
            or duplicate_entity_source_links
            or dangling_entity_sources
            or unreferenced_sources
            or cross_entity_sources
        ),
    }
