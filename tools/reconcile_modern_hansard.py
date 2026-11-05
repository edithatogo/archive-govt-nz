"""Compare dated DocumentsDB IDs with a supplied ledger of official sittings."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

import pyarrow.parquet as pq

DOCUMENT_DATE = re.compile(r"(?:\d+)?Hans(?:Deb|D|S|Q|Y)?_(\d{8})(?:_|$|new)")
DRAFT_DATE = re.compile(r"Draft transcript - (\w+), (\d{1,2} \w+ \d{4})")


def document_date(identifier: str, kind: str, title: str) -> date | None:
    """Prefer the ID date. Recover a malformed draft ID only from its dated title."""
    if match := DOCUMENT_DATE.match(identifier):
        return date.fromisoformat(match[1])
    if kind == "Hansard - draft" and (match := DRAFT_DATE.fullmatch(title)):
        day = datetime.strptime(match[2], "%d %B %Y").date()  # noqa: DTZ007
        if day.strftime("%A") == match[1]:
            return day
    return None


def reconcile(parquet: Path, ledger: list[dict[str, str]]) -> dict:
    """Count documents and daily records separately; retain unmappable IDs."""
    groups = defaultdict(Counter)
    unresolved = []
    identifiers = set()
    for batch in pq.ParquetFile(parquet).iter_batches(
        columns=["parliament_document_id", "document_type", "title"]
    ):
        for row in batch.to_pylist():
            identifier = row["parliament_document_id"]
            if identifier in identifiers:
                msg = "Duplicate Parliament document ID"
                raise ValueError(msg)
            identifiers.add(identifier)
            kind = row["document_type"]
            day = document_date(identifier, kind, row["title"])
            if day is None:
                unresolved.append(identifier)
            else:
                groups[day.isoformat()][kind] += 1
    return {
        "document_rows": len(identifiers),
        "unresolved_ids": unresolved,
        "documents_by_id_date": dict(sorted(groups.items())),
        "comparisons": [
            {
                **entry,
                "matching_documents": sum(groups.get(entry["date"], {}).values()),
                "daily_documents": groups.get(entry["date"], {}).get(
                    "Hansard - daily", 0
                ),
            }
            for entry in ledger
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("parquet", type=Path)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    result = reconcile(args.parquet, json.loads(args.ledger.read_bytes()))
    with args.output.open("x", encoding="utf-8") as output:
        json.dump(result, output, sort_keys=True)
