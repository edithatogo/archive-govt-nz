"""Publication, multi-target distribution, and open metadata generation."""

from __future__ import annotations

from archive_govt_nz.distribution.metadata import (
    generate_croissant_metadata,
    generate_dcat_metadata,
    generate_ro_crate_metadata,
)
from archive_govt_nz.distribution.publisher import (
    DistributionPublisher,
    DistributionTarget,
)

__all__ = (
    "DistributionPublisher",
    "DistributionTarget",
    "generate_croissant_metadata",
    "generate_dcat_metadata",
    "generate_ro_crate_metadata",
)
