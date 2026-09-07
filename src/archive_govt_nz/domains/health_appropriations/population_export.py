"""Bounded Infoshare response admission; capture persistence stays separate."""

from __future__ import annotations

import calendar
import csv
import hashlib
import re
from dataclasses import dataclass
from datetime import date
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.workbook_common import identity

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.population_context import (
        PopulationContext,
    )

MAX_BYTES = 65_536
MAX_LINES = 200
MAX_LINE = 2048
MAX_PERIODS = 142
DATA_COLUMNS = 3
MISSING_VALUE = ".."
BASE_NOTE = (
    "All population estimates at 30 June 2023 and beyond are based on the "
    "2023 Estimated Resident Population (ERP)."
)
REVIEWED_FOOTER = (
    "Units:",
    "Number, Magnitude = Units",
    "Footnotes:",
    "Due to rounding, individual figures may not sum to stated totals.",
    BASE_NOTE,
    (
        "Population estimates after 30 June 2018 have been revised to incorporate "
        "results from the 2023 Census and 2023 Post-enumeration Survey."
    ),
    (
        "Estimates flagged as provisional are subject to revision, mainly to "
        "incorporate revisions to external (international) migration "
        "and birth estimates."
    ),
    "Symbols:",
    ".. figure not available",
    "C: Confidential",
    "E: Early Estimate",
    "P: Provisional",
    "R: Revised",
    "S: Suppressed",
    "Status flags are not displayed",
    "Table reference: ",
    "DPE054AA",
    "Last updated:",
    "Total All Ages: 18 August 2026 10:45am",
    "Source: Statistics New Zealand",
    "Contact: Information Centre",
    "Telephone: 0508 525 525",
    "Email:info@stats.govt.nz",
)


class PopulationExportError(ValueError):
    """A response does not satisfy the bounded population export profile."""


@dataclass(frozen=True)
class ExportTransport:
    """Caller-observed transport facts; no network or capture attestation."""

    http_status: int
    media_type: str
    sha256: str


def _require(condition: object) -> None:
    if not condition:
        message = "population_export_contract"
        raise PopulationExportError(message)


def _period(token: str) -> str:
    _require(re.fullmatch(r"(199[1-9]|20[0-2][0-9])Q[1-4]", token))
    _require("1991Q1" <= token <= "2026Q2")
    year, quarter = int(token[:4]), int(token[-1])
    month = quarter * 3
    return date(year, month, calendar.monthrange(year, month)[1]).isoformat()


def _rows(payload: bytes) -> list[list[str]]:
    _require(0 < len(payload) <= MAX_BYTES)
    try:
        lines = payload.decode("utf-8", errors="strict").splitlines()
        _require(len(lines) <= MAX_LINES)
        rows = []
        for line in lines:
            _require(len(line) <= MAX_LINE)
            rows.append(next(csv.reader([line], strict=True)))
    except (UnicodeDecodeError, csv.Error) as error:
        message = "population_export_encoding_or_csv"
        raise PopulationExportError(message) from error
    return rows


def _footer(rows: list[list[str]]) -> None:
    _require(all(len(row) <= 1 for row in rows))
    # Only the publisher's observed blank separator forms are ignorable.
    # Every substantive row is ordered and accounted for, including notes.
    values = tuple(row[0] for row in rows if row and row[0] not in ("", " "))
    _require(values == REVIEWED_FOOTER)


def inspect_export(
    payload: bytes,
    context: PopulationContext,
    *,
    transport: ExportTransport,
    requested_periods: tuple[str, ...],
) -> dict[str, Any]:
    """Validate exact response bytes and retain both publisher measures.

    Caller owns HTTP acquisition and immutable original persistence. This
    function never fetches, writes, interpolates, or chooses a denominator.
    Unknown layouts, status visibility, footers and numeric tokens fail closed.
    The accepted unflagged profile retains status=None, never inferred FINAL.

    Raises:
        ValueError: Transport, fixity, request or source semantics do not match.

    """
    _require(0 < len(payload) <= MAX_BYTES)
    _require(
        transport.http_status == HTTPStatus.OK and transport.media_type == "text/csv"
    )
    expected_sha256 = transport.sha256
    _require(hashlib.sha256(payload).hexdigest() == expected_sha256)
    _require(0 < len(requested_periods) <= MAX_PERIODS)
    _require(len(set(requested_periods)) == len(requested_periods))
    for period in requested_periods:
        _period(period)
    rows = _rows(payload)
    _require(
        rows[:4]
        == [
            [context.table_title, "", ""],
            ["", "As at", "Mean year ended"],
            [" ", "Total", "Total"],
            [" ", "Total All Ages", "Total All Ages"],
        ]
    )
    _require(rows.count(["Table information:"]) == 1)
    boundary = rows.index(["Table information:"])
    _footer(rows[boundary + 1 :])
    seen: set[str] = set()
    facts = []
    for source_row, row in enumerate(rows[4:boundary], 5):
        _require(len(row) == DATA_COLUMNS)
        period = row[0]
        _require(period in requested_periods and period not in seen)
        seen.add(period)
        reference_date = _period(period)
        for column, (code, label, kind) in enumerate(
            [
                ("1", "As at", "point_in_time"),
                ("2", "Mean year ended", "mean_year_ended"),
            ],
            1,
        ):
            token = row[column]
            _require(token == MISSING_VALUE or re.fullmatch(r"[0-9]{1,12}", token))
            facts.append(
                {
                    "record_id": identity(
                        "population-export/v1",
                        expected_sha256,
                        context.table_id,
                        context.release_date,
                        period,
                        code,
                        context.population_code,
                        context.age_code,
                    ),
                    "estimate_code": code,
                    "estimate_label": label,
                    "reference_kind": kind,
                    "reference_period": period,
                    "reference_date": reference_date,
                    "population_code": context.population_code,
                    "age_code": context.age_code,
                    "unit": context.unit,
                    "value_token": token,
                    "amount": None if token == MISSING_VALUE else int(token),
                    "missing_reason": "figure_not_available"
                    if token == MISSING_VALUE
                    else None,
                    "status": None,
                    "source_row": source_row,
                    "source_column": column + 1,
                }
            )
    _require(seen == set(requested_periods))
    return {
        "schema_version": "archive-govt-nz.population-export-inspection/v1",
        "source_sha256": expected_sha256,
        "source_bytes": len(payload),
        "table_id": context.table_id,
        "release_date": context.release_date,
        "basis_date": context.basis_date,
        "context_sha256": hashlib.sha256(
            context.model_dump_json().encode()
        ).hexdigest(),
        "request_periods": list(requested_periods),
        "status_visibility": "not_displayed",
        "capture_state": "response_verified_not_persisted",
        "rights": "not_evaluated",
        "analytical_selection": "not_selected",
        "facts": facts,
    }
