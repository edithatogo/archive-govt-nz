"""Hash-pinned, detail-only Bronze adapter for Vote Health Estimates 2002/03."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from archive_govt_nz.domains.health_appropriations import vote_health
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

_SOURCE_SHA256 = vote_health.DETAIL_2002_03_SHA256
_SOURCE_VINTAGE = vote_health.DETAIL_VINTAGE_2002_03
_SOURCE_PAGES = 44
_DETAIL_START = 15
_DETAIL_END = 41
_DETAIL_FACTS = 27
_MAX_BYTES = 2 * 1024 * 1024
_PROFILE = "vote-health-estimates-2002-03-detail/v1"
_ADAPTER_ID = "nz-treasury-vote-health-estimates-2002-03-detail"


@dataclass(frozen=True, slots=True)
class VoteHealthEstimates2002DetailAdapter:
    """Admit only the pinned Estimates 2002/03 Part B1 six-value rows."""

    source_locator: str
    source_vintage: str
    observed_at: str

    def _rows(self, bronze: bytes) -> list[dict[str, Any]] | None:
        if (
            self.source_vintage != _SOURCE_VINTAGE
            or len(bronze) > _MAX_BYTES
            or hashlib.sha256(bronze).hexdigest() != _SOURCE_SHA256
        ):
            return None
        try:
            reader = PdfReader(BytesIO(bronze), strict=True)
            if reader.is_encrypted or len(reader.pages) != _SOURCE_PAGES:
                return None
            texts = [
                page.extract_text(extraction_mode="plain") or ""
                for page in reader.pages
            ]
            starts = [
                index
                for index, text in enumerate(texts)
                if "Part B1 - Details of Appropriations" in text
                and "(continued)" not in text
            ]
            ends = [index for index, text in enumerate(texts) if "Part E -" in text]
            if starts != [_DETAIL_START] or ends != [_DETAIL_END]:
                return None
            rows: list[dict[str, Any]] = []
            for index in range(_DETAIL_START, _DETAIL_END):
                rows.extend(
                    {"source_page": index + 1, **row}
                    for row in vote_health.parse_detail_page(
                        texts[index], require_heading=False, require_rows=False
                    )
                )
            names = [row["appropriation_name"] for row in rows]
            return (
                rows
                if len(rows) == _DETAIL_FACTS and len(set(names)) == len(names)
                else None
            )
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

    def matches_layout(self, bronze: bytes) -> bool:
        """Require exact source fixity, vintage, page count and table bounds."""
        return self._rows(bronze) is not None

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Return 27 source-faithful rows and explicit page dispositions."""
        actual = hashlib.sha256(bronze).hexdigest()
        if actual != source_sha256:
            message = "source_hash_mismatch"
            raise ValueError(message)
        rows = self._rows(bronze)
        if rows is None:
            return preserved_only(
                source_coordinate="bronze:sha256:" + actual,
                reason="unsupported_vote_health_2002_03_layout",
            )
        context = source_context(
            actual, self.source_locator, self.source_vintage, self.observed_at
        )
        records: list[dict[str, object]] = []
        lineage: list[FieldLineage] = []
        normalized_pages: set[int] = set()
        for row in rows:
            page = int(row["source_page"])
            name = str(row["appropriation_name"])
            tokens = dict(row["tokens"])
            record_id = identity(
                vote_health.DETAIL_2002_03_TRANSFORMATION,
                "detail",
                actual,
                page,
                name,
            )
            records.append(
                {
                    **context,
                    "record_id": record_id,
                    "schema_version": "archive-govt-nz.vote-health-detail/v1",
                    "recordset": "vote_health_appropriation_detail_fact",
                    "source_page": page,
                    "appropriation_name": name,
                    **{
                        field: vote_health.parse_amount_token(value)
                        for field, value in tokens.items()
                    },
                    "unit": "$000",
                    "rights_state": "not_evaluated",
                    "quality_flags": [
                        "complete_six_value_row_only",
                        "dash_not_converted_to_zero",
                        "part_b1_layout_incomplete",
                    ],
                    "transformation_id": vote_health.DETAIL_2002_03_TRANSFORMATION,
                    "lineage_id": identity(record_id, "lineage"),
                    "raw_values_json": encode_json(
                        {"appropriation_name": name, "tokens": tokens}
                    ),
                }
            )
            normalized_pages.add(page)
            for field, raw_value in tokens.items():
                lineage.append(
                    FieldLineage(
                        record_id=record_id,
                        field=field,
                        source_coordinate=(
                            f"pdf:page={page};part_b1:{name};column={field}"
                        ),
                        raw_value=raw_value,
                        normalized_value=str(vote_health.parse_amount_token(raw_value)),
                        rule="vote-health-detail-complete-row/v1",
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
                    "complete_six_value_rows_only"
                    if page in normalized_pages
                    else "outside_2002_03_part_b1_or_no_complete_row"
                ),
            )
            for page in range(1, _SOURCE_PAGES + 1)
        )
        return AdapterOutput(
            records=tuple(records),
            losses=losses,
            lineage=tuple(lineage),
            layout=_PROFILE,
        )


def vote_health_estimates_2002_03_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register the exact retained 2002/03 Estimates detail-only source."""
    adapter = VoteHealthEstimates2002DetailAdapter(
        source_locator, source_vintage, observed_at
    )
    return AdapterRegistration(
        adapter_id=_ADAPTER_ID,
        version="1.0.0",
        media_type="application/pdf",
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
