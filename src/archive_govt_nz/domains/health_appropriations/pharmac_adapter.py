"""Bronze dispatcher adapter for Pharmac's reviewed CPB HTML table."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from archive_govt_nz.domains.health_appropriations import pharmac
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    LossAccounting,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import source_context

_MEDIA_TYPE = "text/html"
_HASH_ERROR = "source_hash_mismatch"
_VINTAGE = "Pharmac-CPB-2026-08-07"


@dataclass(frozen=True, slots=True)
class PharmacBudgetAdapter:
    """Extract only the exact published budget table and context profile."""

    source_locator: str
    source_vintage: str
    observed_at: str

    def matches_layout(self, bronze: bytes) -> bool:
        """Recognize the exact bounded HTML table, rejecting structural drift."""
        if self.source_vintage != _VINTAGE or not 0 < len(bronze) <= pharmac.MAX_BYTES:
            return False
        try:
            parser = pharmac._parse(bronze)  # noqa: SLF001 - reviewed parser contract
            facts, _, _ = pharmac._extract(  # noqa: SLF001
                parser,
                source_context(
                    hashlib.sha256(bronze).hexdigest(),
                    "probe",
                    self.source_vintage,
                    "2026-01-01T00:00:00+00:00",
                ),
            )
        except UnicodeDecodeError, ValueError, TypeError:
            return False
        return len(facts) == pharmac.TABLE_ROWS - 1

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Return literal budget rows with exact table/cell accounting."""
        actual = hashlib.sha256(bronze).hexdigest()
        if actual != source_sha256:
            raise ValueError(_HASH_ERROR)
        if not self.matches_layout(bronze):
            return preserved_only(
                source_coordinate="bronze:sha256:" + actual,
                reason="unsupported_pharmac_budget_html_layout",
            )
        context = source_context(
            actual, self.source_locator, self.source_vintage, self.observed_at
        )
        parser = pharmac._parse(bronze)  # noqa: SLF001 - reviewed parser contract
        facts, lineage, dispositions = pharmac._extract(  # noqa: SLF001
            parser, context
        )
        field_lineage = tuple(
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
        losses = tuple(
            LossAccounting(
                source_coordinate=str(row["source_coordinate"]),
                disposition=str(row["disposition"]),
                reason=str(row["reason"]),
            )
            for row in dispositions
            if row["disposition"] not in ("normalized", "context")
        )
        return AdapterOutput(
            records=tuple(dict(row) for row in facts),
            losses=losses,
            lineage=field_lineage,
            layout=pharmac.TRANSFORMATION,
        )


def pharmac_budget_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register the exact 7 August 2026 CPB table and no other HTML source."""
    adapter = PharmacBudgetAdapter(source_locator, source_vintage, observed_at)
    return AdapterRegistration(
        adapter_id="pharmac-combined-pharmaceutical-budget",
        version="1.0.0",
        media_type=_MEDIA_TYPE,
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
