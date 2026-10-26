"""Bronze dispatcher for the two pinned HAIR2024 published-indicator CSVs."""

from __future__ import annotations

import csv
import hashlib
from dataclasses import dataclass
from types import MappingProxyType

from archive_govt_nz.domains.health_appropriations import moh_indicators
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.moh_canonical_projection import (
    PROFILES,
    SOURCE_VINTAGE,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    source_context,
)

SOURCE_SHA256_BY_PROFILE = MappingProxyType(
    {
        "fig27/v1": "c1e7758667b8255e049603de8325d732f34a76e6099e0fe4de6553a36d48e9fc",
        "fig28/v1": "7b9a51643550e3d890f4f341f27346d3466708fe924702ade4a731d1bb6266e4",
    }
)
_MEDIA_TYPE = "text/csv"


@dataclass(frozen=True, slots=True)
class MohIndicatorAdapter:
    """Select one exact source/profile pair and preserve unknown semantics."""

    profile: str
    source_locator: str
    source_vintage: str
    observed_at: str

    def matches_layout(self, bronze: bytes) -> bool:
        """Require the captured source hash and its exact bounded row shape."""
        if (
            self.profile not in PROFILES
            or self.source_vintage != SOURCE_VINTAGE
            or self.source_locator != PROFILES[self.profile]
            or not 0 < len(bronze) <= moh_indicators.MAX_BYTES
            or hashlib.sha256(bronze).hexdigest()
            != SOURCE_SHA256_BY_PROFILE[self.profile]
        ):
            return False
        try:
            moh_indicators._rows(bronze, moh_indicators.PROFILES[self.profile])  # noqa: SLF001
        except ValueError, UnicodeDecodeError, csv.Error, StopIteration:
            return False
        return True

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Emit published values, row accounting and exact field lineage."""
        digest = hashlib.sha256(bronze).hexdigest()
        if digest != source_sha256:
            message = "source_hash_mismatch"
            raise ValueError(message)
        if not self.matches_layout(bronze):
            return preserved_only(
                source_coordinate="bronze:sha256:" + digest,
                reason="unsupported_moh_indicator_source_profile",
            )
        context = source_context(
            digest, self.source_locator, self.source_vintage, self.observed_at
        )
        rows = moh_indicators._rows(  # noqa: SLF001
            bronze, moh_indicators.PROFILES[self.profile]
        )
        facts, lineage, _dispositions = moh_indicators._extract(  # noqa: SLF001
            rows, context, self.profile
        )
        return AdapterOutput(
            records=tuple(dict(row) for row in facts),
            losses=(),
            lineage=tuple(
                FieldLineage(
                    record_id=str(row["record_id"]),
                    field=str(row["field"]),
                    source_coordinate=str(row["source_coordinate"]),
                    raw_value=row["raw_value"],
                    normalized_value=row["normalized_value"],
                    rule=str(row["rule"]),
                )
                for row in lineage
            ),
            layout=moh_indicators.TRANSFORMATION,
        )


def registration(
    *,
    profile: str,
    source_locator: str,
    source_vintage: str,
    observed_at: str,
) -> AdapterRegistration:
    """Register one source-locator-bound HAIR2024 indicator CSV."""
    if profile not in PROFILES or source_locator != PROFILES[profile]:
        message = "unsupported_moh_indicator_source_context"
        raise ValueError(message)
    if source_vintage != SOURCE_VINTAGE:
        message = "unsupported_moh_indicator_source_context"
        raise ValueError(message)
    adapter = MohIndicatorAdapter(profile, source_locator, source_vintage, observed_at)
    return AdapterRegistration(
        adapter_id=f"moh-hair2024-{profile.replace('/', '-')}",
        version="1.0.0",
        media_type=_MEDIA_TYPE,
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
