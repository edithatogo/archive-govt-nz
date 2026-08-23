"""Deterministic health payload eligibility evaluation (fail-closed)."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

OPEN_LICENCE_IDENTIFIERS = frozenset(
    {
        "cc0",
        "cc-by",
        "cc-by-4.0",
        "cc-by-3.0",
        "cc-by-sa",
        "cc-by-sa-4.0",
        "ogl-nz",
        "ogl-nz-3.0",
        "ogl",
        "public-domain",
        "pd",
    }
)

ELIGIBILITY_RECEIPT_SCHEMA = "archive-govt-nz.health-eligibility/v1"


def load_resource_snapshot(snapshot_path: Path) -> list[dict[str, Any]]:
    """Load the recorded decision-required resource snapshot."""
    data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    resources = data.get("resources") if isinstance(data, dict) else data
    if not isinstance(resources, list):
        msg = "resource snapshot must contain a 'resources' array"
        raise TypeError(msg)
    return [r for r in resources if isinstance(r, dict)]


def load_licence_map(map_path: Path | None) -> dict[str, str]:
    """Load an optional dataset_id -> licence_id evidence map."""
    if map_path is None or not map_path.is_file():
        return {}
    data = json.loads(map_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        msg = "licence map must be a JSON object of dataset_id -> licence_id"
        raise TypeError(msg)
    return {str(k): str(v).strip().lower() for k, v in data.items()}


def evaluate_resource(
    resource: dict[str, Any], licence_map: dict[str, str]
) -> tuple[str, str]:
    """Classify one resource; returns (classification, reason)."""
    dataset_id = str(resource.get("dataset_id", "")).strip()
    resource_id = str(resource.get("resource_id", "")).strip()
    if not dataset_id or not resource_id:
        return "decision-required", "identity fields absent from recorded metadata"

    licence = licence_map.get(dataset_id, "").strip().lower()
    if not licence:
        return (
            "decision-required",
            "no licence evidence supplied for dataset",
        )

    if licence in OPEN_LICENCE_IDENTIFIERS:
        url = str(resource.get("url", "")).strip()
        if not url.startswith(("http://", "https://")):
            return "decision-required", "eligible licence but no retrievable URL"
        return "payload-eligible", f"open licence evidence: {licence}"

    return "decision-required", f"non-open licence evidence: {licence}"


def evaluate_all(
    resources: list[dict[str, Any]], licence_map: dict[str, str]
) -> dict[str, Any]:
    """Evaluate every resource and build the eligibility receipt."""
    dispositions: list[dict[str, Any]] = []
    counts = {"payload-eligible": 0, "decision-required": 0}

    for resource in resources:
        classification, reason = evaluate_resource(resource, licence_map)
        counts[classification] += 1
        dispositions.append(
            {
                "dataset_id": resource.get("dataset_id", ""),
                "resource_id": resource.get("resource_id", ""),
                "classification": classification,
                "reason": reason,
            }
        )

    return {
        "schema_version": ELIGIBILITY_RECEIPT_SCHEMA,
        "evaluated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "criteria": {
            "open_licences": sorted(OPEN_LICENCE_IDENTIFIERS),
            "fail_closed_default": True,
        },
        "counts": counts,
        "dispositions": dispositions,
    }


def main() -> int:
    """CLI entrypoint for the eligibility evaluator."""
    parser = argparse.ArgumentParser(
        description="Evaluate health payload eligibility (fail-closed)"
    )
    parser.add_argument(
        "--resource-snapshot",
        type=Path,
        default=Path(
            "conductor/tracks/health_payload_capture_20260802/evidence/"
            "moh-resource-metadata.json"
        ),
    )
    parser.add_argument("--licence-map", type=Path, default=None)
    parser.add_argument(
        "--receipt-path",
        type=Path,
        default=Path("evidence/health/eligibility-receipt.json"),
    )
    args = parser.parse_args()

    try:
        resources = load_resource_snapshot(args.resource_snapshot)
        licence_map = load_licence_map(args.licence_map)
    except (OSError, ValueError, TypeError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    receipt = evaluate_all(resources, licence_map)
    args.receipt_path.parent.mkdir(parents=True, exist_ok=True)
    args.receipt_path.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        "[ELIGIBILITY] "
        f"evaluated={len(resources)} "
        f"eligible={receipt['counts']['payload-eligible']} "
        f"decision-required={receipt['counts']['decision-required']} "
        f"receipt={args.receipt_path}"
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
