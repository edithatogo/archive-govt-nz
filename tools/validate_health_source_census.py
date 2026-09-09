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
_SHA256_LENGTH = 64


def _validate_inventory_evidence(source_id: str, row: dict[str, object]) -> None:
    """Require fixity and rights evidence for captured inventory items."""
    disposition = row["disposition"]
    if disposition == "captured":
        digest = row.get("object_sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != _SHA256_LENGTH
            or any(char not in "0123456789abcdef" for char in digest)
        ):
            message = f"captured source {source_id} lacks a valid object_sha256"
            raise CensusValidationError(message)
        for field in ("license", "rights_uri"):
            value = row.get(field)
            if not isinstance(value, str) or not value.strip():
                message = f"captured source {source_id} lacks {field} evidence"
                raise CensusValidationError(message)


class CensusValidationError(ValueError):
    """Indicate that a source census violates its validation contract."""


def validate(path: Path) -> dict[str, int]:
    """Validate a source census and return its record and family counts."""
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data.get("records")
    if not isinstance(rows, list) or not rows:
        message = "records must be a non-empty list"
        raise CensusValidationError(message)
    if data.get("record_count") != len(rows):
        message = "record_count must equal the number of records"
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
        _validate_inventory_evidence(source_id, row)
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
