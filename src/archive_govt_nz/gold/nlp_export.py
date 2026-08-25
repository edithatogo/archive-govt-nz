"""Export contracts and streaming adapters for downstream nlp-policy-nz consumption."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pyarrow.parquet as pq

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class NLPExportBatch:
    """Metadata descriptor for an exported NLP corpus batch."""

    domain: str
    record_count: int
    export_path: Path
    schema_version: str = "archive-govt-nz.nlp-export/v1"


class NLPExportService:
    """Generates clean, pre-structured Parquet feeds for nlp-policy-nz."""

    @staticmethod
    def export_domain_for_nlp(
        silver_parquet_path: Path,
        output_dir: Path,
        *,
        domain_name: str,
        text_column: str = "text_content",
        urn_column: str = "nz_canonical_urn",
    ) -> NLPExportBatch:
        """Export normalized text and URN identifiers for NLP analysis."""
        output_dir.mkdir(parents=True, exist_ok=True)
        table = pq.read_table(silver_parquet_path)

        cols = [
            c
            for c in [urn_column, text_column, "domain", "source_observed_at"]
            if c in table.column_names
        ]
        nlp_table = table.select(cols)

        out_file = output_dir / f"{domain_name}_nlp_corpus.parquet"
        pq.write_table(nlp_table, out_file, compression="zstd")

        return NLPExportBatch(
            domain=domain_name,
            record_count=nlp_table.num_rows,
            export_path=out_file,
        )

    @classmethod
    def export_gazette_notices(
        cls, silver_parquet: Path, output_dir: Path
    ) -> NLPExportBatch:
        """Export Gazette notices for regulatory & commercial NLP extraction."""
        return cls.export_domain_for_nlp(
            silver_parquet, output_dir, domain_name="gazette"
        )

    @classmethod
    def export_hansard_debates(
        cls, silver_parquet: Path, output_dir: Path
    ) -> NLPExportBatch:
        """Export Hansard parliamentary speeches for discourse modeling."""
        return cls.export_domain_for_nlp(
            silver_parquet, output_dir, domain_name="hansard"
        )

    @classmethod
    def export_medilegal_cases(
        cls, silver_parquet: Path, output_dir: Path
    ) -> NLPExportBatch:
        """Export Medico-Legal tribunal decisions for legal taxonomy analysis."""
        return cls.export_domain_for_nlp(
            silver_parquet, output_dir, domain_name="cases_medilegal"
        )
