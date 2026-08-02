"""Classify Ministry of Health candidates before any payload retrieval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast


def classify(document: dict[str, Any]) -> dict[str, object]:
    """Produce fail-closed dataset classifications from metadata only."""
    scope = cast("dict[str, Any]", document.get("scope", {}))
    datasets = cast("list[dict[str, Any]]", scope.get("datasets", []))
    records = [
        {
            "dataset_id": item.get("id"),
            "title": item.get("title"),
            "resource_count": item.get("resource_count", 0),
            "classification": "decision-required",
            "reason": (
                "resource-level rights, sensitivity, URL, and type evidence absent"
            ),
            "download_authorized": False,
        }
        for item in datasets
    ]
    return {
        "schema": "archive-govt-nz.moh-capture-classification/v1",
        "source_schema": document.get("schema"),
        "source_observed_at": document.get("observed_at"),
        "metadata_only": True,
        "payload_capture": False,
        "publication": False,
        "records": records,
        "counts": {"decision-required": len(records)},
    }


def main() -> int:
    """Read a discovery receipt and write a pre-capture classification."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    document = cast(
        "dict[str, Any]", json.loads(args.input.read_text(encoding="utf-8"))
    )
    result = classify(document)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({"output": str(args.output), "counts": result["counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
