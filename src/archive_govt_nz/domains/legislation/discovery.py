"""Work identifier discovery, candidate cataloguing, and scope filtering."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from archive_govt_nz.domains.legislation.api import NZLegislationApiClient


def build_work_inventory(
    client: NZLegislationApiClient,
    search_terms: list[str],
    legislation_types: list[str] | None = None,
    max_works: int | None = None,
) -> dict[str, Any]:
    """Discover unique candidate work IDs from search API results."""
    type_filters = legislation_types or [None]
    seen_ids: set[str] = set()
    works: list[dict[str, Any]] = []

    for term in search_terms:
        for leg_type in type_filters:
            for item in client.iter_search_works(
                search_term=term,
                legislation_type=leg_type,
            ):
                work_id = str(item.get("work_id", "")).strip()
                if not work_id or work_id in seen_ids:
                    continue
                seen_ids.add(work_id)
                works.append(
                    {
                        "work_id": work_id,
                        "title": item.get("title", ""),
                        "legislation_type": item.get("legislation_type", "act"),
                        "status": item.get("status", "in_force"),
                        "canonical_uri": item.get("canonical_uri"),
                        "expressions": item.get("expressions"),
                    }
                )
                if max_works and len(works) >= max_works:
                    break
            if max_works and len(works) >= max_works:
                break
        if max_works and len(works) >= max_works:
            break

    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "schema_version": "archive-govt-nz.legislation-discovery/v1",
        "generated_at": now_iso,
        "candidate_works_count": len(works),
        "work_ids": sorted(seen_ids),
        "works": works,
        "coverage_classification": "search_derived_candidates",
        "authoritative_completeness": False,
    }
