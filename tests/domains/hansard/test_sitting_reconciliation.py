"""One actual sitting may have a daily record and separately catalogued speeches."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
from tools.reconcile_modern_hansard import reconcile


def test_multiple_document_sitting(tmp_path: Path) -> None:
    """Date the sitting by its ID even when a document was edited much later."""
    source = tmp_path / "sample.parquet"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "parliament_document_id": "HansD_20240305_20240305",
                    "document_type": "Hansard - daily",
                    "title": "Tuesday",
                },
                {
                    "parliament_document_id": "HansDeb_20240305_20240306_774",
                    "document_type": "Hansard - debate",
                    "title": "Continued debate",
                },
            ]
        ),
        source,
    )
    result = reconcile(source, [{"date": "2024-03-05"}, {"date": "2024-03-06"}])
    assert [
        (r["matching_documents"], r["daily_documents"]) for r in result["comparisons"]
    ] == [(2, 1), (0, 0)]
    assert json.loads(json.dumps(result))["unresolved_ids"] == []
