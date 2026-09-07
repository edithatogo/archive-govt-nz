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


class CensusValidationError(ValueError):
    """Indicate that a source census violates its validation contract."""


def validate(path: Path) -> dict[str, int]:
    """Validate a source census and return its record and family counts."""
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("records")
    if not isinstance(rows, list) or not rows:
        message = "records must be a non-empty list"
        raise CensusValidationError(message)
    ids: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not row.keys() >= REQUIRED:
            message = f"record {index} lacks required fields"
            raise CensusValidationError(message)
        source_id = row["source_id"]
        if not isinstance(source_id, str) or not source_id or source_id in ids:
            message = f"duplicate or invalid source_id at record {index}"
            raise CensusValidationError(message)
        ids.add(source_id)
        if row["disposition"] not in ALLOWED:
            message = f"record {source_id} has invalid disposition"
            raise CensusValidationError(message)
        if not isinstance(row["reason"], str) or not row["reason"].strip():
            message = f"record {source_id} lacks disposition evidence"
            raise CensusValidationError(message)
    return {"records": len(rows), "families": len({r["family"] for r in rows})}


def main() -> int:
    """Run census validation from the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("census", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(args.census), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
