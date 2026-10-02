"""Fail-closed extraction of Vote Health 2003/04 Part F Crown Revenue."""

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
MAX_PAGES = 22
MAX_TEXT = 200_000
PART_F_PAGES = 2
PART_F_ROWS = 17
PROFILE = "vote-health-supplementary-2003-04-revenue/v1"
TRANSFORMATION = "vote-health-supplementary-revenue/v1"
ESTIMATES_2002_03_VINTAGE = "Treasury-Vote-Health-Estimates-2002-03"
ESTIMATES_2002_03_SHA256 = (
    "1170e0bf5d11e6ac93620a2d76d68004ed99b88ed45a0c6c3c48bbc38f72fafe"
)
ESTIMATES_2002_03_PROFILE = "vote-health-estimates-2002-03-revenue/v1"
ESTIMATES_2002_03_TRANSFORMATION = "vote-health-estimates-revenue-2002-03/v1"
ESTIMATES_2002_03_PAGE_COUNT = 44
ESTIMATES_2002_03_ROWS = 16
ESTIMATES_2002_03_COLUMNS = (
    "prior_year_budgeted",
    "prior_year_estimated_actual",
    "current_year_budgeted",
)
_ERROR = "vote_health_revenue_pdf_contract"
_AMOUNT = r"(?:\(\s*[0-9][0-9,]*\)|-|[0-9][0-9,]*)"
_NUMERIC = re.compile(
    rf"^(?P<main>{_AMOUNT})\s+(?P<supplementary>{_AMOUNT})\s+"
    rf"(?P<total>{_AMOUNT})(?:\s+.*)?$"
)
_INLINE = re.compile(
    rf"^(?P<label>[A-Za-z][A-Za-z0-9 &'().,-]+?)\s+(?P<main>{_AMOUNT})\s+"
    rf"(?P<supplementary>{_AMOUNT})\s+(?P<total>{_AMOUNT})(?:\s+.*)?$"
)
_LABEL_STARTS = (
    "ACC -",
    "Payment of Capital Charge",
    "Net Surplus",
    "Repayment of Loan",
    "Residual Health",
    "Total ",
    "Principal Repayment",
    "Repayment of Residential",
    "Repayment of DHB Debt",
)
_COLUMNS = ("main_estimates", "supplementary_estimates", "total_budgeted")

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
        ("revenue_name", pa.string()),
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
ESTIMATES_2002_03_FACT_SCHEMA = pa.schema(
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
        ("revenue_name", pa.string()),
        *((column, pa.decimal128(20, 3)) for column in ESTIMATES_2002_03_COLUMNS),
        ("unit", pa.string()),
        ("rights_state", pa.string()),
        ("quality_flags", pa.list_(pa.string())),
        ("transformation_id", pa.string()),
        ("lineage_id", pa.string()),
        ("raw_values_json", pa.string()),
    ]
)


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _amount(token: str) -> Decimal | None:
    compact = token.replace(",", "").replace(" ", "")
    if compact == "-":
        return None
    try:
        value = Decimal(compact.strip("()"))
    except InvalidOperation:
        raise ValueError(_ERROR) from None
    return -value if compact.startswith("(") else value


def parse_amount_token(token: str) -> Decimal | None:
    """Parse one amount token using the reviewed Part F grammar."""
    return _amount(token)


def _label(value: str) -> str:
    return re.sub(r"(?<=[A-Za-z])-\s+", "-", " ".join(value.split())).strip()


def parse_revenue_pages(texts: list[str]) -> list[dict[str, Any]]:
    """Parse the fixed two-page Part F layout without admitting prose."""
    _require(
        len(texts) == PART_F_PAGES and all(len(text) <= MAX_TEXT for text in texts)
    )
    _require("Part F - Crown Revenue and Receipts" in texts[0])
    rows: list[dict[str, Any]] = []
    pending: list[str] = []
    for page, text in enumerate(texts, start=20):
        for raw_line in text.splitlines():
            line = _label(raw_line)
            inline = _INLINE.fullmatch(line)
            numeric = _NUMERIC.fullmatch(line)
            if inline is not None and inline.group("label").startswith(_LABEL_STARTS):
                label = inline.group("label")
                tokens = {
                    column: inline.group(key)
                    for column, key in zip(
                        _COLUMNS, ("main", "supplementary", "total"), strict=True
                    )
                }
            elif numeric is not None and pending:
                label = _label(" ".join(pending))
                tokens = {
                    column: numeric.group(key)
                    for column, key in zip(
                        _COLUMNS, ("main", "supplementary", "total"), strict=True
                    )
                }
            else:
                if line.startswith(_LABEL_STARTS):
                    pending = [line]
                elif pending and not numeric:
                    pending.append(line)
                continue
            _require(label and label not in {row["revenue_name"] for row in rows})
            rows.append({"source_page": page, "revenue_name": label, "tokens": tokens})
            pending = []
    names = {row["revenue_name"] for row in rows}
    _require(len(rows) == PART_F_ROWS and "Total Crown Revenue and Receipts" in names)
    return rows


def parse_estimates_2002_03_revenue_pages(
    texts: list[str],
) -> list[dict[str, Any]]:
    """Parse the exact 2002/03 Part F pages with their distinct year columns."""
    _require(len(texts) == PART_F_PAGES)
    _require(all(len(text) <= MAX_TEXT for text in texts))
    _require("Part F - Crown Revenue and Receipts" in texts[0])
    rows: list[dict[str, Any]] = []
    pending: list[str] = []
    for page, text in zip((43, 44), texts, strict=True):
        for raw_line in text.splitlines():
            line = _label(raw_line)
            inline = _INLINE.fullmatch(line)
            numeric = _NUMERIC.fullmatch(line)
            if inline is not None and inline.group("label").startswith(_LABEL_STARTS):
                label = inline.group("label")
                values = tuple(
                    inline.group(key) for key in ("main", "supplementary", "total")
                )
            elif numeric is not None and pending:
                label = _label(" ".join(pending))
                values = tuple(
                    numeric.group(key) for key in ("main", "supplementary", "total")
                )
            else:
                if line.startswith(_LABEL_STARTS):
                    pending = [line]
                elif pending and not numeric:
                    pending.append(line)
                continue
            _require(label and label not in {row["revenue_name"] for row in rows})
            rows.append(
                {
                    "source_page": page,
                    "revenue_name": label,
                    "tokens": dict(zip(ESTIMATES_2002_03_COLUMNS, values, strict=True)),
                }
            )
            pending = []
    names = {row["revenue_name"] for row in rows}
    _require(
        len(rows) == ESTIMATES_2002_03_ROWS
        and "Total Crown Revenue and Receipts" in names
        and "Total Capital Receipts" in names
    )
    return rows


def normalize_vote_health_revenue(  # noqa: PLR0913 - provenance is explicit
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize exactly the reviewed 2003/04 Part F revenue layout."""
    _require(source_vintage == "Treasury-Vote-Health-Supplementary-2003-04")
    _require(not source.is_symlink() and source.is_file())
    _require(not output_dir.exists() and not output_dir.is_symlink())
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    _require(not reader.is_encrypted and len(reader.pages) == MAX_PAGES)
    texts = [page.extract_text(extraction_mode="plain") or "" for page in reader.pages]
    rows = parse_revenue_pages(texts[19:21])
    facts: list[dict[str, object]] = []
    lineage: list[dict[str, object]] = []
    for row in rows:
        record_id = identity(
            TRANSFORMATION, expected_sha256, row["source_page"], row["revenue_name"]
        )
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": "archive-govt-nz.vote-health-revenue/v1",
                "recordset": "vote_health_crown_revenue_fact",
                "source_page": row["source_page"],
                "revenue_name": row["revenue_name"],
                **{column: _amount(token) for column, token in row["tokens"].items()},
                "unit": "$000",
                "rights_state": "not_evaluated",
                "quality_flags": ["part_f_fixed_layout", "dash_not_converted_to_zero"],
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
                        f"pdf:page={row['source_page']};part_f:"
                        f"{row['revenue_name']};column={column}"
                    ),
                    "raw_value": token,
                    "normalized_value": str(_amount(token)),
                    "rule": TRANSFORMATION,
                }
            )
    receipt: dict[str, object] = {
        "schema_version": "archive-govt-nz.vote-health-revenue-extraction/v1",
        "status": "planned" if dry_run else "passed",
        "profile": PROFILE,
        "source_object_sha256": expected_sha256,
        "counts": {"pages": 2, "facts": len(facts)},
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "vote_health_revenue_facts.parquet": pa.Table.from_pylist(
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
                        "reason": "reviewed_2003_04_part_f_layout",
                    }
                    for page in (20, 21)
                ],
                DISPOSITION_SCHEMA,
            ),
        },
        receipt,
    )


def normalize_vote_health_estimates_revenue_2002_03(  # noqa: PLR0913 - provenance is explicit
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_vintage: str,
    source_locator: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Normalize only the pinned 2002/03 Estimates Part F source pages."""
    _require(
        source_vintage == ESTIMATES_2002_03_VINTAGE
        and expected_sha256 == ESTIMATES_2002_03_SHA256
    )
    _require(not source.is_symlink() and source.is_file())
    _require(not output_dir.exists() and not output_dir.is_symlink())
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    reader = PdfReader(BytesIO(payload), strict=True)
    _require(
        not reader.is_encrypted and len(reader.pages) == ESTIMATES_2002_03_PAGE_COUNT
    )
    texts = [page.extract_text(extraction_mode="plain") or "" for page in reader.pages]
    rows = parse_estimates_2002_03_revenue_pages(texts[42:44])
    facts: list[dict[str, object]] = []
    lineage: list[dict[str, object]] = []
    for row in rows:
        page = int(row["source_page"])
        name = str(row["revenue_name"])
        tokens = dict(row["tokens"])
        record_id = identity(
            ESTIMATES_2002_03_TRANSFORMATION, expected_sha256, page, name
        )
        facts.append(
            {
                **context,
                "record_id": record_id,
                "schema_version": "archive-govt-nz.vote-health-estimates-revenue/v1",
                "recordset": "vote_health_crown_revenue_estimates_fact",
                "source_page": page,
                "revenue_name": name,
                **{column: _amount(token) for column, token in tokens.items()},
                "unit": "$000",
                "rights_state": "not_evaluated",
                "quality_flags": [
                    "part_f_fixed_layout",
                    "prior_year_columns_preserved",
                    "dash_not_converted_to_zero",
                ],
                "transformation_id": ESTIMATES_2002_03_TRANSFORMATION,
                "lineage_id": identity(record_id, "lineage"),
                "raw_values_json": encode_json(row),
            }
        )
        for column, token in tokens.items():
            value = _amount(token)
            lineage.append(
                {
                    "lineage_id": identity(record_id, column),
                    "record_id": record_id,
                    "field": column,
                    "source_object_sha256": expected_sha256,
                    "source_locator": source_locator,
                    "source_coordinate": (
                        f"pdf:page={page};part_f:{name};column={column}"
                    ),
                    "raw_value": token,
                    "normalized_value": str(value),
                    "rule": ESTIMATES_2002_03_TRANSFORMATION,
                }
            )
    receipt: dict[str, object] = {
        "schema_version": "archive-govt-nz.vote-health-estimates-revenue-extraction/v1",
        "status": "planned" if dry_run else "passed",
        "profile": ESTIMATES_2002_03_PROFILE,
        "source_object_sha256": expected_sha256,
        "counts": {"pages": 2, "facts": len(facts)},
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "vote_health_estimates_revenue_facts.parquet": pa.Table.from_pylist(
                facts, ESTIMATES_2002_03_FACT_SCHEMA
            ),
            "field_lineage.parquet": pa.Table.from_pylist(lineage, LINEAGE_SCHEMA),
            "page_dispositions.parquet": pa.Table.from_pylist(
                [
                    {
                        "source_object_sha256": expected_sha256,
                        "source_locator": source_locator,
                        "source_page": page,
                        "disposition": "normalized",
                        "reason": "reviewed_2002_03_part_f_layout",
                    }
                    for page in (43, 44)
                ],
                DISPOSITION_SCHEMA,
            ),
        },
        receipt,
    )
