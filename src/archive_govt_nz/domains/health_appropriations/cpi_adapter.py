"""Bronze dispatcher adapter for the pinned CPIQ.SE9A CSV layout."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from archive_govt_nz.domains.health_appropriations import cpi
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    LossAccounting,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.context_dimensions import (
    context_source_dimensions,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import source_context

_MEDIA_TYPE = "text/csv"
_HASH_ERROR = "source_hash_mismatch"
_VINTAGE = "2026-Q2"


@dataclass(frozen=True, slots=True)
class CpiAdapter:
    """Extract one reviewed CPI series while accounting for every CSV row."""

    source_locator: str
    source_vintage: str
    observed_at: str

    def matches_layout(self, bronze: bytes) -> bool:
        """Recognize the bounded layout only when its selected series is valid."""
        if (
            self.source_vintage != _VINTAGE
            or len(bronze) > cpi.MAX_BYTES
            or not cpi.is_supported_bronze_layout(bronze)
        ):
            return False
        digest = hashlib.sha256(bronze).hexdigest()
        context = source_context(
            digest, self.source_locator, self.source_vintage, self.observed_at
        )
        try:
            facts, _, _ = cpi.inspect_bronze_payload(bronze, context)
        except ValueError, KeyError, UnicodeDecodeError:
            return False
        return bool(facts)

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Project exact-series facts without changing original bytes."""
        digest = hashlib.sha256(bronze).hexdigest()
        if digest != source_sha256:
            raise ValueError(_HASH_ERROR)
        if not self.matches_layout(bronze):
            return preserved_only(
                source_coordinate="bronze:sha256:" + digest,
                reason="unsupported_cpi_csv_layout",
            )
        context = source_context(
            digest, self.source_locator, self.source_vintage, self.observed_at
        )
        try:
            facts, lineage, dispositions = cpi.inspect_bronze_payload(bronze, context)
        except ValueError, KeyError:
            return preserved_only(
                source_coordinate="bronze:sha256:" + digest,
                reason="unsupported_cpi_series_layout",
            )
        losses = tuple(
            LossAccounting(
                source_coordinate=f"csv:row={row['source_row']}",
                disposition=str(row["disposition"]),
                reason=str(row["reason"]),
            )
            for row in dispositions
            if row["disposition"] != "selected"
        )
        field_lineage = tuple(
            FieldLineage(
                record_id=str(row["record_id"]),
                field=str(row["field"]),
                source_coordinate=str(row["source_coordinate"]),
                raw_value=row["raw_value"],
                normalized_value=row["normalized_value"],
                rule=str(row["rule"]),
            )
            for row in lineage
        )
        dimensions, links = context_source_dimensions(
            tuple(dict(row) for row in facts), field_lineage, family="cpi"
        )
        return AdapterOutput(
            records=tuple(dict(row) for row in facts),
            losses=losses,
            lineage=field_lineage,
            layout=cpi.TRANSFORMATION,
            dimensions=dimensions,
            dimension_links=links,
        )


def cpi_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register only the explicitly supported CPI profile."""
    adapter = CpiAdapter(source_locator, source_vintage, observed_at)
    return AdapterRegistration(
        adapter_id="stats-nz-cpiq-se9a",
        version="1.0.0",
        media_type=_MEDIA_TYPE,
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
