"""Explicit common adapters for the two reviewed forecast successor summaries."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from zipfile import BadZipFile

from archive_govt_nz.domains.health_appropriations import forecast
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    LossAccounting,
    preserved_only,
)

_PROFILES = {
    "befu-2026/v1": "nz-treasury-befu-2026-health-summary",
    "hyefu-2025/v1": "nz-treasury-hyefu-2025-health-summary",
}


@dataclass(frozen=True, slots=True)
class ForecastHealthAdapter:
    """Select an exact versioned layout; a selected result may retain rejections."""

    profile: str
    source_locator: str
    source_vintage: str
    observed_at: str

    def _parse(self, bronze: bytes) -> forecast.ForecastExtraction | None:
        if (
            self.profile not in _PROFILES
            or not 0 < len(bronze) <= forecast.MAX_SOURCE_BYTES
        ):
            return None
        try:
            return forecast.parse_forecast_snapshot(
                bronze,
                expected_sha256=hashlib.sha256(bronze).hexdigest(),
                profile=self.profile,
                observed_at=self.observed_at,
                source_vintage=self.source_vintage,
                source_locator=self.source_locator,
            )
        except BadZipFile, KeyError, OSError, TypeError, ValueError:
            return None

    def matches_layout(self, bronze: bytes) -> bool:
        """Require the existing exact successor sheet/coordinate/year/type guards."""
        return self._parse(bronze) is not None

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Retain native facts/lineage and all non-normalized cell/sheet inputs."""
        if hashlib.sha256(bronze).hexdigest() != source_sha256:
            message = "source_hash_mismatch"
            raise ValueError(message)
        parsed = self._parse(bronze)
        if parsed is None:
            return preserved_only(
                source_coordinate="bronze:sha256:" + source_sha256,
                reason="unsupported_forecast_summary_layout",
            )
        lineage = tuple(
            FieldLineage(
                record_id=str(row["record_id"]),
                field=str(row["field"]),
                source_coordinate=str(row["source_coordinate"]),
                raw_value=None if row["raw_value"] is None else str(row["raw_value"]),
                normalized_value=None
                if row["normalized_value"] is None
                else str(row["normalized_value"]),
                rule=str(row["rule"]),
            )
            for row in parsed.lineage
        )
        # Context also remains accounted when its amount was rejected and no fact
        # (and therefore no field lineage) could be emitted for that column.
        losses = tuple(
            LossAccounting(
                str(row["source_coordinate"]),
                str(row["disposition"]),
                str(row["reason"]),
            )
            for row in parsed.dispositions
            if row["disposition"] != "normalized"
        ) + tuple(
            LossAccounting("worksheet:" + row["sheet"], "preserved_only", row["reason"])
            for row in parsed.excluded_sheets
        )
        return AdapterOutput(
            records=tuple(
                {name: row.get(name) for name in forecast.SILVER_SCHEMA.names}
                for row in parsed.facts
            ),
            losses=losses,
            lineage=lineage,
            layout=self.profile,
        )


def forecast_health_registration(
    *,
    profile: str,
    source_locator: str,
    source_vintage: str,
    observed_at: str,
) -> AdapterRegistration:
    """Register a named successor only; do not introduce generic legacy matches."""
    adapter_id = _PROFILES.get(profile)
    if adapter_id is None:
        message = "unsupported_common_forecast_profile"
        raise ValueError(message)
    adapter = ForecastHealthAdapter(
        profile, source_locator, source_vintage, observed_at
    )
    return AdapterRegistration(
        adapter_id,
        "1",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        adapter,
        adapter.matches_layout,
    )
