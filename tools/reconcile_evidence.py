"""Reconcile resource and publication evidence without transferring payloads."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

EXPECTED_RESOURCES = 91


def load(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    """Reconcile local resource and publication receipts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    plan = load(root / "evidence/phase-6-treasury-capture-plan.json")
    summary = load(root / "evidence/phase-6-capture-summary.json")
    resolution = load(
        root
        / (
            "conductor/tracks/treasury_archive_mvp_20260731/evidence/"
            "phase-10-source-resolution-manifest.json"
        )
    )
    tombstones = load(root / "evidence/phase-10-tombstone-reprobe.json")
    release = load(
        root
        / (
            "conductor/tracks/treasury_archive_mvp_20260731/evidence/"
            "phase-9-release-reconciliation.json"
        )
    )
    ids = {str(x["resource_id"]) for x in plan["outcomes"]}
    resolved_ids = {str(x["resource_id"]) for x in resolution["resources"]}
    tombstone_ids = {str(x["resource_id"]) for x in tombstones["tombstones"]}
    captured = int(summary["captured"])
    restricted = sum(
        1 for x in resolution["resources"] if x["classification"] == "restricted"
    )
    unavailable = sum(
        1 for x in resolution["resources"] if x["classification"] == "unavailable"
    )
    checks = {
        "discovery_resolution_ids_match": ids == resolved_ids,
        "tombstones_match_unresolved": tombstone_ids
        == {
            x["resource_id"]
            for x in resolution["resources"]
            if x["capture_state"] == "tombstone-required"
        },
        "resource_count": len(ids) == EXPECTED_RESOURCES,
        "capture_summary_closure": captured + restricted + unavailable
        == EXPECTED_RESOURCES,
        "release_reconciled": release["state"] == "reconciled",
    }
    result = {
        "schema_version": "archive-govt-nz.evidence-reconciliation/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": (
            "Treasury resource, tombstone, capture, WARC, and publication evidence"
        ),
        "counts": {
            "discovered": len(ids),
            "resolved": len(resolved_ids),
            "captured": captured,
            "restricted": restricted,
            "unavailable": unavailable,
            "tombstones": len(tombstone_ids),
        },
        "checks": checks,
        "status": "reconciled" if all(checks.values()) else "discrepancy",
        "publication": {
            "release_state": release["state"],
            "zenodo": next(
                (
                    x["detail"]
                    for x in release["checks"]
                    if x["name"] == "zenodo_release"
                ),
                None,
            ),
            "huggingface_revision": next(
                (
                    x["detail"]
                    for x in release["checks"]
                    if x["name"] == "huggingface_revision"
                ),
                None,
            ),
        },
        "limitations": [
            "Payload availability and live WARC coverage remain externally gated; "
            "reconciliation does not assert complete capture."
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Final evidence reconciliation",
        "",
        f"Status: **{result['status']}**",
        "",
        "| Stage | Count |",
        "|---|---:|",
    ]
    counts = cast("dict[str, int]", result["counts"])
    lines.extend(f"| {k} | {v} |" for k, v in counts.items())
    lines += ["", "## Checks", ""]
    lines.extend(f"- `{k}`: {'PASS' if v else 'FAIL'}" for k, v in checks.items())
    lines += [
        "",
        "Live payload and WARC completeness remain explicitly gated; "
        "no external request was sent.",
        "",
    ]
    args.markdown.write_text("\n".join(lines), encoding="utf-8")
    return 0 if result["status"] == "reconciled" else 1


if __name__ == "__main__":
    raise SystemExit(main())
