"""Pinned page-six summaries from the 2025/26 Vote Health Supplementary Estimates."""

from __future__ import annotations

import re
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any, NoReturn

import pyarrow as pa
from pypdf import PdfReader

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2024_25 as _shared,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    identity,
    source_context,
    verified_snapshot,
    write_workbook_outputs,
)

if TYPE_CHECKING:
    from pathlib import Path

PROFILE = "vote-health-supplementary-2025-26-summary-totals/v1"
TRANSFORMATION = PROFILE
VINTAGE = "Treasury-Vote-Health-Supplementary-2025-26"
SOURCE_SHA256 = "575e3744f555d668f3748f46cc55781378bfc0ad35008c9512a942c57279f31f"
SOURCE_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2026-05/suppest26health.pdf"
)
PAGE_COUNT = 30
MAX_BYTES = _shared.MAX_BYTES
MAX_TEXT = _shared.MAX_TEXT
PAGE = 6
COLUMNS = _shared.COLUMNS
FACT_SCHEMA = _shared.FACT_SCHEMA
PAGE_SCHEMA = _shared.PAGE_SCHEMA
_AMOUNT_PATTERN = r"(?:\([0-9][0-9,]*\)|-|[0-9][0-9,]*)"
_EXPECTED_ROWS = (
    (
        "total_annual_appropriations_and_forecast_permanent_appropriations",
        r"Total Annual Appropriations and Forecast Permanent Appropriations",
    ),
    (
        "total_forecast_mya_departmental_output_expenses",
        r"Total Forecast MYA Departmental Output Expenses",
    ),
    (
        "total_forecast_mya_non_departmental_output_expenses",
        r"Total Forecast MYA Non-Departmental Output Expenses",
    ),
    (
        "total_forecast_mya_non_departmental_capital_expenditure",
        r"Total Forecast MYA Non-Departmental Capital Expenditure",
    ),
    (
        "total_annual_appropriations_and_forecast_permanent_appropriations_and_multi_year_appropriations",
        (
            r"Total Annual Appropriations and Forecast Permanent Appropriations "
            r"and Multi\s*-\s*Year Appropriations"
        ),
    ),
    (
        "ministry_of_health_capital_injection_m36_a21",
        r"Ministry of Health - Capital Injection \(M36\) \(A21\)",
    ),
)


def _fail(code: str) -> NoReturn:
    raise ValueError(code)


def _amount(token: str) -> Decimal | None:
    if token == "-":  # noqa: S105 - official source dash token
        return None
    value = Decimal(token.replace(",", "").strip("()"))
    return -value if token.startswith("(") else value


def parse_summary_page(pages: list[tuple[int, str]]) -> list[dict[str, Any]]:
    """Parse the six explicitly named summary rows on PDF page six only."""
    if tuple(number for number, _ in pages) != (PAGE,):
        _fail("vote_health_2025_26_page_span")
    text = pages[0][1]
    flat = " ".join(text.split())
    if (
        len(text) > MAX_TEXT
        or "The Supplementary Estimates of Appropriations 2025/26" not in flat
        or "Total Annual Appropriations and Forecast" not in flat
        or "Supplementary Estimates Budget $000" not in flat
        or "Total Budget $000" not in flat
        or "Capital Injection Authorisations" not in flat
    ):
        _fail("vote_health_2025_26_layout")
    rows: list[dict[str, Any]] = []
    positions: list[int] = []
    for label, label_pattern in _EXPECTED_ROWS:
        matches = list(
            re.finditer(
                rf"(?P<label>{label_pattern})\s+(?P<a>{_AMOUNT_PATTERN})\s+"
                rf"(?P<b>{_AMOUNT_PATTERN})\s+(?P<c>{_AMOUNT_PATTERN})",
                flat,
            )
        )
        if len(matches) != 1:
            _fail("vote_health_2025_26_summary_row")
        match = matches[0]
        positions.append(match.start())
        rows.append(
            {
                "summary_label": label,
                "source_label": " ".join(match.group("label").split()),
                "tokens": dict(
                    zip(
                        COLUMNS,
                        (match.group("a"), match.group("b"), match.group("c")),
                        strict=True,
                    )
                ),
            }
        )
    if positions != sorted(positions):
        _fail("vote_health_2025_26_summary_order")
    return rows


def normalize(  # noqa: PLR0913 - provenance context remains explicit
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Emit a local, hash-pinned summary fact, lineage and page disposition."""
    if (
        source_vintage != VINTAGE
        or expected_sha256 != SOURCE_SHA256
        or source_locator != SOURCE_LOCATOR
    ):
        _fail("vote_health_2025_26_identity")
    if (
        source.is_symlink()
        or not source.is_file()
        or output_dir.exists()
        or output_dir.is_symlink()
    ):
        _fail("vote_health_2025_26_path")
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    if reader.is_encrypted or len(reader.pages) != PAGE_COUNT:
        _fail("vote_health_2025_26_pdf_identity")
    rows = parse_summary_page([(PAGE, reader.pages[PAGE - 1].extract_text() or "")])
    facts: list[dict[str, Any]] = []
    lineage: list[dict[str, str]] = []
    for row in rows:
        record_id = identity(
            TRANSFORMATION, expected_sha256, PAGE, row["summary_label"]
        )
        quality_flags = (
            ["source_reported_capital_injection_authorisation"]
            if row["summary_label"] == "ministry_of_health_capital_injection_m36_a21"
            else ["source_reported_summary_total"]
        )
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": (
                    "archive-govt-nz.vote-health-supplementary-summary/v1"
                ),
                "recordset": "vote_health_supplementary_summary_fact",
                "source_page": PAGE,
                "summary_label": row["summary_label"],
                **{column: _amount(token) for column, token in row["tokens"].items()},
                "unit": "$000",
                "rights_state": "not_evaluated",
                "quality_flags": [
                    *quality_flags,
                    "supplementary_estimates_only",
                    "dash_preserved_as_null",
                ],
                "transformation_id": TRANSFORMATION,
                "lineage_id": identity(record_id, "lineage"),
                "raw_values_json": encode_json(row),
            }
        )
        for column, token in row["tokens"].items():
            lineage.append(
                {
                    "lineage_id": identity(record_id, column),
                    "record_id": record_id,
                    "field": column,
                    "source_object_sha256": expected_sha256,
                    "source_locator": source_locator,
                    "source_coordinate": (
                        f"pdf:page={PAGE};summary:{row['summary_label']};column={column}"
                    ),
                    "raw_value": token,
                    "normalized_value": str(_amount(token)),
                    "rule": TRANSFORMATION,
                }
            )
    receipt: dict[str, object] = {
        "schema_version": (
            "archive-govt-nz.vote-health-supplementary-summary-extraction/v1"
        ),
        "status": "planned" if dry_run else "passed",
        "profile": PROFILE,
        "source_object_sha256": expected_sha256,
        "counts": {"pages": 1, "facts": len(facts)},
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "vote_health_supplementary_summary_facts.parquet": pa.Table.from_pylist(
                facts, FACT_SCHEMA
            ),
            "field_lineage.parquet": pa.Table.from_pylist(lineage, LINEAGE_SCHEMA),
            "page_dispositions.parquet": pa.Table.from_pylist(
                [
                    {
                        "source_object_sha256": expected_sha256,
                        "source_locator": source_locator,
                        "source_page": PAGE,
                        "disposition": "partially_normalized",
                        "reason": "six_named_page_six_summary_rows_only",
                    }
                ],
                PAGE_SCHEMA,
            ),
        },
        receipt,
    )
