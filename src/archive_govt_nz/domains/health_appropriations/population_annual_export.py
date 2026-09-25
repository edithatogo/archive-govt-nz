"""Exact Stats NZ annual mean population export admission profile."""

from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

from archive_govt_nz.domains.health_appropriations.workbook_common import identity

MAX_BYTES = 65_536
MAX_LINES = 100
MAX_LINE = 2_048
MAX_REQUESTED_YEARS = 100
FIRST_YEAR = 1991
LAST_YEAR = 2026
COLUMN_COUNT = 3
MISSING_TOKEN = ".."  # noqa: S105 - Stats NZ missing-value symbol
TITLE = "Estimated Resident Population by Age and Sex (1991+) (Annual-Jun)"
TABLE_ID = "DPE056AA"
RELEASE_DATE = "2026-08-18"
BASE_NOTE = (
    "All population estimates at 30 June 2023 and beyond are based on the "
    "2023 Estimated Resident Population (ERP)."
)
FOOTER = (
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
        "incorporate revisions to external (international) migration and birth "
        "estimates."
    ),
    "Symbols:",
    ".. figure not available",
    "C: Confidential",
    "E: Early Estimate",
    "P: Provisional",
    "R: Revised",
    "S: Suppressed",
    "Table reference: ",
    TABLE_ID,
    "Last updated:",
    "Total All Ages: 18 August 2026 10:45am",
    "Source: Statistics New Zealand",
    "Contact: Information Centre",
    "Telephone: 0508 525 525",
    "Email:info@stats.govt.nz",
)


class AnnualPopulationExportError(ValueError):
    """An annual population export violates the reviewed source profile."""


@dataclass(frozen=True)
class ExportTransport:
    """Optional caller-observed transport properties; never inferred by parser."""

    http_status: int | None
    media_type: str | None
    sha256: str


def _require(condition: object) -> None:
    if not condition:
        message = "annual_population_export_contract"
        raise AnnualPopulationExportError(message)


def _read_rows(payload: bytes) -> list[list[str]]:
    _require(0 < len(payload) <= MAX_BYTES)
    try:
        lines = payload.decode("utf-8", errors="strict").splitlines()
        _require(len(lines) <= MAX_LINES)
        rows: list[list[str]] = []
        for line in lines:
            _require(len(line) <= MAX_LINE)
            rows.append(next(csv.reader([line], strict=True)))
    except (UnicodeDecodeError, csv.Error) as error:
        message = "annual_population_csv_encoding"
        raise AnnualPopulationExportError(message) from error
    else:
        return rows


def _footer(rows: list[list[str]]) -> None:
    _require(all(len(row) <= 1 for row in rows))
    values = tuple(row[0] for row in rows if row and row[0] not in ("", " "))
    _require(values == FOOTER)


def inspect_export(
    payload: bytes,
    *,
    transport: ExportTransport,
    requested_years: tuple[int, ...] = tuple(range(1991, 2027)),
) -> dict[str, Any]:
    """Validate and type one exact annual-Jun, mean-year-ended export.

    Returned records preserve publisher values and P statuses. They are
    contextual source facts only; no denominator or rights decision is made.
    """
    _require(transport.http_status in (None, HTTPStatus.OK))
    _require(transport.media_type in (None, "text/csv"))
    source_hash = hashlib.sha256(payload).hexdigest()
    _require(source_hash == transport.sha256)
    _require(0 < len(requested_years) <= MAX_REQUESTED_YEARS)
    _require(tuple(sorted(set(requested_years))) == requested_years)
    _require(requested_years[0] == FIRST_YEAR and requested_years[-1] == LAST_YEAR)
    _require(requested_years == tuple(range(FIRST_YEAR, LAST_YEAR + 1)))
    rows = _read_rows(payload)
    _require(
        rows[:4]
        == [
            [TITLE, "", ""],
            ["", "Mean year ended", ""],
            [" ", "Total", ""],
            [" ", "Total All Ages", ""],
        ]
    )
    _require(rows.count(["Table information:"]) == 1)
    boundary = rows.index(["Table information:"])
    _footer(rows[boundary + 1 :])
    facts: list[dict[str, Any]] = []
    seen: set[int] = set()
    for source_row, row in enumerate(rows[4:boundary], 5):
        _require(
            len(row) == COLUMN_COUNT and row[2] in ("", " P", " R", " E", " C", " S")
        )
        _require(
            re.fullmatch(r"(?:199[1-9]|20(?:0[0-9]|1[0-9]|2[0-6]))", row[0]) is not None
        )
        year = int(row[0])
        _require(year in requested_years and year not in seen)
        seen.add(year)
        value_text = row[1]
        _require(
            value_text == MISSING_TOKEN
            or re.fullmatch(r"[0-9]{1,12}", value_text) is not None
        )
        status = row[2].strip() or None
        facts.append(
            {
                "record_id": identity(
                    "population-annual-export/v1",
                    source_hash,
                    TABLE_ID,
                    RELEASE_DATE,
                    str(year),
                    "2",
                    "C",
                    "DPE056FF",
                ),
                "estimate_code": "2",
                "estimate_label": "Mean year ended",
                "reference_kind": "mean_year_ended",
                "reference_period": f"FY{year}",
                "reference_date": f"{year}-06-30",
                "population_code": "C",
                "age_code": "DPE056FF",
                "unit": "persons",
                "value_token": value_text,
                "amount": None if value_text == MISSING_TOKEN else int(value_text),
                "missing_reason": (
                    "figure_not_available" if value_text == MISSING_TOKEN else None
                ),
                "status": status,
                "source_row": source_row,
                "source_column": 2,
            }
        )
    _require(seen == set(requested_years))
    return {
        "schema_version": "archive-govt-nz.population-annual-export-inspection/v1",
        "source_sha256": source_hash,
        "source_bytes": len(payload),
        "table_id": TABLE_ID,
        "release_date": RELEASE_DATE,
        "query": {
            "estimate": "Mean year ended",
            "population": "Total",
            "observation": "Total All Ages",
            "frequency": "Annual-Jun",
        },
        "first_year": requested_years[0],
        "last_year": requested_years[-1],
        "status_visibility": "displayed",
        "capture_state": "persisted_bronze_cas",
        "transport_status": "not_observed"
        if transport.http_status is None
        else "observed_200",
        "transport_media_type": "not_observed"
        if transport.media_type is None
        else transport.media_type,
        "rights": "not_evaluated",
        "analytical_selection": "not_selected",
        "facts": facts,
    }
