"""Common adapters reusing the two reviewed Supplementary summary extractors."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable

from pypdf.errors import PdfReadError

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2024_25 as summary_2024,
)
from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2025_26 as summary_2025,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    LossAccounting,
    preserved_only,
)


@dataclass(frozen=True, slots=True)
class ReviewedSummaryProfile:
    """Closed binding to one existing typed native extraction function."""

    adapter_id: str
    profile: str
    source_sha256: str
    page_count: int
    page: int
    extract: Callable[..., tuple[list[dict[str, Any]], list[dict[str, str]]]]


def _reviewed_profile(
    source_locator: str, source_vintage: str
) -> ReviewedSummaryProfile:
    profiles = {
        summary_2024.VINTAGE: (
            summary_2024,
            "nz-treasury-vote-health-supplementary-2024-25-summary",
        ),
        summary_2025.VINTAGE: (
            summary_2025,
            "nz-treasury-vote-health-supplementary-2025-26-summary",
        ),
    }
    entry = profiles.get(source_vintage)
    if entry is None:
        message = "unsupported_supplementary_summary_context"
        raise ValueError(message)
    module, adapter_id = entry
    if source_locator != module.SOURCE_LOCATOR:
        message = "unsupported_supplementary_summary_context"
        raise ValueError(message)
    return ReviewedSummaryProfile(
        adapter_id,
        module.PROFILE,
        module.SOURCE_SHA256,
        module.PAGE_COUNT,
        module.PAGE,
        module.extract_snapshot,
    )


@dataclass(frozen=True, slots=True)
class SupplementarySummaryAdapter:
    """Exact source context, shared native facts and explicit page accounting."""

    source_locator: str
    source_vintage: str
    observed_at: str

    def _parse(
        self, bronze: bytes
    ) -> tuple[list[dict[str, Any]], list[dict[str, str]]] | None:
        profile = _reviewed_profile(self.source_locator, self.source_vintage)
        try:
            return profile.extract(
                bronze,
                expected_sha256=profile.source_sha256,
                source_locator=self.source_locator,
                source_vintage=self.source_vintage,
                observed_at=self.observed_at,
            )
        except PdfReadError, ValueError, TypeError, KeyError, IndexError, OSError:
            return None

    def matches_layout(self, bronze: bytes) -> bool:
        """Require native byte, edition, page count and parser controls."""
        return self._parse(bronze) is not None

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Preserve native records/field lineage and account for every source page."""
        if hashlib.sha256(bronze).hexdigest() != source_sha256:
            message = "source_hash_mismatch"
            raise ValueError(message)
        parsed = self._parse(bronze)
        if parsed is None:
            return preserved_only(
                source_coordinate="bronze:sha256:" + source_sha256,
                reason="unsupported_supplementary_summary_layout",
            )
        records, native_lineage = parsed
        profile = _reviewed_profile(self.source_locator, self.source_vintage)
        lineage = tuple(
            FieldLineage(
                record_id=row["record_id"],
                field=row["field"],
                source_coordinate=row["source_coordinate"],
                raw_value=row["raw_value"],
                normalized_value=row["normalized_value"],
                rule=row["rule"],
            )
            for row in native_lineage
        )
        losses = tuple(
            LossAccounting(
                source_coordinate=f"pdf:page={page}",
                disposition="partially_normalized"
                if page == profile.page
                else "preserved_only",
                reason="reviewed_summary_rows_only"
                if page == profile.page
                else "outside_reviewed_summary_page",
            )
            for page in range(1, profile.page_count + 1)
        )
        return AdapterOutput(tuple(records), losses, lineage, profile.profile)


def supplementary_summary_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register one exact reviewed edition without source or rights inference."""
    adapter = SupplementarySummaryAdapter(source_locator, source_vintage, observed_at)
    profile = _reviewed_profile(source_locator, source_vintage)
    return AdapterRegistration(
        adapter_id=profile.adapter_id,
        version="v1",
        media_type="application/pdf",
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
