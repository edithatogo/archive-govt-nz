"""Fail-closed extraction of the 2003/04 Vote Health summary table.

This deliberately admits only the compact Part B summary from the pinned
Supplementary Estimates layout.  Part B1 continuation pages are a separate
layout and are never guessed from this parser.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import TYPE_CHECKING, Any

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

MAX_BYTES = 2 * 1024 * 1024
MAX_PAGES = 100
MAX_TEXT = 200_000
MIN_ROWS = 4
_ERROR = "vote_health_pdf_contract"
PROFILE = "vote-health-supplementary-2003-04-summary/v1"
TRANSFORMATION = "vote-health-supplementary-summary/v1"
_YEAR = "2003/04"
_COLUMNS = (
    "department_annual",
    "department_other",
    "non_departmental_annual",
    "non_departmental_other",
    "total_appropriations",
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
        ("appropriation_type", pa.string()),
        *((column, pa.decimal128(20, 3)) for column in _COLUMNS),
        ("unit", pa.string()),
        ("rights_state", pa.string()),
        ("quality_flags", pa.list_(pa.string())),
        ("transformation_id", pa.string()),
        ("lineage_id", pa.string()),
        ("raw_values_json", pa.string()),
    ]
)
DISPOSITION_SCHEMA = pa.schema(
    [
        ("source_object_sha256", pa.string()),
        ("source_locator", pa.string()),
        ("source_page", pa.int64()),
        ("disposition", pa.string()),
        ("reason", pa.string()),
    ]
)
_AMOUNT = r"(?:\([0-9][0-9,]*\)|-|[0-9][0-9,]*)"
_ROW = re.compile(
    rf"^(?P<label>[A-Za-z][A-Za-z0-9/ ]+?)\s+(?P<a>{_AMOUNT})\s+(?P<b>{_AMOUNT})\s+"
    rf"(?P<c>{_AMOUNT})\s+(?P<d>{_AMOUNT})\s+(?P<e>{_AMOUNT})$"
)
_DETAIL_ROW = re.compile(
    rf"^\s*(?P<label>[A-Za-z][A-Za-z0-9/ Māori&'().,-]+?)\s+"
    rf"(?P<main_annual>{_AMOUNT})\s+(?P<main_other>{_AMOUNT})\s+"
    rf"(?P<supplementary_annual>{_AMOUNT})\s+(?P<supplementary_other>{_AMOUNT})\s+"
    rf"(?P<cumulative_annual>{_AMOUNT})\s+(?P<cumulative_other>{_AMOUNT})(?:\s+.*)?$"
)
_DETAIL_COLUMNS = (
    "main_annual",
    "main_other",
    "supplementary_annual",
    "supplementary_other",
    "cumulative_annual",
    "cumulative_other",
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _amount(token: str) -> Decimal | None:
    if token == "-":  # noqa: S105 - official source dash token
        return None
    try:
        value = Decimal(token.replace(",", "").strip("()"))
    except InvalidOperation:
        raise ValueError(_ERROR) from None
    return -value if token.startswith("(") else value


def parse_summary_page(text: str) -> list[dict[str, Any]]:
    """Parse one exact summary layout while retaining each source token."""
    _require(len(text) <= MAX_TEXT)
    _require("Summary of Appropriations" in text and _YEAR in text)
    rows: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = " ".join(raw_line.split())
        match = _ROW.fullmatch(line)
        if match is None:
            continue
        values = [match.group(name) for name in ("a", "b", "c", "d", "e")]
        rows.append(
            {
                "appropriation_type": match.group("label"),
                "tokens": dict(zip(_COLUMNS, values, strict=True)),
            }
        )
    labels = [row["appropriation_type"] for row in rows]
    _require(len(rows) >= MIN_ROWS and len(labels) == len(set(labels)))
    _require("Total Appropriations for 2003/04" in labels)
    return rows


def parse_detail_page(text: str) -> list[dict[str, Any]]:
    """Extract only complete Part B1 six-column rows from a single page.

    Wrapped labels and reason prose have no independent numerical admission;
    callers retain them as source pages until a continuation-aware layout is
    separately reviewed.
    """
    _require(len(text) <= MAX_TEXT and "Part B1 - Details of Appropriations" in text)
    rows = []
    for raw_line in text.splitlines():
        match = _DETAIL_ROW.fullmatch(raw_line)
        if match is None:
            continue
        label = match.group("label").strip()
        _require(label not in {"Appropriations", "Annual Other"})
        rows.append(
            {
                "appropriation_name": label,
                "tokens": {column: match.group(column) for column in _DETAIL_COLUMNS},
            }
        )
    _require(
        bool(rows) and len({row["appropriation_name"] for row in rows}) == len(rows)
    )
    return rows


def normalize_vote_health_summary(  # noqa: PLR0913 - provenance is explicit
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Extract the single reviewed 2003/04 summary table into local outputs."""
    _require(source_vintage == "Treasury-Vote-Health-Supplementary-2003-04")
    _require(not source.is_symlink() and source.is_file())
    _require(not output_dir.exists() and not output_dir.is_symlink())
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    _require(not reader.is_encrypted and 0 < len(reader.pages) <= MAX_PAGES)
    candidates = []
    for number, candidate in enumerate(reader.pages, start=1):
        text = candidate.extract_text(extraction_mode="layout")
        if "Summary of Appropriations" in (text or ""):
            candidates.append((number, text))
    _require(len(candidates) == 1 and candidates[0][1] is not None)
    page, text = candidates[0]
    rows = parse_summary_page(text)
    facts = []
    lineage = []
    for row in rows:
        record_id = identity(
            TRANSFORMATION, expected_sha256, page, row["appropriation_type"]
        )
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": "archive-govt-nz.vote-health-summary/v1",
                "recordset": "vote_health_appropriation_summary_fact",
                "source_page": page,
                "appropriation_type": row["appropriation_type"],
                **{key: _amount(value) for key, value in row["tokens"].items()},
                "unit": "$000",
                "rights_state": "not_evaluated",
                "quality_flags": ["summary_layout_only", "dash_not_converted_to_zero"],
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
                        f"pdf:page={page};summary:{row['appropriation_type']};"
                        f"column={column}"
                    ),
                    "raw_value": token,
                    "normalized_value": str(_amount(token)),
                    "rule": TRANSFORMATION,
                }
            )
    receipt: dict[str, object] = {
        "schema_version": "archive-govt-nz.vote-health-summary-extraction/v1",
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
            "vote_health_summary_facts.parquet": pa.Table.from_pylist(
                facts, FACT_SCHEMA
            ),
            "field_lineage.parquet": pa.Table.from_pylist(lineage, LINEAGE_SCHEMA),
            "page_dispositions.parquet": pa.Table.from_pylist(
                [
                    {
                        "source_object_sha256": expected_sha256,
                        "source_locator": source_locator,
                        "source_page": page,
                        "disposition": "normalized",
                        "reason": "reviewed_2003_04_summary_layout",
                    }
                ],
                DISPOSITION_SCHEMA,
            ),
        },
        receipt,
    )
