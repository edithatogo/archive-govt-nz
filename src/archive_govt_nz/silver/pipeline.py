"""Vectorized Silver Pipeline: Reads Bronze manifests & CAS, writes canonical Parquet."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pyarrow as pa
import pyarrow.parquet as pq

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

if TYPE_CHECKING:
    from archive_govt_nz.bronze.models import BronzeIngestionManifest

CORE_NORMALIZERS: Final[dict[str, SilverNormalizer]] = {
    "legislation": LegislationSilverNormalizer(),
    "gazette": GazetteSilverNormalizer(),
    "courts": CourtsNoticesSilverNormalizer(),
    "health": HealthSilverNormalizer(),
    "treasury": TreasurySilverNormalizer(),
}


def get_domain_normalizer(domain: str) -> SilverNormalizer | None:
    """Return the normalizer instance for a domain, dynamically importing extensions."""
    if domain in CORE_NORMALIZERS:
        return CORE_NORMALIZERS[domain]
    if domain == "hansard":
        from archive_govt_nz.domains.hansard.normalizer import (  # noqa: PLC0415
            HansardSilverNormalizer,
        )

        return HansardSilverNormalizer()
    if domain in ("hathi", "hathitrust_historic"):
        from archive_govt_nz.domains.hathi.normalizer import (  # noqa: PLC0415
            HathiSilverNormalizer,
        )

        return HathiSilverNormalizer()
    if domain in ("medilegal", "cases_medilegal"):
        from archive_govt_nz.domains.medilegal.normalizer import (  # noqa: PLC0415
            MedicoLegalSilverNormalizer,
        )

        return MedicoLegalSilverNormalizer()
    return None


class _DomainNormalizersProxy(Mapping[str, SilverNormalizer]):
    """Dict-compatible lookup proxy for all registered domain normalizers."""

    _ALL_DOMAINS: Final[tuple[str, ...]] = (
        "legislation",
        "gazette",
        "courts",
        "health",
        "treasury",
        "hansard",
        "hathi",
        "medilegal",
    )

    def __getitem__(self, key: str) -> SilverNormalizer:
        norm = get_domain_normalizer(key)
        if norm is None:
            raise KeyError(key)
        return norm

    def __iter__(self) -> Iterator[str]:
        return iter(self._ALL_DOMAINS)

    def __len__(self) -> int:
        return len(self._ALL_DOMAINS)


DOMAIN_NORMALIZERS: Final[Mapping[str, SilverNormalizer]] = _DomainNormalizersProxy()


@dataclass(frozen=True, slots=True)
class SilverTransformationResult:
    """Output metrics and path for a completed Silver Parquet transformation."""

    domain: str
    records_transformed: int
    parquet_path: Path
    parquet_bytes: int
    schema_fingerprint: str
    checkpoint_resumed: bool = False


def _load_checkpoint(checkpoint_path: Path, domain: str) -> tuple[int, int, bool]:
    """Read starting index and transformed count from existing checkpoint file."""
    if not checkpoint_path.is_file():
        return 0, 0, False
    try:
        cp_data = json.loads(checkpoint_path.read_text(encoding="utf-8"))
        if cp_data.get("domain") == domain:
            start_index = int(cp_data.get("last_processed_index", -1)) + 1
            total_transformed = int(cp_data.get("records_transformed", 0))
            return start_index, total_transformed, True
    except json.JSONDecodeError, OSError, ValueError:
        pass
    return 0, 0, False


def _save_checkpoint(checkpoint_path: Path, domain: str, idx: int, total: int) -> None:
    """Write current transformation checkpoint to disk."""
    checkpoint_path.write_text(
        json.dumps(
            {
                "domain": domain,
                "last_processed_index": idx,
                "records_transformed": total,
            }
        ),
        encoding="utf-8",
    )


class SilverPipeline:
    """Consumes Bronze ingestion manifests and CAS payloads, producing Silver Parquet."""

    def __init__(self, silver_base_dir: Path | None = None) -> None:
        """Initialize pipeline with target base directory."""
        self.silver_base_dir = silver_base_dir or Path("data/silver")

    def transform_manifest(
        self,
        manifest: BronzeIngestionManifest,
        *,
        cas_base_dir: Path | None = None,
        chunk_size: int = 500,
        max_buffer_bytes: int = 64 * 1024 * 1024,
        resume: bool = True,
    ) -> SilverTransformationResult:
        """Read CAS records from Bronze manifest and stream to Silver Parquet in chunks."""
        domain = manifest.domain
        normalizer = DOMAIN_NORMALIZERS.get(domain)
        if normalizer is None:
            msg = f"No registered Silver normalizer for domain '{domain}'"
            raise ValueError(msg)

        domain_silver_dir = self.silver_base_dir / domain
        domain_silver_dir.mkdir(parents=True, exist_ok=True)
        parquet_path = domain_silver_dir / "corpus.parquet"
        checkpoint_path = domain_silver_dir / ".checkpoint.json"

        start_index, total_transformed, resumed = (
            _load_checkpoint(checkpoint_path, domain) if resume else (0, 0, False)
        )
        first_fingerprint = ""
        current_buffer_bytes = 0

        # Stream in bounded batches using PyArrow ParquetWriter to minimize RAM usage
        with pq.ParquetWriter(
            parquet_path, SILVER_ARROW_SCHEMA, compression="zstd"
        ) as writer:
            current_batch: list[NormalizedSilverRecord] = []
            for idx, record in enumerate(manifest.records):
                if idx < start_index:
                    continue

                cas_p = Path(record.fixity.cas_path)
                if not cas_p.is_absolute() and cas_base_dir is not None:
                    cas_p = cas_base_dir / cas_p

                payload_bytes = cas_p.read_bytes()
                current_buffer_bytes += len(payload_bytes)
                records = normalizer.normalize_record(record, payload_bytes)
                if records and not first_fingerprint:
                    first_fingerprint = records[0].nz_schema_fingerprint

                current_batch.extend(records)
                total_transformed += len(records)

                # Flush on either count threshold or byte threshold
                if (
                    len(current_batch) >= chunk_size
                    or current_buffer_bytes >= max_buffer_bytes
                ):
                    pydict: dict[str, list[object]] = {
                        name: [getattr(r, name) for r in current_batch]
                        for name in SILVER_ARROW_SCHEMA.names
                    }
                    batch_table = pa.Table.from_pydict(
                        pydict, schema=SILVER_ARROW_SCHEMA
                    )
                    writer.write_table(batch_table)
                    current_batch.clear()
                    current_buffer_bytes = 0

                    _save_checkpoint(checkpoint_path, domain, idx, total_transformed)

            if current_batch:
                pydict = {
                    name: [getattr(r, name) for r in current_batch]
                    for name in SILVER_ARROW_SCHEMA.names
                }
                batch_table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)
                writer.write_table(batch_table)
                current_batch.clear()

        # Clean up checkpoint on successful completion
        if checkpoint_path.exists():
            checkpoint_path.unlink()

        return SilverTransformationResult(
            domain=domain,
            records_transformed=total_transformed,
            parquet_path=parquet_path,
            parquet_bytes=parquet_path.stat().st_size,
            schema_fingerprint=first_fingerprint,
            checkpoint_resumed=resumed,
        )
