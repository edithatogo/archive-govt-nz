"""Vectorized Silver Pipeline: Reads Bronze manifests & CAS, writes canonical Parquet."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.bronze.models import BronzeIngestionManifest
from archive_govt_nz.silver.base import (
    SILVER_ARROW_SCHEMA,
    NormalizedSilverRecord,
    SilverNormalizer,
)
from archive_govt_nz.silver.normalizers import (
    CourtsNoticesSilverNormalizer,
    GazetteSilverNormalizer,
    HealthSilverNormalizer,
    LegislationSilverNormalizer,
    TreasurySilverNormalizer,
)

DOMAIN_NORMALIZERS: dict[str, SilverNormalizer] = {
    "legislation": LegislationSilverNormalizer(),
    "gazette": GazetteSilverNormalizer(),
    "courts": CourtsNoticesSilverNormalizer(),
    "health": HealthSilverNormalizer(),
    "treasury": TreasurySilverNormalizer(),
}


@dataclass(frozen=True, slots=True)
class SilverTransformationResult:
    """Output metrics and path for a completed Silver Parquet transformation."""

    domain: str
    records_transformed: int
    parquet_path: Path
    parquet_bytes: int
    schema_fingerprint: str


class SilverPipeline:
    """Orchestrates transformation of Bronze ingested streams into Silver Parquet."""

    def __init__(self, silver_base_dir: Path | None = None) -> None:
        self.silver_base_dir = silver_base_dir or Path("data/silver")

    def transform_manifest(
        self,
        manifest: BronzeIngestionManifest,
        cas_base_dir: Path,
    ) -> SilverTransformationResult:
        """Transform all records in a Bronze manifest into a Silver Parquet dataset."""
        normalizer = DOMAIN_NORMALIZERS.get(manifest.domain)
        if not normalizer:
            raise ValueError(
                f"No Silver normalizer registered for domain: {manifest.domain}"
            )

        all_silver_records: list[NormalizedSilverRecord] = []

        for record in manifest.records:
            # Locate payload in CAS
            cas_file = cas_base_dir / record.fixity.cas_path
            if cas_file.exists():
                payload_bytes = cas_file.read_bytes()
            else:
                # If CAS file missing, synthesize from custom metadata or empty
                payload_bytes = json.dumps(record.custom_metadata).encode("utf-8")

            normalized = normalizer.normalize_record(record, payload_bytes)
            all_silver_records.extend(normalized)

        # Convert to PyArrow Table with strict schema validation
        dict_records = [r.to_dict() for r in all_silver_records]

        if dict_records:
            pydict: dict[str, list[Any]] = {
                field.name: [] for field in SILVER_ARROW_SCHEMA
            }
            for rec in dict_records:
                for k, v in rec.items():
                    pydict[k].append(v)
            arrow_table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)
        else:
            arrow_table = pa.Table.from_pylist([], schema=SILVER_ARROW_SCHEMA)

        # Write to destination Parquet
        dest_dir = self.silver_base_dir / manifest.domain
        dest_dir.mkdir(parents=True, exist_ok=True)
        parquet_file = dest_dir / "corpus.parquet"

        pq.write_table(
            arrow_table,
            parquet_file,
            compression="zstd",
            use_dictionary=True,
        )

        file_bytes = parquet_file.stat().st_size if parquet_file.exists() else 0
        schema_fingerprint = str(arrow_table.schema)

        return SilverTransformationResult(
            domain=manifest.domain,
            records_transformed=len(all_silver_records),
            parquet_path=parquet_file,
            parquet_bytes=file_bytes,
            schema_fingerprint=schema_fingerprint,
        )
