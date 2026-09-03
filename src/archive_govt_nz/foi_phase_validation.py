"""Fail-closed acceptance accounting for the global FOI catalogue phase."""

from __future__ import annotations

from typing import Any, NoReturn


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _unique(rows: list[dict[str, Any]], key: str, reason: str) -> dict[str, Any]:
    indexed = {row[key]: row for row in rows}
    if len(indexed) != len(rows):
        _fail(reason)
    return indexed


def _validate_coverage(
    coverage: dict[str, Any],
    entities: dict[str, Any],
    sources: dict[str, Any],
    jurisdictions: dict[str, Any],
) -> int:
    geographic = sum(row["kind"] != "supranational" for row in entities.values())
    expected = {
        "geographic_entities": geographic,
        "supranational_entities": len(entities) - geographic,
        "known_sources": len(sources),
        "target_regimes": len(jurisdictions),
    }
    if any(coverage.get(key) != value for key, value in expected.items()):
        _fail("coverage_count_mismatch")
    return geographic


def validate_catalogue_phase(catalogue: dict[str, Any]) -> dict[str, Any]:
    """Validate structural accounting without promoting incomplete discovery."""
    entities = _unique(catalogue["entities"], "id", "duplicate_entity")
    sources = _unique(catalogue["sources"], "id", "duplicate_source")
    jurisdictions = _unique(catalogue["jurisdictions"], "id", "duplicate_jurisdiction")
    if any(row["entity_id"] not in entities for row in sources.values()):
        _fail("unknown_source_entity")
    for entity in entities.values():
        expected = sorted(
            source_id
            for source_id, source in sources.items()
            if source["entity_id"] == entity["id"]
        )
        if entity["source_ids"] != expected:
            _fail("entity_source_mismatch")
    if any(row["entity_id"] not in entities for row in jurisdictions.values()):
        _fail("unknown_jurisdiction_entity")

    coverage = catalogue["coverage"]
    geographic = _validate_coverage(coverage, entities, sources, jurisdictions)

    review_rows = (
        catalogue.get("provenance", {}).get("directory_review", {}).get("entities")
    )
    if not isinstance(review_rows, list):
        _fail("directory_review_missing")
    reviews = _unique(review_rows, "entity_id", "duplicate_directory_review")
    if set(reviews) != set(entities):
        _fail("directory_review_incomplete")

    broader = sum(
        row.get("broader_discovery") != "complete" for row in reviews.values()
    )
    complete = sum(
        bool(row.get("complete_verified"))
        for row in entities.values()
        if row["kind"] != "supranational"
    )
    if coverage.get("verified_complete") != complete:
        _fail("completion_evidence_mismatch")

    blockers = []
    if broader:
        blockers.append("broader_discovery_incomplete")
    if complete != geographic:
        blockers.append("country_completion_unverified")
    return {
        "schema_version": "archive-govt-nz.foi-catalogue-phase-validation/v1",
        "status": "passed" if not blockers else "blocked",
        "structural_validation": "passed",
        "phase_acceptance": "satisfied" if not blockers else "not_satisfied",
        "counts": {
            "entities": len(entities),
            "sources": len(sources),
            "jurisdictions": len(jurisdictions),
            "entities_without_named_sources": sum(
                not row["source_ids"] for row in entities.values()
            ),
            "entities_requiring_broader_discovery": broader,
            "countries_verified_complete": complete,
        },
        "blockers": blockers,
    }
