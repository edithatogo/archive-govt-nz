"""Pinned appropriation totals from the 2013/14 Vote Health Supplementary Estimates."""

from __future__ import annotations

import re
from decimal import Decimal
from io import BytesIO
from typing import TYPE_CHECKING, Any, NoReturn

import pyarrow as pa
from pypdf import PdfReader

from archive_govt_nz.domains.health_appropriations import (
    vote_health_supplementary_2018_19 as _shared,
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

PROFILE = "vote-health-supplementary-2013-14-category-totals/v1"
TRANSFORMATION = PROFILE
VINTAGE = "Treasury-Vote-Health-Supplementary-2013-14"
SOURCE_SHA256 = "1ec8cf9e4c33d027f3ed02593ab3e8c7cab89883d5b286e0cf4aa4b1e947f5a2"
SOURCE_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2014-05/suppest14health.pdf"
)
PAGE_COUNT = 44
MAX_BYTES = _shared.MAX_BYTES
MAX_TEXT = _shared.MAX_TEXT
PAGES = (2, 3, 4, 5, 6)
COLUMNS = ("estimates_budget", "supplementary_estimates_budget", "total_budget")
FACT_SCHEMA = _shared.FACT_SCHEMA
PAGE_SCHEMA = _shared.PAGE_SCHEMA
_AMOUNT = r"(?:\([0-9][0-9,]*\)|-|[0-9][0-9,]*)"
_TOTAL = re.compile(
    rf"^Total (?P<label>.+?)\s+(?P<a>{_AMOUNT})\s+(?P<b>{_AMOUNT})\s+(?P<c>{_AMOUNT})$"
)
_EXPECTED_LABELS = (
    "Total Departmental Output Expenses",
    "Total Departmental Capital Expenditure",
    "Total Non-Departmental Output Expenses",
    "Total Non-Departmental Other Expenses",
    "Total Non-Departmental Capital Expenditure",
    "Total Annual and Permanent Appropriations",
)


def _fail(code: str) -> NoReturn:
    raise ValueError(code)


def _amount(token: str) -> Decimal | None:
    if token == "-":  # noqa: S105 - official source dash token
        return None
    value = Decimal(token.replace(",", "").strip("()"))
    return -value if token.startswith("(") else value


def parse_category_totals(pages: list[tuple[int, str]]) -> list[dict[str, Any]]:
    """Parse the six explicitly named totals across the pinned table pages."""
    if tuple(number for number, _ in pages) != PAGES:
        _fail("vote_health_2013_14_page_span")
    rows: list[dict[str, Any]] = []
    for number, text in pages:
        flat = " ".join(text.split())
        if (
            len(text) > MAX_TEXT
            or "2013/14" not in flat
            or "Supplementary Estimates" not in flat
            or "Estimates Budget" not in flat
            or "Total Budget" not in flat
        ):
            _fail("vote_health_2013_14_layout")
        for raw in text.splitlines():
            match = _TOTAL.fullmatch(" ".join(raw.split()))
            if match:
                tokens = dict(
                    zip(
                        COLUMNS,
                        (match.group("a"), match.group("b"), match.group("c")),
                        strict=True,
                    )
                )
                rows.append(
                    {
                        "source_page": number,
                        "total_label": f"Total {match.group('label')}",
                        "tokens": tokens,
                    }
                )
    if tuple(row["total_label"] for row in rows) != _EXPECTED_LABELS:
        _fail("vote_health_2013_14_total_set")
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
    """Emit local source-pinned facts, direct lineage and partial page status."""
    if (
        source_vintage != VINTAGE
        or expected_sha256 != SOURCE_SHA256
        or source_locator != SOURCE_LOCATOR
    ):
        _fail("vote_health_2013_14_identity")
    if (
        source.is_symlink()
        or not source.is_file()
        or output_dir.exists()
        or output_dir.is_symlink()
    ):
        _fail("vote_health_2013_14_path")
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    if reader.is_encrypted or len(reader.pages) != PAGE_COUNT:
        _fail("vote_health_2013_14_pdf_identity")
    pages = [
        (number, reader.pages[number - 1].extract_text() or "") for number in PAGES
    ]
    rows = parse_category_totals(pages)
    facts: list[dict[str, Any]] = []
    lineage: list[dict[str, str]] = []
    for row in rows:
        record_id = identity(
            TRANSFORMATION, expected_sha256, row["source_page"], row["total_label"]
        )
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": "archive-govt-nz.vote-health-category-totals/v1",
                "recordset": "vote_health_category_total_fact",
                "source_page": row["source_page"],
                "total_label": row["total_label"],
                **{column: _amount(token) for column, token in row["tokens"].items()},
                "unit": "$000",
                "rights_state": "not_evaluated",
                "quality_flags": [
                    "source_reported_category_total",
                    "dash_preserved_as_null",
                    "supplementary_estimates_only",
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
                        f"pdf:page={row['source_page']};total={row['total_label']};column={column}"
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
        "counts": {"pages": len(PAGES), "facts": len(facts)},
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "vote_health_category_total_facts.parquet": pa.Table.from_pylist(
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
                        "reason": "six_named_category_totals_only",
                    }
                    for number in PAGES
                ],
                PAGE_SCHEMA,
            ),
        },
        receipt,
    )
