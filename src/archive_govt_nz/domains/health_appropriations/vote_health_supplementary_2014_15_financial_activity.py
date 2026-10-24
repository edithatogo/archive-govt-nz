"""Pinned financial-activity summary from 2014/15 Vote Health estimates."""

from __future__ import annotations

import re
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any, NoReturn

import pyarrow as pa
from pypdf import PdfReader

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

PROFILE = "vote-health-supplementary-2014-15-financial-activity/v1"
TRANSFORMATION = PROFILE
VINTAGE = "Treasury-Vote-Health-Supplementary-2014-15"
SOURCE_SHA256 = "99e90dfddd8fc7b6d2bb545148d95f8f3c4c3cbf77760b91103130304176780e"
SOURCE_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2015-05/suppest15health.pdf"
)
PAGE_COUNT = 38
MAX_BYTES = 8 * 1024 * 1024
MAX_TEXT = 100_000
PAGES = (7,)
COLUMNS = (
    "estimates",
    "departmental_transactions",
    "non_departmental_transactions",
    "total_transactions",
    "total",
)
_AMOUNT = r"(?:\([0-9][0-9,]*\)|N/A|-|[0-9][0-9,]*)"
_ROW = re.compile(
    rf"^(?P<label>.+?)\s+(?P<a>{_AMOUNT})\s+(?P<b>{_AMOUNT})\s+"
    rf"(?P<c>{_AMOUNT})\s+(?P<d>{_AMOUNT})\s+(?P<e>{_AMOUNT})$"
)
_EXPECTED_ROWS = (
    ("appropriations", "Output Expenses"),
    ("appropriations", "Benefits or Related Expenses"),
    ("appropriations", "Borrowing Expenses"),
    ("appropriations", "Other Expenses"),
    ("appropriations", "Capital Expenditure"),
    (
        "appropriations",
        "Intelligence and Security Department Expenses and Capital Expenditure",
    ),
    ("appropriations", "Output Expenses"),
    ("appropriations", "Other Expenses"),
    ("appropriations", "Capital Expenditure"),
    ("appropriations", "Total Appropriations"),
    ("crown_revenue_and_capital_receipts", "Tax Revenue"),
    ("crown_revenue_and_capital_receipts", "Non-Tax Revenue"),
    ("crown_revenue_and_capital_receipts", "Capital Receipts"),
    ("crown_revenue_and_capital_receipts", "Total Crown Revenue and Capital Receipts"),
)

FACT_SCHEMA = pa.schema(
    [
        ("record_id", pa.string()),
        ("schema_version", pa.string()),
        ("recordset", pa.string()),
        ("source_object_sha256", pa.string()),
        ("source_observation_id", pa.string()),
        ("source_locator", pa.string()),
        ("source_vintage", pa.string()),
        ("observed_at", pa.timestamp("us", tz="UTC")),
        ("source_page", pa.int64()),
        ("section", pa.string()),
        ("source_label", pa.string()),
        *((column, pa.decimal128(20, 3)) for column in COLUMNS),
        ("unit", pa.string()),
        ("rights_state", pa.string()),
        ("quality_flags", pa.list_(pa.string())),
        ("transformation_id", pa.string()),
        ("lineage_id", pa.string()),
        ("raw_values_json", pa.string()),
    ]
)
PAGE_SCHEMA = pa.schema(
    [
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("source_page", pa.int64()),
        ("disposition", pa.string()),
        ("reason", pa.string()),
    ]
)


def _fail(code: str) -> NoReturn:
    raise ValueError(code)


def _amount(token: str) -> Decimal | None:
    if token in {"-", "N/A"}:
        return None
    value = Decimal(token.replace(",", "").strip("()"))
    return -value if token.startswith("(") else value


def parse_financial_activity(pages: list[tuple[int, str]]) -> list[dict[str, Any]]:
    """Parse the fourteen named rows from the exact summary page only."""
    if tuple(number for number, _ in pages) != PAGES:
        _fail("vote_health_2014_15_financial_activity_page_span")
    rows: list[dict[str, Any]] = []
    for number, source_text in pages:
        flat = " ".join(source_text.split())
        if (
            len(source_text) > MAX_TEXT
            or "2014/15" not in flat
            or "Summary of Financial Activity" not in flat
            or "Departmental Transactions" not in flat
            or not re.search(r"Non-\s*Departmental\s+Transactions", flat)
            or "Crown Revenue and Capital Receipts" not in flat
        ):
            _fail("vote_health_2014_15_financial_activity_layout")
        normalized_text = re.sub(
            r"Intelligence and Security Department Expenses and Capital"
            r"\s*\n\s*Expenditure",
            "Intelligence and Security Department Expenses and Capital Expenditure",
            source_text,
        )
        normalized_text = re.sub(
            r"(Intelligence and Security Department Expenses and Capital Expenditure)"
            r"\s*\n\s*(-\s+-\s+N/A\s+-\s+-)",
            r"\1 \2",
            normalized_text,
        )
        section = "appropriations"
        for raw in normalized_text.splitlines():
            line = " ".join(raw.split())
            if line == "Crown Revenue and Capital Receipts":
                section = "crown_revenue_and_capital_receipts"
                continue
            match = _ROW.fullmatch(line)
            if match:
                tokens = dict(zip(COLUMNS, match.groups()[1:], strict=True))
                rows.append(
                    {
                        "source_page": number,
                        "section": section,
                        "source_label": match.group("label"),
                        "tokens": tokens,
                    }
                )
    if tuple((row["section"], row["source_label"]) for row in rows) != _EXPECTED_ROWS:
        _fail("vote_health_2014_15_financial_activity_row_set")
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
    """Emit a source-pinned context summary, exact tokens and field lineage."""
    if (
        source_vintage != VINTAGE
        or expected_sha256 != SOURCE_SHA256
        or source_locator != SOURCE_LOCATOR
    ):
        _fail("vote_health_2014_15_financial_activity_identity")
    if (
        source.is_symlink()
        or not source.is_file()
        or output_dir.exists()
        or output_dir.is_symlink()
    ):
        _fail("vote_health_2014_15_financial_activity_path")
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    if reader.is_encrypted or len(reader.pages) != PAGE_COUNT:
        _fail("vote_health_2014_15_financial_activity_pdf_identity")
    pages = [
        (number, reader.pages[number - 1].extract_text() or "") for number in PAGES
    ]
    rows = parse_financial_activity(pages)
    facts: list[dict[str, Any]] = []
    lineage: list[dict[str, str]] = []
    for ordinal, row in enumerate(rows, start=1):
        record_id = identity(
            TRANSFORMATION,
            expected_sha256,
            row["source_page"],
            ordinal,
            row["section"],
            row["source_label"],
        )
        values = {column: _amount(token) for column, token in row["tokens"].items()}
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": "archive-govt-nz.vote-health-financial-activity/v1",
                "recordset": "vote_health_financial_activity_fact",
                "source_page": row["source_page"],
                "section": row["section"],
                "source_label": row["source_label"],
                **values,
                "unit": "$000",
                "rights_state": "not_evaluated",
                "quality_flags": [
                    "source_reported_financial_activity",
                    "dash_and_na_preserved_as_null",
                    "edition_specific_supplementary_estimates",
                ],
                "transformation_id": TRANSFORMATION,
                "lineage_id": identity(record_id, "lineage"),
                "raw_values_json": encode_json({**row, "source_row_ordinal": ordinal}),
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
                        f"pdf:page={row['source_page']};section={row['section']};"
                        f"row={row['source_label']};ordinal={ordinal};column={column}"
                    ),
                    "raw_value": token,
                    "normalized_value": str(values[column]),
                    "rule": TRANSFORMATION,
                }
            )
    receipt: dict[str, object] = {
        "schema_version": (
            "archive-govt-nz.vote-health-financial-activity-extraction/v1"
        ),
        "status": "planned" if dry_run else "passed",
        "profile": PROFILE,
        "source_object_sha256": expected_sha256,
        "counts": {"pages": len(PAGES), "facts": len(facts), "lineage": len(lineage)},
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "vote_health_financial_activity_facts.parquet": pa.Table.from_pylist(
                facts, FACT_SCHEMA
            ),
            "field_lineage.parquet": pa.Table.from_pylist(lineage, LINEAGE_SCHEMA),
            "page_dispositions.parquet": pa.Table.from_pylist(
                [
                    {
                        "source_object_sha256": expected_sha256,
                        "source_locator": source_locator,
                        "source_page": number,
                        "disposition": "partially_normalized",
                        "reason": "fourteen_named_summary_financial_activity_rows_only",
                    }
                    for number in PAGES
                ],
                PAGE_SCHEMA,
            ),
        },
        receipt,
    )
