"""Bronze dispatcher adapter for the exact DPE056AA annual export."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal

from archive_govt_nz.domains.health_appropriations import population_annual_export
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.context_dimensions import (
    context_source_dimensions,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import source_context

_MEDIA_TYPE = "text/csv"
_HASH_ERROR = "source_hash_mismatch"
_POPULATION_ERROR = "unsupported_population_export_layout"
_VINTAGE = "2026-08-18"


@dataclass(frozen=True, slots=True)
class PopulationAnnualAdapter:
    """Emit source-faithful mean-year population context, without denominator use."""

    source_locator: str
    source_vintage: str
    observed_at: str

    def matches_layout(self, bronze: bytes) -> bool:
        """Probe only the exact bounded Stats NZ export profile."""
        if (
            self.source_vintage != _VINTAGE
            or not 0 < len(bronze) <= population_annual_export.MAX_BYTES
        ):
            return False
        try:
            population_annual_export.inspect_export(
                bronze,
                transport=population_annual_export.ExportTransport(
                    None, None, hashlib.sha256(bronze).hexdigest()
                ),
            )
        except ValueError:
            return False
        return True

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Return all annual observations and their year/value source links."""
        digest = hashlib.sha256(bronze).hexdigest()
        if digest != source_sha256:
            raise ValueError(_HASH_ERROR)
        if not self.matches_layout(bronze):
            return preserved_only(
                source_coordinate="bronze:sha256:" + digest,
                reason=_POPULATION_ERROR,
            )
        context = source_context(
            digest, self.source_locator, self.source_vintage, self.observed_at
        )
        inspection = population_annual_export.inspect_export(
            bronze,
            transport=population_annual_export.ExportTransport(None, None, digest),
        )
        records = []
        lineage = []
        for item in inspection["facts"]:
            year = int(item["reference_period"][2:])
            record_id = str(item["record_id"])
            amount = None if item["amount"] is None else Decimal(item["amount"])
            records.append(
                {
                    **context,
                    **item,
                    "period_token": item["reference_period"],
                    "amount": amount,
                    "series_id": (
                        "DPE056AA:Mean year ended:Total:Total All Ages:Annual-Jun"
                    ),
                    "geography": "New Zealand",
                    "denominator_selected": False,
                    "rights_state": "not_evaluated",
                }
            )
            for field, coordinate, raw, normalized, rule in (
                (
                    "period_token",
                    f"csv:row={item['source_row']};column=year",
                    str(year),
                    str(item["reference_period"]),
                    "population-annual-reference-period/v1",
                ),
                (
                    "amount",
                    f"csv:row={item['source_row']};column=value",
                    str(item["value_token"]),
                    str(amount) if amount is not None else str(item["value_token"]),
                    "population-annual-value-token/v1",
                ),
                (
                    "status",
                    f"csv:row={item['source_row']};column=status",
                    str(item["status"] or ""),
                    str(item["status"] or ""),
                    "population-annual-status-preserved/v1",
                ),
            ):
                lineage.append(
                    FieldLineage(
                        record_id=record_id,
                        field=field,
                        source_coordinate=coordinate,
                        raw_value=raw,
                        normalized_value=normalized,
                        rule=rule,
                    )
                )
        dimensions, links = context_source_dimensions(
            tuple(records), tuple(lineage), family="population"
        )
        return AdapterOutput(
            records=tuple(records),
            losses=(),
            lineage=tuple(lineage),
            layout="stats-nz-population-annual-mean-context/v1",
            dimensions=dimensions,
            dimension_links=links,
        )


def population_annual_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register the exact annual mean DPE056AA source profile."""
    adapter = PopulationAnnualAdapter(source_locator, source_vintage, observed_at)
    return AdapterRegistration(
        adapter_id="stats-nz-dpe056aa-annual-mean",
        version="1.0.0",
        media_type=_MEDIA_TYPE,
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
