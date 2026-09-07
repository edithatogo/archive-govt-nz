"""Fail-closed validation for the health appropriations source census."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED = {
    "captured",
    "unchanged",
    "superseded",
    "unavailable",
    "withdrawn",
    "restricted",
    "corrupt",
    "retryable",
    "duplicate",
    "out_of_scope",
}
REQUIRED = {"source_id", "title", "family", "url", "disposition", "reason", "cutoff"}


def validate(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("records")
    if not isinstance(rows, list) or not rows:
        raise ValueError("records must be a non-empty list")
    ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not REQUIRED <= row.keys():
            raise ValueError(f"record {index} lacks required fields")
        source_id = row["source_id"]
        if not isinstance(source_id, str) or not source_id or source_id in ids:
            raise ValueError(f"duplicate or invalid source_id at record {index}")
        ids.add(source_id)
        if row["disposition"] not in ALLOWED:
            raise ValueError(f"record {source_id} has invalid disposition")
        if not isinstance(row["reason"], str) or not row["reason"].strip():
            raise ValueError(f"record {source_id} lacks disposition evidence")
    return {"records": len(rows), "families": len({r["family"] for r in rows})}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("census", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.census), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
