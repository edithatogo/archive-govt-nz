"""Reconcile source-census dispositions from a verified capture manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, cast


def main() -> int:
    """Promote matched observations to captured without hiding unmatched rows."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--census", required=True, type=Path)
    parser.add_argument("--capture-manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    census = json.loads(args.census.read_text(encoding="utf-8"))
    capture = json.loads(args.capture_manifest.read_text(encoding="utf-8"))
    results = {
        row["source_id"]: row
        for row in cast("list[dict[str, Any]]", capture["results"])
    }
    matched = 0
    for row in cast("list[dict[str, Any]]", census["records"]):
        result = results.get(row["source_id"])
        if result is None:
            continue
        matched += 1
        row["disposition"] = result["state"]
        row["reason"] = "bounded capture with fixity and WARC evidence"
        row["object_sha256"] = result["sha256"]
        row["rights_uri"] = result["rights"]["evidence"]
        row["license"] = result["rights"]["license"]
    if matched != len(results):
        error = "capture_result_not_in_census"
        raise ValueError(error)
    census["capture_reconciliation"] = {
        "matched": matched,
        "capture_manifest": args.capture_manifest.name,
    }
    args.output.write_text(
        json.dumps(census, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "passed", "matched": matched}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
