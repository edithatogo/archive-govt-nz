"""Test suite for NLPExportService."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.gold.nlp_export import NLPExportService

if TYPE_CHECKING:
    from pathlib import Path


def test_export_domain_for_nlp(tmp_path: Path) -> None:
    """Verify exporting domain Parquet for nlp-policy-nz consumption."""
    records = {
        "nz_canonical_urn": [
            "urn:nz:gazette:notice:2026-1",
            "urn:nz:gazette:notice:2026-2",
        ],
        "text_content": [
            "Notice of liquidation of ABC Ltd",
            "Notice of appointment of receiver",
        ],
        "domain": ["gazette", "gazette"],
        "source_observed_at": ["2026-08-25T19:00:00Z", "2026-08-25T19:00:00Z"],
        "other_unused_col": [1, 2],
    }
    src_pq = tmp_path / "gazette_silver.parquet"
    pq.write_table(pa.Table.from_pydict(records), src_pq)

    out_dir = tmp_path / "nlp_export"
    batch_gazette = NLPExportService.export_gazette_notices(src_pq, out_dir)
    assert batch_gazette.domain == "gazette"
    assert batch_gazette.record_count == 2
    assert batch_gazette.export_path.exists()

    batch_hansard = NLPExportService.export_hansard_debates(src_pq, out_dir)
    assert batch_hansard.domain == "hansard"

    batch_medilegal = NLPExportService.export_medilegal_cases(src_pq, out_dir)
    assert batch_medilegal.domain == "cases_medilegal"

    exported_table = pq.read_table(batch_gazette.export_path)
    assert exported_table.num_rows == 2
    assert "nz_canonical_urn" in exported_table.column_names
    assert "text_content" in exported_table.column_names
    assert "other_unused_col" not in exported_table.column_names
