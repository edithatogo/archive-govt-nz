"""Plan every registered entity without turning discovery into source activation."""

from __future__ import annotations

import hashlib
import json
from typing import Any

INSTITUTIONAL_CANDIDATES = frozenset({"ca-federal-atip", "us-federal-foia"})


def build_rollout(catalogue: dict[str, Any]) -> dict[str, Any]:
    """Project a trusted reviewed catalogue into a non-executable work ledger.

    Candidate grouping is planning only. No caller-supplied status can enable
    capture, publication, or country completion through this projection.
    Institutional group membership concerns statistical subsets, not all
    records exposed by the named portal.
    """
    sources = []
    for source in sorted(catalogue["sources"], key=lambda row: row["id"]):
        restricted = source["rights_status"] == "restricted"
        institutional = source["id"] in INSTITUTIONAL_CANDIDATES
        group = (
            "restricted_or_unclear"
            if restricted
            else "institutional_open_data"
            if institutional
            else "mixed_correspondence"
        )
        sources.append(
            {
                "source_id": source["id"],
                "entity_id": source["entity_id"],
                "publication_group": group,
                "group_is_candidate_only": True,
                "next_action": (
                    "retain_restriction_review"
                    if restricted
                    else "verify_bounded_statistical_subset"
                    if institutional
                    else "assess_adapter_and_separate_content_rights"
                ),
                "source_denominator": None,
                "schedule_active": False,
                "publication_approved": False,
                "capture_evidence": "separate_pilot_receipt_required",
            }
        )
    entities = [
        {
            "entity_id": entity["id"],
            "source_ids": sorted(entity["source_ids"]),
            "next_action": (
                "review_named_sources_and_discover_gaps"
                if entity["source_ids"]
                else "discover_official_and_civic_sources"
            ),
            "broader_discovery_required": True,
            "country_denominator": None,
            "country_complete": False,
        }
        for entity in sorted(catalogue["entities"], key=lambda row: row["id"])
    ]
    return {
        "schema_version": "archive-govt-nz.foi-rollout/v1",
        "catalogue_sha256": hashlib.sha256(
            json.dumps(catalogue, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "scope": "planning_only_not_capture_or_publication_evidence",
        "entities": entities,
        "sources": sources,
        "summary": {
            "entities": len(entities),
            "sources": len(sources),
            "entities_requiring_broader_discovery": len(entities),
            "entities_without_named_sources": sum(
                not row["source_ids"] for row in entities
            ),
            "public_raw_complete_countries_verified": 0,
        },
    }
