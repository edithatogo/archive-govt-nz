"""Pinned page-five summaries from the 2023/24 Vote Health Supplementary Estimates."""

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

PROFILE = "vote-health-supplementary-2023-24-summary-totals/v1"
TRANSFORMATION = PROFILE
VINTAGE = "Treasury-Vote-Health-Supplementary-2023-24"
SOURCE_SHA256 = "7c35d7c49827e5f4a478203007fb388f3f403698765472ab5e44167ed61c2b72"
SOURCE_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2024-06/suppest24health.pdf"
)
PAGE_COUNT = 28
MAX_BYTES = 8 * 1024 * 1024
MAX_TEXT = 100_000
PAGE = 5
COLUMNS = ("estimates_budget", "supplementary_estimates_budget", "total_budget")
_AMOUNT = r"(?:\([0-9][0-9,]*\)|-|[0-9][0-9,]*)"
_EXPECTED_ROWS = (
    (
        "total_annual_appropriations_and_forecast_permanent_appropriations",
        r"Total Annual Appropriations and Forecast Permanent Appropriations",
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
        ("summary_label", pa.string()),
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


def parse_summary_page(pages: list[tuple[int, str]]) -> list[dict[str, Any]]:
    """Parse the four explicitly named summary rows on PDF page 5 only."""
    if tuple(number for number, _ in pages) != (PAGE,):
        _fail("vote_health_2023_24_page_span")
    text = pages[0][1]
    flat = " ".join(text.split())
    if (
        len(text) > MAX_TEXT
        or "The Supplementary Estimates of Appropriations 2023/24" not in flat
        or "Capital Injection Authorisations" not in flat
        or "Estimates Budget $000" not in flat
        or "Supplementary Estimates Budget $000" not in flat
        or "Total Budget $000" not in flat
    ):
        _fail("vote_health_2023_24_layout")
    rows: list[dict[str, Any]] = []
    positions: list[int] = []
    for label, label_pattern in _EXPECTED_ROWS:
        matches = list(
            re.finditer(
                rf"(?P<label>{label_pattern})\s+(?P<a>{_AMOUNT})\s+"
                rf"(?P<b>{_AMOUNT})\s+(?P<c>{_AMOUNT})",
                flat,
            )
        )
        if len(matches) != 1:
            _fail("vote_health_2023_24_summary_row")
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
        _fail("vote_health_2023_24_summary_order")
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
        _fail("vote_health_2023_24_identity")
    if (
        source.is_symlink()
        or not source.is_file()
        or output_dir.exists()
        or output_dir.is_symlink()
    ):
        _fail("vote_health_2023_24_path")
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    if reader.is_encrypted or len(reader.pages) != PAGE_COUNT:
        _fail("vote_health_2023_24_pdf_identity")
    text = reader.pages[PAGE - 1].extract_text() or ""
    rows = parse_summary_page([(PAGE, text)])
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
                        "reason": "four_named_page_five_summary_rows_only",
                    }
                ],
                PAGE_SCHEMA,
            ),
        },
        receipt,
    )
