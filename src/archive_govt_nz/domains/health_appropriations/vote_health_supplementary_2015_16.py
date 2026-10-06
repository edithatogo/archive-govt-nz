"""Pinned appropriation totals from the 2015/16 Vote Health Supplementary Estimates."""

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

PROFILE = "vote-health-supplementary-2015-16-category-totals/v1"
TRANSFORMATION = PROFILE
VINTAGE = "Treasury-Vote-Health-Supplementary-2015-16"
SOURCE_SHA256 = "694aece23fdb2eac82d96e5dc075339f39ba481b12b33a03db2de5596cf2a47d"
SOURCE_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2016-05/suppest16health.pdf"
)
PAGE_COUNT = 46
MAX_BYTES = 8 * 1024 * 1024
MAX_TEXT = 100_000
PAGES = (2, 3, 4, 5, 6)
COLUMNS = ("estimates_budget", "supplementary_estimates_budget", "total_budget")
_AMOUNT = r"(?:\([0-9][0-9,]*\)|-|[0-9][0-9,]*)"
_TOTAL = re.compile(
    rf"^(?P<label>Total .+?)\s+(?P<a>{_AMOUNT})\s+(?P<b>{_AMOUNT})\s+(?P<c>{_AMOUNT})$"
)
_EXPECTED_LABELS = (
    "Total Departmental Output Expenses",
    "Total Departmental Capital Expenditure",
    "Total Non-Departmental Output Expenses",
    "Total Non-Departmental Other Expenses",
    "Total Non-Departmental Capital Expenditure",
    "Total Multi-Category Expenses and Capital Expenditure",
    "Total Annual and Permanent Appropriations",
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
        ("total_label", pa.string()),
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
    if token == "-":  # noqa: S105 - official source dash token
        return None
    value = Decimal(token.replace(",", "").strip("()"))
    return -value if token.startswith("(") else value


def parse_category_totals(pages: list[tuple[int, str]]) -> list[dict[str, Any]]:
    """Parse only the seven named totals from the pinned five-page table span."""
    if tuple(page for page, _ in pages) != PAGES:
        _fail("vote_health_2015_16_page_span")
    rows: list[dict[str, Any]] = []
    for page, text in pages:
        flat = " ".join(text.split())
        if (
            "2015/16" not in flat
            or "Supplementary" not in flat
            or "Estimates Budget" not in flat
            or "Total Budget" not in flat
            or len(text) > MAX_TEXT
        ):
            _fail("vote_health_2015_16_layout")
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
                        "source_page": page,
                        "total_label": match.group("label"),
                        "tokens": tokens,
                    }
                )
    if tuple(row["total_label"] for row in rows) != _EXPECTED_LABELS:
        _fail("vote_health_2015_16_total_set")
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
    """Emit a source-pinned, local category-total table with field lineage."""
    if (
        source_vintage != VINTAGE
        or expected_sha256 != SOURCE_SHA256
        or source_locator != SOURCE_LOCATOR
    ):
        _fail("vote_health_2015_16_identity")
    if (
        source.is_symlink()
        or not source.is_file()
        or output_dir.exists()
        or output_dir.is_symlink()
    ):
        _fail("vote_health_2015_16_path")
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    if reader.is_encrypted or len(reader.pages) != PAGE_COUNT:
        _fail("vote_health_2015_16_pdf_identity")
    pages = [(page, reader.pages[page - 1].extract_text() or "") for page in PAGES]
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
                        f"pdf:page={row['source_page']};"
                        f"category_total:{row['total_label']};column={column}"
                    ),
                    "raw_value": token,
                    "normalized_value": str(_amount(token)),
                    "rule": "vote-health-2015-16-category-total-token/v1",
                }
            )
    receipt: dict[str, object] = {
        "schema_version": "archive-govt-nz.vote-health-category-totals-extraction/v1",
        "status": "planned" if dry_run else "passed",
        "profile": PROFILE,
        "source_object_sha256": expected_sha256,
        "counts": {"pages": len(pages), "facts": len(facts)},
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
                        "source_page": page,
                        "disposition": "partially_normalized",
                        "reason": "seven_named_category_totals_only",
                    }
                    for page, _ in pages
                ],
                PAGE_SCHEMA,
            ),
        },
        receipt,
    )
