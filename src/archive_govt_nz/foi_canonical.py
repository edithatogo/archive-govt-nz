"""Join pinned factual dispositions into a non-executable source catalogue."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from copy import deepcopy
from typing import TYPE_CHECKING, Any

from archive_govt_nz.foi_candidate_cohort import assess_cohort
from archive_govt_nz.foi_catalogue import _origin, catalogue_files
from archive_govt_nz.foi_discovery import build_reviewed_catalogue
from archive_govt_nz.foi_linked_assessment import assess_links
from archive_govt_nz.foi_reconciliation import reconcile_rollout
from archive_govt_nz.foi_year_navigation import assess_navigation

if TYPE_CHECKING:
    from pathlib import Path

GUARDED = "guarded-linked-20260907/"
INPUTS = (
    "country-rollout-20260831.json",
    "rollout-reconciliation.json",
    "candidate-assessment.json",
    "candidate-assessment-complete.json",
    "candidate-observations-remaining-20260907.json",
    "factual-observations-al-bh-20260907.json",
    "candidate-probe-review-correction-20260907.json",
    "linked-foi-provenance-20260907.json",
    "rights-decision-owner-20260905.json",
    GUARDED + "linked-foi-observations-20260907.json",
    GUARDED + "linked-foi-assessment.json",
    GUARDED + "linked-foi-provenance-20260907.json",
    GUARDED + "al-year-navigation-observations.json",
    GUARDED + "al-year-navigation-assessment.json",
)
FACT_FIELDS = (
    "factual_review",
    "source_existence",
    "source_access",
    "foi_scope",
    "interface",
    "capture_adapter_verified",
    "publisher_attribution",
    "access_rights",
    "capture_rights",
    "retention",
    "redistribution",
    "privacy",
    "declared_disposition",
    "publication_approved",
    "schedule_active",
    "hf_target",
    "request_denominator",
    "country_complete",
)


def _require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _rows(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    result = {row[key]: row for row in rows}
    _require(len(result) == len(rows), "duplicate_join_identity")
    return result


def _read(track: Path, name: str) -> bytes:
    path = track / name
    _require(
        not any(p.is_symlink() for p in (path, *path.parents))
        and path.resolve().is_relative_to(track.resolve()),
        "unsafe_join_input",
    )
    return path.read_bytes()


def _inputs(track: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    pins = json.loads(_read(track, "canonical-inputs-20260907.json"))
    _require(
        pins["schema_version"] == "archive-govt-nz.foi-canonical-inputs/v1"
        and set(pins["files"]) == set(INPUTS),
        "canonical_input_set",
    )
    documents = {}
    for name in INPUTS:
        payload = _read(track, name)
        _require(
            hashlib.sha256(payload).hexdigest() == pins["files"][name],
            "canonical_input_drift",
        )
        documents[name] = json.loads(payload)
    return documents, pins


def join_catalogue(
    catalogue: dict[str, Any],
    rollout: dict[str, Any],
    lineage: dict[str, Any],
    candidates: dict[str, Any],
    linked: dict[str, Any],
) -> dict[str, Any]:
    """Join validated inputs; reject incomplete, duplicate and cross-entity rows."""
    result = deepcopy(catalogue)
    seeds = _rows(result["sources"], "id")
    materialized = _rows(rollout["sources"], "source_id")
    receipts = _rows(lineage["sources"], "source_id")
    assessed = _rows(candidates["sources"], "source_id")
    entities = _rows(result["entities"], "id")
    rollout_entities = _rows(rollout["entities"], "entity_id")
    _require(
        set(seeds) <= set(materialized)
        and set(receipts) == set(materialized)
        and set(assessed) == set(materialized) - set(seeds)
        and set(entities) == set(rollout_entities),
        "inexact_canonical_join",
    )
    for source_id, source in materialized.items():
        entity = source["entity_id"]
        _require(
            entity in entities
            and receipts[source_id]["entity_id"] == entity
            and (seeds.get(source_id) or assessed[source_id])["entity_id"] == entity,
            "canonical_entity_mismatch",
        )
    for entity_id, entity in rollout_entities.items():
        expected = sorted(
            key
            for key, source in materialized.items()
            if source["entity_id"] == entity_id
        )
        _require(sorted(entity["source_ids"]) == expected, "entity_source_join")
    linked_rows = _rows(
        [dict(row, id=row["target"]["source_id"]) for row in linked["sources"]], "id"
    )
    for row in linked_rows.values():
        target = row["target"]
        parent = assessed.get(target["parent_source_id"])
        _require(
            parent is not None
            and parent["entity_id"] == target["entity_id"]
            and parent["retained_receipt_sha256"] == target["retained_receipt_sha256"],
            "linked_parent_mismatch",
        )
    for source_id, row in sorted(assessed.items()):
        receipt = receipts[source_id]
        _require(
            all(
                row[key] is False
                for key in (
                    "capture_adapter_verified",
                    "publication_approved",
                    "schedule_active",
                    "country_complete",
                )
            )
            and row["request_denominator"] is None
            and row["hf_target"] is None,
            "candidate_execution_promotion",
        )
        _require(
            receipt["receipt"] is not None
            and receipt["receipt_sha256"] is not None
            and row["retained_receipt"] == receipt["receipt"]
            and row["retained_receipt_sha256"] == receipt["receipt_sha256"],
            "candidate_receipt_join",
        )
        restricted = row["declared_disposition"] in {"restricted", "disallowed"} or (
            row["privacy"] in {"restricted", "disallowed"}
        )
        facts = {key: deepcopy(row[key]) for key in FACT_FIELDS}
        facts["observed_pacing"] = {
            key: deepcopy(row["robots"][key])
            for key in (
                "status",
                "body_sha256",
                "crawl_delay_seconds",
                "rate_limit_verified",
            )
            if key in row["robots"]
        }
        if "bounded_observation" in row:
            facts["observed_pacing"]["robots_policy"] = deepcopy(
                row["bounded_observation"].get("robots_policy")
            )
        facts["observation_times"] = deepcopy(row.get("observation_times", []))
        if "bounded_observation" in row:
            facts["observation_times"] = [
                row["bounded_observation"]["observed_at"],
                row["bounded_observation"]["finished_at"],
            ]
        findings = [
            {
                "source_id": item["target"]["source_id"],
                "source_url": None if restricted else item["target"]["source_url"],
                "finding": item["finding"],
                "outcome": item["observation"]["outcome"],
                "observed_at": item["observation"]["observed_at"],
                "finished_at": item["observation"]["finished_at"],
            }
            for item in sorted(linked_rows.values(), key=lambda item: item["id"])
            if item["target"]["parent_source_id"] == source_id
        ]
        result["sources"].append(
            {
                "id": source_id,
                "entity_id": row["entity_id"],
                "declared_jurisdiction": None,
                "origins": []
                if restricted or row["source_url"] is None
                else [_origin(row["source_url"])],
                "source_url": None if restricted else row["source_url"],
                "hf_repo_id": row["hf_target"],
                "hf_revision": None,
                "hf_observed_at": None,
                "declared_adapter_modes": [],
                "declared_registry_status": "assessed_candidate",
                "disposition": row["declared_disposition"]
                if restricted
                else row["foi_scope"],
                "rights_status": row["redistribution"],
                "privacy_status": row["privacy"],
                "capture_verified": False,
                "raw_publication_verified": False,
                "total_requests": row["request_denominator"],
                "factual_assessment": facts,
                "linked_dispositions": findings,
                "evidence": {
                    "receipt": receipt["receipt"],
                    "sha256": receipt["receipt_sha256"],
                },
                "pacing": {
                    "verified": False,
                    "execution_policy": "not_authorized_by_index",
                },
            }
        )
    result["sources"].sort(key=lambda row: row["id"])
    for entity in result["entities"]:
        members = [row for row in result["sources"] if row["entity_id"] == entity["id"]]
        entity.update(
            source_ids=[row["id"] for row in members],
            known_sources=len(members),
            disposition="bounded_source_dispositions_recorded",
            evidence_basis=(
                "Pinned seeds and dated candidate/linked assessments; "
                "not exhaustive discovery."
            ),
            source_dispositions={row["id"]: row["disposition"] for row in members},
            exhaustive_discovery=False,
        )
    result["schema_version"] = "archive-govt-nz.foi-source-catalogue/v2"
    result["coverage"].update(
        known_sources=len(materialized),
        retained_seed_sources=len(seeds),
        factually_assessed_candidates=len(assessed),
        entities_with_explicit_dispositions=len(entities),
        source_dispositions=dict(
            sorted(Counter(row["disposition"] for row in result["sources"]).items())
        ),
    )
    # Historical state is retained, not recalculated from landing-page structure.
    result["rollout_state"] = deepcopy(rollout)
    return result


def build_canonical_catalogue(seeds: Path, track: Path) -> dict[str, Any]:
    """Reproduce pinned assessments offline before generating the joined index."""
    docs, pins = _inputs(track)
    lineage = reconcile_rollout(seeds, track / INPUTS[0], track)
    _require(lineage == docs["rollout-reconciliation.json"], "lineage_report_drift")
    candidates = assess_cohort(
        track / "candidate-assessment.json",
        track / "candidate-observations-remaining-20260907.json",
    )
    _require(
        candidates == docs["candidate-assessment-complete.json"],
        "candidate_report_drift",
    )
    linked = assess_links(
        track, docs[GUARDED + "linked-foi-observations-20260907.json"]
    )
    _require(
        linked == docs[GUARDED + "linked-foi-assessment.json"], "linked_report_drift"
    )
    raw = docs[GUARDED + "al-year-navigation-observations.json"]
    _require(len(raw["sources"]) == 1, "navigation_cohort_drift")
    navigation = assess_navigation(raw["target"], raw["sources"][0])
    _require(
        navigation == docs[GUARDED + "al-year-navigation-assessment.json"],
        "navigation_report_drift",
    )
    result = join_catalogue(
        build_reviewed_catalogue(seeds), docs[INPUTS[0]], lineage, candidates, linked
    )
    result["year_navigation_assessment"] = deepcopy(navigation)
    result["provenance"]["canonical_join"] = {
        "inputs": pins,
        "scope": "bounded_factual_metadata_not_exhaustive_discovery",
        "transport_compliance": "historical_compliance_not_certified",
        "publication_or_schedule_authority": False,
    }
    return result


def build_source_index(seeds: Path, track: Path) -> dict[str, bytes]:
    """Generate the canonical registry, machine ledger and paired human index."""
    return catalogue_files(build_canonical_catalogue(seeds, track))
