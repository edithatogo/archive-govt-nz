"""Hash-pinned common Bronze adapter for the 2016/17 Vote Health overview."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from archive_govt_nz.domains.health_appropriations import vote_health_estimates_summary
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    AdapterRegistration,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    AdapterOutput,
    FieldLineage,
    LossAccounting,
    preserved_only,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    identity,
    source_context,
)

_PROFILE = vote_health_estimates_summary.PROFILE_2016_17
_TRANSFORMATION = vote_health_estimates_summary.TRANSFORMATION_2016_17
_VINTAGE = vote_health_estimates_summary.VINTAGE_2016_17
_SOURCE_SHA256 = vote_health_estimates_summary.SOURCE_SHA256_2016_17
_PAGE_COUNT = vote_health_estimates_summary.PAGE_COUNT_2016_17
_FACT_COUNT = 24
_MAX_BYTES = 8 * 1024 * 1024
_ADAPTER_ID = "nz-treasury-vote-health-estimates-2016-17-overview"


@dataclass(frozen=True, slots=True)
class VoteHealthEstimates201617OverviewAdapter:
    """Normalize only the reviewed 2016/17 overview pages; retain every page."""

    source_locator: str
    source_vintage: str
    observed_at: str

    def _rows(self, bronze: bytes) -> list[dict[str, Any]] | None:
        if (
            self.source_vintage != _VINTAGE
            or len(bronze) > _MAX_BYTES
            or hashlib.sha256(bronze).hexdigest() != _SOURCE_SHA256
        ):
            return None
        try:
            reader = PdfReader(BytesIO(bronze), strict=True)
            if reader.is_encrypted or len(reader.pages) != _PAGE_COUNT:
                return None
            texts = [
                reader.pages[index].extract_text(extraction_mode="plain") or ""
                for index in (1, 2)
            ]
            rows = vote_health_estimates_summary.parse_overview_2016_17_pages(texts)
            if len(rows) != _FACT_COUNT:
                return None
            if any(int(row["source_page"]) not in {2, 3} for row in rows):
                return None
        except (
            EOFError,
            IndexError,
            KeyError,
            OSError,
            PdfReadError,
            TypeError,
            ValueError,
        ):
            return None
        else:
            return rows

    def matches_layout(self, bronze: bytes) -> bool:
        """Require the exact vintage, source fixity, page count and parser layout."""
        return self._rows(bronze) is not None

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Emit overview facts, field lineage and a disposition for all pages."""
        actual = hashlib.sha256(bronze).hexdigest()
        if actual != source_sha256:
            message = "source_hash_mismatch"
            raise ValueError(message)
        rows = self._rows(bronze)
        if rows is None:
            return preserved_only(
                source_coordinate="bronze:sha256:" + actual,
                reason="unsupported_vote_health_estimates_2016_17_layout",
            )

        context = source_context(
            actual, self.source_locator, self.source_vintage, self.observed_at
        )
        records: list[dict[str, object]] = []
        lineage: list[FieldLineage] = []
        normalized_pages = {int(row["source_page"]) for row in rows}
        for row in rows:
            page = int(row["source_page"])
            measure = str(row["summary_measure"])
            value = row["value"]
            record_id = identity(_TRANSFORMATION, actual, page, measure)
            records.append(
                {
                    **context,
                    "record_id": record_id,
                    "schema_version": "archive-govt-nz.vote-health-overview/v1",
                    "recordset": "vote_health_appropriation_overview_fact",
                    "source_page": page,
                    "summary_measure": measure,
                    "value": value,
                    "unit": row["unit"],
                    "currency_code": None,
                    "reference_period": row["reference_period"],
                    "rights_state": "not_evaluated",
                    "quality_flags": [
                        "overview_headline_only",
                        "currency_code_not_supplied",
                        "source_reported_in_whole_millions",
                        *(
                            ["source_qualifier_preserved_in_raw_phrase"]
                            if row.get("source_qualifier_preserved")
                            else []
                        ),
                    ],
                    "transformation_id": _TRANSFORMATION,
                    "lineage_id": identity(record_id, "lineage"),
                    "raw_values_json": encode_json(row),
                }
            )
            lineage.append(
                FieldLineage(
                    record_id=record_id,
                    field="value",
                    source_coordinate=f"pdf:page={page};overview:{measure}",
                    raw_value=str(row["raw_token"]),
                    normalized_value=str(value),
                    rule=_TRANSFORMATION,
                )
            )
        losses = tuple(
            LossAccounting(
                source_coordinate=f"pdf:page={page}",
                disposition=(
                    "partially_normalized"
                    if page in normalized_pages
                    else "preserved_only"
                ),
                reason=(
                    "twenty_four_selected_2016_17_overview_statements_only"
                    if page in normalized_pages
                    else "not_reviewed_by_2016_17_overview_profile"
                ),
            )
            for page in range(1, _PAGE_COUNT + 1)
        )
        return AdapterOutput(
            records=tuple(records),
            losses=losses,
            lineage=tuple(lineage),
            layout=_PROFILE,
        )


def vote_health_estimates_2016_17_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register the exact 2016/17 PDF profile with its source-bound layout probe."""
    adapter = VoteHealthEstimates201617OverviewAdapter(
        source_locator, source_vintage, observed_at
    )
    return AdapterRegistration(
        adapter_id=_ADAPTER_ID,
        version="1",
        media_type="application/pdf",
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
