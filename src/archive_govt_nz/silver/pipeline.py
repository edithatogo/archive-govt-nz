"""Vectorized Silver Pipeline: Reads Bronze manifests & CAS, writes canonical Parquet."""

from __future__ import annotations

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
    if domain == "hathi":
        from archive_govt_nz.domains.hathi.normalizer import (  # noqa: PLC0415
            HathiSilverNormalizer,
        )

        return HathiSilverNormalizer()
    if domain == "medilegal":
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
    ) -> SilverTransformationResult:
        """Read all CAS records in a Bronze manifest and materialize Silver Parquet."""
        domain = manifest.domain
        normalizer = DOMAIN_NORMALIZERS.get(domain)
        if normalizer is None:
            msg = f"No registered Silver normalizer for domain '{domain}'"
            raise ValueError(msg)

        all_silver_records: list[NormalizedSilverRecord] = []
        for record in manifest.records:
            cas_p = Path(record.fixity.cas_path)
            if not cas_p.is_absolute() and cas_base_dir is not None:
                cas_p = cas_base_dir / cas_p

            payload_bytes = cas_p.read_bytes()
            records = normalizer.normalize_record(record, payload_bytes)
            all_silver_records.extend(records)

        pydict: dict[str, list[object]] = {
            name: [getattr(r, name) for r in all_silver_records]
            for name in SILVER_ARROW_SCHEMA.names
        }
        table = pa.Table.from_pydict(pydict, schema=SILVER_ARROW_SCHEMA)

        domain_silver_dir = self.silver_base_dir / domain
        domain_silver_dir.mkdir(parents=True, exist_ok=True)
        parquet_path = domain_silver_dir / "corpus.parquet"

        pq.write_table(table, parquet_path, compression="zstd")

        return SilverTransformationResult(
            domain=domain,
            records_transformed=len(all_silver_records),
            parquet_path=parquet_path,
            parquet_bytes=parquet_path.stat().st_size,
            schema_fingerprint=all_silver_records[0].nz_schema_fingerprint
            if all_silver_records
            else "",
        )
