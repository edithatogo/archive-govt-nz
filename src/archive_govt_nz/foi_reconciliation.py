"""Reconcile rollout lineage locally without promoting source review or coverage."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from archive_govt_nz.foi_discovery import build_reviewed_catalogue
from archive_govt_nz.foi_rollout import build_rollout
from archive_govt_nz.foi_rollout_evidence import verify_rollout


def _require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _receipt(source: dict[str, Any], evidence_dir: Path) -> dict[str, Any]:
    reference = source["capture_evidence"]
    if reference == "separate_pilot_receipt_required":
        return {
            "receipt": None,
            "receipt_sha256": None,
            "receipt_kind": "pilot_receipt_required",
        }
    # verify_rollout has checked path containment and source association.
    payload = (evidence_dir / reference).read_bytes()
    receipt = json.loads(payload)
    _require(
        receipt.get("source_id") == source["source_id"]
        and receipt.get("entity_id", source["entity_id"]) == source["entity_id"],
        "receipt_identity_changed",
    )
    schema = receipt.get("evidence_schema", receipt.get("schema_version"))
    return {
        "receipt": reference,
        "receipt_sha256": hashlib.sha256(payload).hexdigest(),
        "receipt_kind": (
            "discovery_metadata_only"
            if schema == "archive-govt-nz.source-discovery/v1"
            else "other_source_receipt_not_reverified"
        ),
    }


def reconcile_rollout(
    seeds: Path, rollout_path: Path, evidence_dir: Path
) -> dict[str, Any]:
    """Bind every source to the pinned catalogue or an explicit candidate delta.

    Raises ValueError for integrity, catalogue pin, universe or retained-source
    drift. Receipt hashes bind local bytes only; no receipt assertions are
    accepted as rights, exhaustive discovery, capture or publication evidence.
    """
    catalogue = build_reviewed_catalogue(seeds)
    baseline = build_rollout(catalogue)
    payload = rollout_path.read_bytes()
    rollout = json.loads(payload)
    _require(verify_rollout(rollout_path, evidence_dir)["valid"], "rollout_integrity")
    _require(rollout_path.read_bytes() == payload, "rollout_changed_during_read")
    _require(
        rollout["schema_version"] == baseline["schema_version"]
        and rollout["scope"] == baseline["scope"],
        "rollout_contract_mismatch",
    )
    _require(
        rollout["catalogue_sha256"] == baseline["catalogue_sha256"],
        "catalogue_pin_mismatch",
    )
    entities = {row["entity_id"] for row in rollout["entities"]}
    _require(
        entities == {row["id"] for row in catalogue["entities"]},
        "catalogue_universe_mismatch",
    )
    pinned = {row["id"]: row["entity_id"] for row in catalogue["sources"]}
    materialized = {row["source_id"]: row["entity_id"] for row in rollout["sources"]}
    _require(pinned.items() <= materialized.items(), "catalogue_source_mismatch")
    sources = [
        {
            "source_id": row["source_id"],
            "entity_id": row["entity_id"],
            "lineage": (
                "pinned_catalogue"
                if row["source_id"] in pinned
                else "additional_candidate_not_catalogue_reviewed"
            ),
            "review_credit_granted": False,
            **_receipt(row, evidence_dir),
        }
        for row in sorted(rollout["sources"], key=lambda row: row["source_id"])
    ]
    receipted = sum(row["receipt_sha256"] is not None for row in sources)
    return {
        "schema_version": "archive-govt-nz.foi-rollout-reconciliation/v1",
        "scope": "local_lineage_only_not_review_or_publication_evidence",
        "catalogue_sha256": baseline["catalogue_sha256"],
        "rollout_sha256": hashlib.sha256(payload).hexdigest(),
        "entity_ids": sorted(entities),
        "summary": {
            "entities": len(entities),
            "catalogue_sources": len(pinned),
            "rollout_sources": len(sources),
            "additional_candidates": len(sources) - len(pinned),
            "sources_with_receipt": receipted,
            "sources_without_receipt": len(sources) - receipted,
        },
        "sources": sources,
        "coverage_credit_granted": False,
        "total_requests": None,
        "next_action": (
            "Review additional candidates against source observations, FOI scope, "
            "adapter, rights and pacing requirements before catalogue admission; "
            "continue broader discovery for all entities."
        ),
    }


def reconciliation_files(report: dict[str, Any]) -> dict[str, bytes]:
    """Render paired deterministic local reports from the same machine ledger."""
    summary = report["summary"]
    lines = [
        "# FOI rollout lineage reconciliation",
        "",
        "Local lineage only. No new review, capture or publication credit.",
        "Receipt classification describes local metadata, not verified assertions.",
        "Unknown request totals remain null; broader discovery remains required.",
        "",
        f"Catalogue SHA-256: `{report['catalogue_sha256']}`",
        f"Rollout SHA-256: `{report['rollout_sha256']}`",
        "",
        "| Measure | Count |",
        "| --- | ---: |",
        *(f"| {key} | {value} |" for key, value in summary.items()),
        "",
        report["next_action"],
        "",
        "| Source | Entity | Lineage | Receipt kind | Receipt |",
        "| --- | --- | --- | --- | --- |",
        *(
            f"| {row['source_id']} | {row['entity_id']} | {row['lineage']} | "
            f"{row['receipt_kind']} | {row['receipt'] or 'none'} |"
            for row in report["sources"]
        ),
    ]
    return {
        "rollout-reconciliation.json": (
            json.dumps(report, sort_keys=True, indent=2) + "\n"
        ).encode(),
        "rollout-reconciliation.md": ("\n".join(lines) + "\n").encode(),
    }


def main(argv: list[str] | None = None) -> int:
    """Emit a local report to stdout without writing inputs or contacting sources."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=Path, required=True)
    parser.add_argument("--rollout", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "md"), default="json")
    args = parser.parse_args(argv)
    try:
        report = reconcile_rollout(args.seeds, args.rollout, args.evidence_dir)
    except OSError, ValueError, KeyError, TypeError:
        sys.stderr.write("FOI reconciliation rejected invalid or unavailable inputs.\n")
        return 2
    sys.stdout.write(
        reconciliation_files(report)[f"rollout-reconciliation.{args.format}"].decode()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
