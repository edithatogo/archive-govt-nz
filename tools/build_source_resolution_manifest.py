"""Build a deterministic, fail-closed source resolution inventory."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HTTP_OK = 200
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404


def build_manifest(
    plan: dict[str, Any], probe: dict[str, Any], output: Path
) -> dict[str, Any]:
    """Join capture policy, secure probes, and CKAN probes without fetching data."""
    plan_by_id = {row["resource_id"]: row for row in plan["outcomes"]}
    rows: list[dict[str, Any]] = []
    for row in sorted(probe["results"], key=lambda value: value["resource_id"]):
        rid = row["resource_id"]
        planned = plan_by_id.get(rid, {})
        attempts = row.get("attempts", [])
        ckan = row.get("ckan_api_attempts", [])
        statuses = [
            a.get("status_code") for a in attempts if a.get("status_code") is not None
        ]
        if row.get("state") == "eligible":
            classification = "capture-eligible"
        elif HTTP_FORBIDDEN in statuses:
            classification = "restricted"
        elif HTTP_NOT_FOUND in statuses:
            classification = "unavailable"
        else:
            classification = "tombstone-required"
        rows.append(
            {
                "dataset_id": planned.get("dataset_id"),
                "resource_id": rid,
                "source_url": planned.get("source_url", row.get("source_url")),
                "secure_candidates": row.get("candidates", []),
                "authoritative_alternatives": [],
                "classification": classification,
                "capture_state": row.get("state"),
                "secure_probe": {"attempts": attempts, "reason": row.get("reason")},
                "ckan_api_probe": ckan,
                "metadata_reachable": any(
                    a.get("status_code") == HTTP_OK
                    for a in ckan
                    if "package_show" in a.get("final_url", "")
                ),
                "datastore_reachable": any(
                    a.get("status_code") == HTTP_OK
                    for a in ckan
                    if "datastore_search" in a.get("final_url", "")
                ),
                "policy_decision": planned.get("decision", {}),
                "resolution": "await-authoritative-alternative"
                if classification != "capture-eligible"
                else "capture-after-validation",
            }
        )
    counts = Counter(row["classification"] for row in rows)
    manifest = {
        "schema_version": "archive-govt-nz.source-resolution-manifest/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "body_transfer": False,
        "authoritative_alternatives_policy": "empty-until-publisher-evidence",
        "resource_count": len(rows),
        "classification_counts": dict(sorted(counts.items())),
        "resources": rows,
        "next_action": (
            "request publisher-confirmed replacements; retain tombstones "
            "pending evidence"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    """Build the manifest from local evidence files."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_manifest(
        json.loads(args.plan.read_text()),
        json.loads(args.probe.read_text()),
        args.output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
