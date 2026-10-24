"""Bronze dispatcher adapter for the pinned Stats NZ GDP Table 1 profile."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from archive_govt_nz.domains.health_appropriations import gdp
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

_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_HASH_ERROR = "source_hash_mismatch"


@dataclass(frozen=True, slots=True)
class GdpAdapter:
    """Extract quarterly actual expenditure-measure GDP without annualizing."""

    source_locator: str
    source_vintage: str
    observed_at: str

    def matches_layout(self, bronze: bytes) -> bool:
        """Recognize only the reviewed release/profile and its bounded layout."""
        if self.source_vintage not in gdp.PROFILE_PERIODS:
            return False
        try:
            facts, _, _ = gdp.inspect_bronze_payload(
                bronze,
                {
                    "source_object_sha256": hashlib.sha256(bronze).hexdigest(),
                    "source_locator": "probe",
                    "source_vintage": self.source_vintage,
                    "observed_at": "2026-01-01T00:00:00+00:00",
                },
            )
        except OSError, ValueError, KeyError, TypeError:
            return False
        return len(facts) == len(gdp.PROFILE_PERIODS[self.source_vintage])

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Return GDP facts with cell lineage and explicit excluded-cell reasons."""
        digest = hashlib.sha256(bronze).hexdigest()
        if digest != source_sha256:
            raise ValueError(_HASH_ERROR)
        if not self.matches_layout(bronze):
            return preserved_only(
                source_coordinate="bronze:sha256:" + digest,
                reason="unsupported_gdp_workbook_layout",
            )
        context = source_context(
            digest, self.source_locator, self.source_vintage, self.observed_at
        )
        facts, lineage, dispositions = gdp.inspect_bronze_payload(bronze, context)
        losses = tuple(
            LossAccounting(
                source_coordinate=str(row["source_coordinate"]),
                disposition=str(row["disposition"]),
                reason=str(row["reason"]),
            )
            for row in dispositions
            if row["disposition"] != "selected"
        )
        links = tuple(
            FieldLineage(
                record_id=str(row["record_id"]),
                field=str(row["field"]),
                source_coordinate=str(row["source_coordinate"]),
                raw_value=None if row["raw_value"] is None else str(row["raw_value"]),
                normalized_value=(
                    None
                    if row["normalized_value"] is None
                    else str(row["normalized_value"])
                ),
                rule=str(row["rule"]),
            )
            for row in lineage
        )
        dimensions, dimension_links = context_source_dimensions(
            tuple(dict(row) for row in facts), links, family="gdp"
        )
        return AdapterOutput(
            records=tuple(dict(row) for row in facts),
            losses=losses,
            lineage=links,
            layout=gdp.TRANSFORMATION,
            dimensions=dimensions,
            dimension_links=dimension_links,
        )


def gdp_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register the explicitly scoped June 2026 GDP workbook."""
    adapter = GdpAdapter(source_locator, source_vintage, observed_at)
    return AdapterRegistration(
        adapter_id="stats-nz-gdp-table1-expenditure-actual",
        version="1.0.0",
        media_type=_MEDIA_TYPE,
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
