"""Silver Layer: Clean, structured columnar Parquet pipelines with Arrow schemas."""

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
from archive_govt_nz.silver.pipeline import (
    DOMAIN_NORMALIZERS,
    SilverPipeline,
    SilverTransformationResult,
)

__all__ = [
    "DOMAIN_NORMALIZERS",
    "SILVER_ARROW_SCHEMA",
    "CourtsNoticesSilverNormalizer",
    "GazetteSilverNormalizer",
    "HealthSilverNormalizer",
    "LegislationSilverNormalizer",
    "NormalizedSilverRecord",
    "SilverNormalizer",
    "SilverPipeline",
    "SilverTransformationResult",
    "TreasurySilverNormalizer",
]
