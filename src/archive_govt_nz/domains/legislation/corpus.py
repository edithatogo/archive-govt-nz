"""Corpus export, period sharding, and Parquet/JSONL table compilation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.domains.legislation.models import LegislationRecord


def export_corpus_jsonl(
    records: list[LegislationRecord],
    output_path: Path,
) -> int:
    """Export canonical legislation records to a stream JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r.to_dict(), sort_keys=True) + "\n")
    return len(records)


def export_corpus_parquet(
    records: list[LegislationRecord],
    output_path: Path,
) -> int:
    """Export canonical legislation records to Snappy-compressed Parquet table."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dicts = [r.to_dict() for r in records]

    table = pa.Table.from_pylist(dicts)
    pq.write_table(table, output_path, compression="snappy")
    return len(records)
