"""Bronze dispatcher for the exact reviewed 2003/04 Vote Health PDF."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO
from typing import Any

from pypdf import PdfReader
from pypdf.errors import PdfReadError

from archive_govt_nz.domains.health_appropriations import (
    vote_health,
    vote_health_revenue,
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
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    identity,
    source_context,
)

_VINTAGE = "Treasury-Vote-Health-Supplementary-2003-04"
_MEDIA_TYPE = "application/pdf"
_MAX_BYTES = min(vote_health.MAX_BYTES, vote_health_revenue.MAX_BYTES)
_MAX_PAGES = vote_health_revenue.MAX_PAGES
_PROFILE = "vote-health-supplementary-2003-04-tables/v1"
_SUMMARY_ID = "nz-treasury-vote-health-2003-04-tables"
_HASH_ERROR = "source_hash_mismatch"
_ParsedTables = tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    int,
    int,
    int,
]


@dataclass(frozen=True, slots=True)
class VoteHealthPdfAdapter:
    """Extract only the reviewed summary, Part B1, and Part F layouts."""

    source_locator: str
    source_vintage: str
    observed_at: str

    def _tables(self, bronze: bytes) -> _ParsedTables | None:  # noqa: PLR0911 - bounded fail-closed gates
        if self.source_vintage != _VINTAGE or not 0 < len(bronze) <= _MAX_BYTES:
            return None
        try:
            reader = PdfReader(BytesIO(bronze), strict=True)
            if reader.is_encrypted or len(reader.pages) != _MAX_PAGES:
                return None
            layout_texts = [
                page.extract_text(extraction_mode="layout") or ""
                for page in reader.pages
            ]
            plain_texts = [
                page.extract_text(extraction_mode="plain") or ""
                for page in reader.pages
            ]
            summaries = [
                (number, text)
                for number, text in enumerate(layout_texts, start=1)
                if "Summary of Appropriations" in text
            ]
            starts = [
                number
                for number, text in enumerate(plain_texts)
                if "Part B1 - Details of Appropriations" in text
                and "(continued)" not in text
            ]
            ends = [
                number for number, text in enumerate(plain_texts) if "Part E -" in text
            ]
            if len(summaries) != 1 or len(starts) != 1 or len(ends) != 1:
                return None
            if starts[0] >= ends[0] or (
                "Part F - Crown Revenue and Receipts" not in plain_texts[19]
            ):
                return None
            summary_rows = vote_health.parse_summary_page(summaries[0][1])
            detail_rows: list[dict[str, object]] = []
            for index in range(starts[0], ends[0]):
                rows = vote_health.parse_detail_page(
                    plain_texts[index], require_heading=False, require_rows=False
                )
                detail_rows.extend({"source_page": index + 1, **row} for row in rows)
            if not detail_rows:
                return None
            revenue_rows = vote_health_revenue.parse_revenue_pages(plain_texts[19:21])
            return (
                summary_rows,
                detail_rows,
                revenue_rows,
                summaries[0][0],
                starts[0],
                ends[0],
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
        """Require all three disambiguating table markers and valid parsers."""
        return self._tables(bronze) is not None

    def extract(self, bronze: bytes, *, source_sha256: str) -> AdapterOutput:
        """Return all three exact table products with page losses and lineage."""
        actual = hashlib.sha256(bronze).hexdigest()
        if actual != source_sha256:
            raise ValueError(_HASH_ERROR)
        parsed = self._tables(bronze)
        if parsed is None:
            return preserved_only(
                source_coordinate="bronze:sha256:" + actual,
                reason="unsupported_vote_health_pdf_layout",
            )
        (
            summary_rows,
            detail_rows,
            revenue_rows,
            summary_page,
            start,
            end,
        ) = parsed
        context = source_context(
            actual, self.source_locator, self.source_vintage, self.observed_at
        )
        records: list[dict[str, object]] = []
        lineage: list[FieldLineage] = []
        dispositions: dict[int, tuple[str, str]] = {}

        def append_lineage(
            record_id: str,
            fields: dict[str, str],
            page: int,
            table: str,
            rule: str,
        ) -> None:
            for field, raw_value in fields.items():
                normalized = (
                    vote_health.parse_amount_token(raw_value)
                    if table.startswith(("summary:", "part_b1:"))
                    else vote_health_revenue.parse_amount_token(raw_value)
                )
                lineage.append(
                    FieldLineage(
                        record_id=record_id,
                        field=field,
                        source_coordinate=f"pdf:page={page};{table};column={field}",
                        raw_value=raw_value,
                        normalized_value=str(normalized),
                        rule=rule,
                    )
                )

        for row in summary_rows:
            label = str(row["appropriation_type"])
            tokens = dict(row["tokens"])
            record_id = identity(
                vote_health.TRANSFORMATION, actual, summary_page, label
            )
            records.append(
                {
                    **context,
                    "record_id": record_id,
                    "schema_version": "archive-govt-nz.vote-health-summary/v1",
                    "recordset": "vote_health_appropriation_summary_fact",
                    "source_page": summary_page,
                    "appropriation_type": label,
                    **{
                        field: vote_health.parse_amount_token(value)
                        for field, value in tokens.items()
                    },
                    "unit": "$000",
                    "rights_state": "not_evaluated",
                    "quality_flags": [
                        "summary_layout_only",
                        "dash_not_converted_to_zero",
                    ],
                    "transformation_id": vote_health.TRANSFORMATION,
                    "lineage_id": identity(record_id, "lineage"),
                    "raw_values_json": encode_json(row),
                }
            )
            append_lineage(
                record_id,
                tokens,
                summary_page,
                f"summary:{label}",
                vote_health.TRANSFORMATION,
            )
        dispositions[summary_page] = ("normalized", "reviewed_2003_04_summary_layout")

        for row in detail_rows:
            page = int(row["source_page"])
            name = str(row["appropriation_name"])
            tokens = dict(row["tokens"])
            record_id = identity(
                vote_health.TRANSFORMATION, "detail", actual, page, name
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
                    "transformation_id": vote_health.TRANSFORMATION,
                    "lineage_id": identity(record_id, "lineage"),
                    "raw_values_json": encode_json(
                        {"appropriation_name": name, "tokens": tokens}
                    ),
                }
            )
            append_lineage(
                record_id,
                tokens,
                page,
                f"part_b1:{name}",
                "vote-health-detail-complete-row/v1",
            )
        detail_pages = range(start + 1, end + 1)
        for page in detail_pages:
            has_rows = any(int(row["source_page"]) == page for row in detail_rows)
            dispositions[page] = (
                ("partially_normalized", "complete_six_value_rows_only")
                if has_rows
                else ("preserved_only", "no_complete_six_value_row")
            )

        for row in revenue_rows:
            page = int(row["source_page"])
            name = str(row["revenue_name"])
            tokens = dict(row["tokens"])
            record_id = identity(
                vote_health_revenue.TRANSFORMATION,
                actual,
                page,
                name,
            )
            records.append(
                {
                    **context,
                    "record_id": record_id,
                    "schema_version": "archive-govt-nz.vote-health-revenue/v1",
                    "recordset": "vote_health_crown_revenue_fact",
                    "source_page": page,
                    "revenue_name": name,
                    **{
                        field: vote_health_revenue.parse_amount_token(value)
                        for field, value in tokens.items()
                    },
                    "unit": "$000",
                    "rights_state": "not_evaluated",
                    "quality_flags": [
                        "part_f_fixed_layout",
                        "dash_not_converted_to_zero",
                    ],
                    "transformation_id": vote_health_revenue.TRANSFORMATION,
                    "lineage_id": identity(record_id, "lineage"),
                    "raw_values_json": encode_json(row),
                }
            )
            append_lineage(
                record_id,
                tokens,
                page,
                f"part_f:{name}",
                vote_health_revenue.TRANSFORMATION,
            )
            dispositions[page] = ("normalized", "reviewed_2003_04_part_f_layout")

        for page in range(1, _MAX_PAGES + 1):
            dispositions.setdefault(
                page, ("preserved_only", "outside_selected_2003_04_tables")
            )
        losses = tuple(
            LossAccounting(
                source_coordinate=f"pdf:page={page}",
                disposition=disposition,
                reason=reason,
            )
            for page, (disposition, reason) in sorted(dispositions.items())
            if disposition != "normalized"
        )
        return AdapterOutput(
            records=tuple(records),
            losses=losses,
            lineage=tuple(lineage),
            layout=_PROFILE,
        )


def vote_health_pdf_registration(
    *, source_locator: str, source_vintage: str, observed_at: str
) -> AdapterRegistration:
    """Register one non-ambiguous adapter for the exact 2003/04 source PDF."""
    adapter = VoteHealthPdfAdapter(source_locator, source_vintage, observed_at)
    return AdapterRegistration(
        adapter_id=_SUMMARY_ID,
        version="1.0.0",
        media_type=_MEDIA_TYPE,
        adapter=adapter,
        layout_probe=adapter.matches_layout,
    )
