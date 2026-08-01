"""Reconcile two metadata-only Ministry of Health discovery receipts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast


def _load(path: Path) -> dict[str, Any]:
    """Load and validate a discovery receipt."""
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("invalid discovery receipt")
    if value.get("schema") != "archive-govt-nz.moh-discovery/v1":
        raise ValueError("invalid discovery receipt")
    return cast("dict[str, Any]", value)


def reconcile(first: dict[str, Any], second: dict[str, Any]) -> dict[str, Any]:
    """Compare dataset inventories without inspecting payloads."""
    a = cast("dict[str, Any]", first["scope"])
    b = cast("dict[str, Any]", second["scope"])
    ids_a = {str(item["id"]): item for item in a["datasets"]}
    ids_b = {str(item["id"]): item for item in b["datasets"]}
    changed = sorted(
        key for key in ids_a.keys() & ids_b.keys() if ids_a[key] != ids_b[key]
    )
    return {
        "schema": "archive-govt-nz.moh-discovery-reconciliation/v1",
        "first_observed_at": first["observed_at"],
        "second_observed_at": second["observed_at"],
        "policy": {
            "metadata_only": True,
            "payload_capture": False,
            "publication": False,
        },
        "counts": {
            "first_datasets": len(ids_a),
            "second_datasets": len(ids_b),
            "first_resources": int(a["resource_count"]),
            "second_resources": int(b["resource_count"]),
            "added_dataset_ids": sorted(ids_b.keys() - ids_a.keys()),
            "removed_dataset_ids": sorted(ids_a.keys() - ids_b.keys()),
            "changed_dataset_ids": changed,
        },
        "stable": not (ids_a.keys() ^ ids_b.keys() or changed),
    }


def main() -> int:
    """Run the reconciliation command."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = reconcile(_load(args.first), _load(args.second))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"output": str(args.output), "stable": result["stable"]}, sort_keys=True
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
