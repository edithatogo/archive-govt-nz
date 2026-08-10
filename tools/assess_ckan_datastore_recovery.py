"""Assess CKAN DataStore fallback evidence without transferring payloads."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HTTP_OK = 200


def assess(probe: dict[str, Any], output: Path) -> dict[str, Any]:
    """Build a receipt for resources with a reachable CKAN DataStore API."""
    resources: list[dict[str, Any]] = []
    for row in sorted(
        probe.get("results", []), key=lambda item: item.get("resource_id", "")
    ):
        attempts = row.get("ckan_api_attempts", [])
        datastore = [
            attempt
            for attempt in attempts
            if "datastore_search" in str(attempt.get("final_url", ""))
            and attempt.get("status_code") == HTTP_OK
        ]
        if not datastore:
            continue
        resources.append(
            {
                "resource_id": row["resource_id"],
                "source_url": row.get("source_url"),
                "datastore_candidates": [a["final_url"] for a in datastore],
                "observed_status": "200",
                "payload_transfer": False,
                "next_step": (
                    "bounded_datastore_capture_after_format_and_rights_validation"
                ),
            }
        )
    receipt = {
        "schema_version": "archive-govt-nz.ckan-datastore-recovery/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "probe_source": "build/live/secure-source-probe-ckan-20260801.json",
        "body_transfer": False,
        "policy": (
            "DataStore API evidence is a fallback candidate, "
            "not automatic source promotion"
        ),
        "resource_count": len(resources),
        "counts": dict(Counter({"reachable_datastore": len(resources)})),
        "resources": resources,
        "limitations": [
            (
                "The receipt proves API reachability only; it does not prove "
                "complete rows or rights."
            ),
            (
                "A separate bounded API capture must paginate, hash, and "
                "preserve raw JSON responses."
            ),
            "Resources without a 200 DataStore probe remain tombstoned or restricted.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> int:
    """Build a DataStore recovery receipt from a probe receipt."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assess(json.loads(args.probe.read_text(encoding="utf-8")), args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
