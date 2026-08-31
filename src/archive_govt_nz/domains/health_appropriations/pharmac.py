"""Literal Pharmac medicines budgets; never actual expenditure or recomputation."""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any, cast

import pyarrow as pa

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

MAX_BYTES = 1024 * 1024
MAX_CELL = 512
TABLE_ROWS = 15
MAX_COLUMNS = 5
PADDING_THROUGH_YEAR = 2016
TRANSFORMATION = "pharmac-published-budget-20260807/v1"
HEADERS = (
    "FINANCIAL YEAR",
    "CPB ($ MILLION)",
    "CHANGE FROM PREVIOUS YEAR ($ MILLION)",
    "PERCENTAGE CHANGE FROM PREVIOUS YEAR (%)",
)
CONTEXT = (
    "Medicines budget, 2013/14 to 2025/26",
    "Pharmac's financial year runs from 1 July to 30 June.",
    (
        "From 1 July 2022, an appropriation was created by Government and allocated "
        "to Pharmac (referred to as the medicines budget). This was part of health "
        "and disability system reforms, shifting budget holding and management away "
        "from the previous 20 district health boards to the national body responsible "
        "for assessment and decision-making about funding."
    ),
)
FLAGS = (
    "budget_allocation_not_actual_expenditure",
    "published_changes_not_recomputed",
    "published_percentage_rounding_retained",
    "caption_ends_2025_26_table_includes_2026_27",
    "budget_holder_reform_2022_cross_regime_comparability_not_asserted",
    "price_basis_not_explicit",
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
        ("source_row", pa.int64()),
        ("period_token", pa.string()),
        ("period_start", pa.date32()),
        ("period_end", pa.date32()),
        ("amount", pa.decimal128(20, 3)),
        ("amount_type", pa.string()),
        ("unit", pa.string()),
        ("published_change", pa.decimal128(20, 3)),
        ("change_status", pa.string()),
        ("published_percent_change", pa.decimal128(20, 3)),
        ("percent_change_status", pa.string()),
        ("percent_unit", pa.string()),
        ("series_caption", pa.string()),
        ("period_definition", pa.string()),
        ("policy_scope_note", pa.string()),
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
        ("source_coordinate", pa.string()),
        ("decoded_text", pa.string()),
        ("colspan", pa.int64()),
        ("disposition", pa.string()),
        ("reason", pa.string()),
        ("record_id", pa.string()),
    ]
)


def _require(condition: object) -> None:
    if not condition:
        message = "pharmac_source_contract"
        raise ValueError(message)


class _Table(HTMLParser):
    """Decode one bounded table and paragraph context without browser execution."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.seen = False
        self.opened = False
        self.rows: list[list[tuple[str, int]]] = []
        self.row: list[tuple[str, int]] | None = None
        self.cell: list[str] | None = None
        self.span = 1
        self.cell_tag = ""
        self.paragraph: list[str] | None = None
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            _require(not self.seen)
            self.seen = self.opened = True
        elif self.opened and tag == "tr":
            _require(self.row is None and len(self.rows) < TABLE_ROWS)
            self.row = []
        elif self.opened and tag in ("td", "th"):
            _require(self.row is not None and self.cell is None)
            _require(len(cast("list[tuple[str, int]]", self.row)) < MAX_COLUMNS)
            _require(tag == ("th" if not self.rows else "td"))
            selected = [
                (key, value) for key, value in attrs if key in ("colspan", "rowspan")
            ]
            _require(len(dict(selected)) == len(selected))
            attributes = dict(selected)
            _require(attributes.get("rowspan", "1") == "1")
            _require(attributes.get("colspan", "1") in ("1", "2"))
            self.span = int(str(attributes.get("colspan", "1")))
            self.cell = []
            self.cell_tag = tag
        elif self.opened and tag in ("script", "style"):
            message = "pharmac_source_contract"
            raise ValueError(message)
        elif tag == "p" and not self.opened:
            self.paragraph = []
        elif tag == "br":
            self.handle_data(" ")

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)
            _require(sum(map(len, self.cell)) <= MAX_CELL)
        elif self.paragraph is not None:
            self.paragraph.append(data)

    def handle_endtag(self, tag: str) -> None:
        if self.opened and tag in ("td", "th"):
            _require(self.row is not None and self.cell is not None)
            _require(tag == self.cell_tag)
            cast("list[tuple[str, int]]", self.row).append(
                (" ".join(" ".join(cast("list[str]", self.cell)).split()), self.span)
            )
            self.cell = None
        elif self.opened and tag == "tr":
            _require(self.row is not None and self.cell is None)
            self.rows.append(cast("list[tuple[str, int]]", self.row))
            self.row = None
        elif tag == "table":
            _require(self.opened and self.row is None and self.cell is None)
            self.opened = False
        elif tag == "p" and not self.opened and self.paragraph is not None:
            self.paragraphs.append(" ".join(" ".join(self.paragraph).split()))
            self.paragraph = None


def parse_number(token: str, *, percent: bool = False) -> Decimal | None:
    """Keep dash missingness and exact published decimals, including zero."""
    if token == "-":  # noqa: S105 - literal source missing marker
        return None
    value = token
    if percent:
        _require(value.endswith("%"))
        value = value[:-1]
    _require(
        re.fullmatch(
            r"[+-]?(?:[0-9]{1,12}|[0-9]{1,3}(?:,[0-9]{3}){1,3})(?:\.[0-9]{1,3})?", value
        )
        is not None
    )
    return Decimal(value.replace(",", "")).quantize(Decimal("0.001"))


def _parse(payload: bytes) -> _Table:
    parser = _Table()
    parser.feed(payload.decode("utf-8", errors="strict"))
    parser.close()
    _require(parser.seen and not parser.opened and len(parser.rows) == TABLE_ROWS)
    _require(parser.rows[0] == list(zip(HEADERS, (1, 1, 1, 2), strict=True)))
    for text in CONTEXT:
        _require(parser.paragraphs.count(text) == 1)
    for row, year in zip(parser.rows[1:], range(2026, 2012, -1), strict=True):
        expected = (1, 1, 1, 2) if year > PADDING_THROUGH_YEAR else (1, 1, 1, 1, 1)
        _require(tuple(span for _, span in row) == expected)
        _require(row[0][0] == f"{year}/{(year + 1) % 100:02}")
        _require(len(row) == len(HEADERS) or row[-1][0] == "")
    return parser


def _extract(
    parser: _Table, context: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    facts, lineage, dispositions = [], [], []
    for row_number, cells in enumerate(parser.rows, start=1):
        record_id = identity(
            TRANSFORMATION, context["source_object_sha256"], row_number
        )
        if row_number > 1:
            raw = [value for value, _ in cells]
            year = int(raw[0][:4])
            amount = parse_number(raw[1])
            _require(amount is not None)
            change = parse_number(raw[2])
            percent = parse_number(raw[3], percent=True)
            fact = {
                **context,
                "record_id": record_id,
                "schema_version": "archive-govt-nz.health-pharmac-silver/v1",
                "recordset": "pharmaceutical_budget_fact",
                "source_row": row_number,
                "period_token": raw[0],
                "period_start": date(year, 7, 1),
                "period_end": date(year + 1, 6, 30),
                "amount": amount,
                "amount_type": "published_budget_allocation",
                "unit": "NZD_millions",
                "published_change": change,
                "change_status": "source_dash_not_supplied"
                if change is None
                else "supplied",
                "published_percent_change": percent,
                "percent_change_status": "source_dash_not_supplied"
                if percent is None
                else "supplied",
                "percent_unit": "percent",
                "series_caption": CONTEXT[0],
                "period_definition": CONTEXT[1],
                "policy_scope_note": CONTEXT[2],
                "rights_state": "not_evaluated",
                "quality_flags": list(FLAGS),
                "transformation_id": TRANSFORMATION,
                "lineage_id": identity(record_id, "lineage"),
                "raw_values_json": encode_json(raw),
            }
            facts.append(fact)
            fields = [
                "period_token",
                "amount",
                "published_change",
                "published_percent_change",
                "raw:padding",
            ]
            sources = [
                (field, f"html:table=1;row={row_number};cell={index}", value)
                for index, (field, value) in enumerate(
                    zip(fields, raw, strict=False), start=1
                )
            ]
            for field, text in zip(
                ("series_caption", "period_definition", "policy_scope_note"),
                CONTEXT,
                strict=True,
            ):
                sources.append(
                    (
                        field,
                        f"html:outside-table-p={parser.paragraphs.index(text) + 1}",
                        text,
                    )
                )
            period_coordinate = (
                f"html:outside-table-p={parser.paragraphs.index(CONTEXT[1]) + 1}"
            )
            for field in ("period_start", "period_end"):
                sources.extend(
                    [
                        (field, f"html:table=1;row={row_number};cell=1", raw[0]),
                        (
                            field,
                            period_coordinate,
                            CONTEXT[1],
                        ),
                    ]
                )
            sources.extend(
                [
                    ("unit", "html:table=1;row=1;cell=2", HEADERS[1]),
                    ("percent_unit", "html:table=1;row=1;cell=4", HEADERS[3]),
                ]
            )
            for field, coordinate, value in sources:
                normalized = fact.get(field, value)
                lineage.append(
                    {
                        "record_id": record_id,
                        "lineage_id": fact["lineage_id"],
                        "field": field,
                        "source_object_sha256": context["source_object_sha256"],
                        "source_locator": context["source_locator"],
                        "source_coordinate": coordinate,
                        "raw_value": value,
                        "normalized_value": None
                        if normalized is None
                        else str(normalized),
                        "rule": TRANSFORMATION,
                    }
                )
        for column, (value, span) in enumerate(cells, start=1):
            dispositions.append(
                {
                    "source_object_sha256": context["source_object_sha256"],
                    "source_coordinate": f"html:table=1;row={row_number};cell={column}",
                    "decoded_text": value,
                    "colspan": span,
                    "disposition": "context"
                    if row_number == 1
                    else "preserved_only"
                    if column == MAX_COLUMNS
                    else "normalized",
                    "reason": "header"
                    if row_number == 1
                    else "empty_layout_padding"
                    if column == MAX_COLUMNS
                    else "published_budget_field",
                    "record_id": None if row_number == 1 else record_id,
                }
            )
    return facts, lineage, dispositions


def normalize_pharmac_budget(  # noqa: PLR0913 - explicit provenance and dry-run
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    source_locator: str,
    source_vintage: str,
    observed_at: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Preflight one reviewed HTML profile; writes require a new output directory.

    Decode physical table cells with whitespace folding, retaining padding and
    colspan. The immutable HTML remains authoritative for markup and all other
    page areas. Supplied changes are not recomputed or treated as expenditure.
    """
    _require(source_vintage == "Pharmac-CPB-2026-08-07")
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    _require(source.is_file() and not source.is_symlink())
    _require(not output_dir.exists() and not output_dir.is_symlink())
    parser = _parse(verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES))
    facts, lineage, dispositions = _extract(parser, context)
    receipt = {
        "schema_version": "archive-govt-nz.health-pharmac-extraction/v1",
        "transformation_id": TRANSFORMATION,
        "status": "planned" if dry_run else "passed",
        "source_object_sha256": expected_sha256,
        "source_locator": source_locator,
        "source_vintage": source_vintage,
        "observed_at": context["observed_at"].isoformat(),
        "rights_state": "not_evaluated",
        "quality_flags": list(FLAGS),
        "counts": {
            "facts": len(facts),
            "lineage": len(lineage),
            "table_cells": len(dispositions),
        },
        "excluded_areas": [
            {
                "area": "outside_selected_table_and_context",
                "disposition": "preserved_only",
                "reason": "original_html_retained",
            }
        ],
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "pharmaceutical_budget_facts.parquet": pa.Table.from_pylist(
                facts, schema=FACT_SCHEMA
            ),
            "field_lineage.parquet": pa.Table.from_pylist(
                lineage, schema=LINEAGE_SCHEMA
            ),
            "cell_dispositions.parquet": pa.Table.from_pylist(
                dispositions, schema=DISPOSITION_SCHEMA
            ),
        },
        receipt,
    )
