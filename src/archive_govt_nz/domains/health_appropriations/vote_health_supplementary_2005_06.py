"""Overview totals from the 2005/06 Vote Health Supplementary Estimates."""

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

PROFILE = "vote-health-supplementary-2005-06-overview-totals/v1"
TRANSFORMATION = PROFILE
VINTAGE = "Treasury-Vote-Health-Supplementary-2005-06"
SOURCE_SHA256 = "9907280937726b80a2f623f3879f9bc69814e02a1702a3cb0b2fb39d2d7d7074"
SOURCE_LOCATOR = (
    "https://www.treasury.govt.nz/sites/default/files/2007-09/supp06health.pdf"
)
PAGE_COUNT = 17
PAGE = 3
MAX_BYTES = 8 * 1024 * 1024
MAX_TEXT = 40_000
COLUMNS = (
    "main_estimates",
    "department_annual",
    "department_other",
    "non_departmental_annual",
    "non_departmental_other",
    "total_appropriations",
)
_CELL = r"(?:N/A|-|\([0-9][0-9,]*\)|[0-9][0-9,]*)"
_ROW_CELLS = re.compile(rf"^\s*(?P<cells>{_CELL}(?:\s+{_CELL}){{5}})\s*$")
_LABELS = (
    "Output Expenses",
    "Benefits and Other Unrequited Expenses",
    "Borrowing Expenses",
    "Other Expenses",
    "Capital Expenditure",
    "Intelligence and Security Department Expenses and Capital Expenditure",
    "Total Appropriations",
)
_LABEL_PATTERNS = tuple(
    re.compile(re.escape(label).replace(r"\ ", r"\s+")) for label in _LABELS
)
_TOKEN = re.compile(_CELL)
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
        ("appropriation_label", pa.string()),
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


def parse_overview_totals(text: str) -> list[dict[str, Any]]:
    """Parse the seven appropriation rows while retaining dash and N/A tokens."""
    flat = " ".join(text.split())
    if (
        "2005/06" not in flat
        or "Summary of Financial Activity" not in flat
        or "Main Estimates" not in flat
        or "Appropriations" not in flat
        or "Crown Revenue and Receipts" not in flat
        or len(text) > MAX_TEXT
    ):
        _fail("vote_health_2005_06_layout")
    section_start = re.search(r"\bAppropriations\s+Output\s+Expenses\b", flat)
    section_end = flat.find("Crown Revenue and Receipts")
    if section_start is None or section_end <= section_start.start():
        _fail("vote_health_2005_06_appropriation_section")
    section = flat[section_start.start() : section_end]
    rows: list[dict[str, Any]] = []
    cursor = 0
    for index, (label, label_pattern) in enumerate(
        zip(_LABELS, _LABEL_PATTERNS, strict=True)
    ):
        match = label_pattern.search(section, cursor)
        if match is None:
            _fail("vote_health_2005_06_total_set")
        next_start = (
            _LABEL_PATTERNS[index + 1].search(section, match.end())
            if index + 1 < len(_LABEL_PATTERNS)
            else None
        )
        row_end = next_start.start() if next_start else len(section)
        cell_match = _ROW_CELLS.match(section[match.end() : row_end])
        if cell_match is None:
            _fail("vote_health_2005_06_row_cells")
        tokens = _TOKEN.findall(cell_match.group("cells"))
        if len(tokens) != len(COLUMNS):
            _fail("vote_health_2005_06_cell_count")
        rows.append(
            {
                "appropriation_label": label,
                "tokens": dict(zip(COLUMNS, tokens, strict=True)),
            }
        )
        cursor = row_end
    if tuple(row["appropriation_label"] for row in rows) != _LABELS:
        _fail("vote_health_2005_06_total_set")
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
    """Emit pinned overview totals with source token and field lineage."""
    if (
        source_vintage != VINTAGE
        or expected_sha256 != SOURCE_SHA256
        or source_locator != SOURCE_LOCATOR
    ):
        _fail("vote_health_2005_06_identity")
    if (
        source.is_symlink()
        or not source.is_file()
        or output_dir.exists()
        or output_dir.is_symlink()
    ):
        _fail("vote_health_2005_06_path")
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    if reader.is_encrypted or len(reader.pages) != PAGE_COUNT:
        _fail("vote_health_2005_06_pdf_identity")
    page_text = reader.pages[PAGE - 1].extract_text() or ""
    rows = parse_overview_totals(page_text)
    facts: list[dict[str, Any]] = []
    lineage: list[dict[str, str]] = []
    for row in rows:
        record_id = identity(
            TRANSFORMATION, expected_sha256, PAGE, row["appropriation_label"]
        )
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": (
                    "archive-govt-nz.vote-health-appropriation-overview/v1"
                ),
                "recordset": "vote_health_appropriation_overview_fact",
                "source_page": PAGE,
                "appropriation_label": row["appropriation_label"],
                **{column: _amount(token) for column, token in row["tokens"].items()},
                "unit": "$000",
                "rights_state": "not_evaluated",
                "quality_flags": [
                    "source_reported_appropriation_overview",
                    "dash_and_not_applicable_tokens_preserved",
                    "supplementary_estimates_2005_06",
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
                        f"pdf:page={PAGE};appropriation_summary:"
                        f"{row['appropriation_label']};column={column}"
                    ),
                    "raw_value": token,
                    "normalized_value": str(_amount(token)),
                    "rule": "vote-health-2005-06-overview-cell/v1",
                }
            )
    receipt: dict[str, object] = {
        "schema_version": (
            "archive-govt-nz.vote-health-appropriation-overview-extraction/v1"
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
            "vote_health_appropriation_overview_facts.parquet": pa.Table.from_pylist(
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
                        "reason": "seven_appropriation_overview_rows_only",
                    }
                ],
                PAGE_SCHEMA,
            ),
        },
        receipt,
    )
