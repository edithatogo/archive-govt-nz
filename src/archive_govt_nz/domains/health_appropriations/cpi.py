"""Exact-series CPI Silver extraction, not an inflation adjustment or rights gate."""

from __future__ import annotations

import calendar
import csv
import re
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

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

MAX_BYTES = 16 * 1024 * 1024
MAX_ROWS = 100_000
MAX_LINE = 8192
MAX_FIELD = 4096
HEADERS = (
    "Series_reference",
    "Period",
    "Data_value",
    "STATUS",
    "UNITS",
    "Subject",
    "Group",
    "Series_title_1",
    "Series_title_2",
)
SERIES = "CPIQ.SE9A"
TRANSFORMATION = "stats-nz-cpi-all-groups/v1"
METADATA = {
    "UNITS": "Index",
    "Subject": "CPI",
    "Group": "CPI All Groups for New Zealand",
    "Series_title_1": "All groups",
    "Series_title_2": "NA",
}
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
        ("series_reference", pa.string()),
        ("period_token", pa.string()),
        ("period_end", pa.date32()),
        ("amount", pa.decimal128(38, 18)),
        ("value_token", pa.string()),
        ("raw_status", pa.string()),
        ("unit", pa.string()),
        ("index_base", pa.string()),
        ("missing_reason", pa.string()),
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
        ("source_row", pa.int64()),
        ("disposition", pa.string()),
        ("reason", pa.string()),
        ("record_id", pa.string()),
        ("raw_values_json", pa.string()),
    ]
)
_FIELDS = {
    "Series_reference": "series_reference",
    "Period": "period_end",
    "Data_value": "amount",
    "STATUS": "raw_status",
    "UNITS": "unit",
}


def _require(condition: object) -> None:
    if not condition:
        message = "cpi_source_contract"
        raise ValueError(message)


def _rows(payload: bytes) -> list[dict[str, str]]:
    # This v1 profile is one physical UTF-8 CSV line per record; multiline quoted
    # fields are unsupported, not silently flattened. No global CSV limits change.
    lines = payload.decode("utf-8", errors="strict").splitlines()
    _require(bool(lines) and len(lines) <= MAX_ROWS + 1)
    parsed = []
    for line in lines:
        _require(len(line) <= MAX_LINE)
        row = next(csv.reader([line], strict=True))
        _require(
            len(row) == len(HEADERS) and all(len(value) <= MAX_FIELD for value in row)
        )
        parsed.append(row)
    _require(tuple(parsed[0]) == HEADERS)
    return [dict(zip(HEADERS, row, strict=True)) for row in parsed[1:]]


def _period(token: str) -> date:
    _require(re.fullmatch(r"[0-9]{4}\.(03|06|09|12)", token) is not None)
    year, month = map(int, token.split("."))
    return date(year, month, calendar.monthrange(year, month)[1])


def _amount(value: str) -> Decimal | None:
    if value == "NA":
        return None
    # decimal128(38,18) is exact for this explicit token grammar. No exponent,
    # NaN, infinity, whitespace, rounding or locale-dependent number conversion.
    _require(re.fullmatch(r"[+-]?[0-9]{1,20}(\.[0-9]{1,18})?", value) is not None)
    return Decimal(value)


def _extract(
    rows: list[dict[str, str]], context: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    facts, lineage, dispositions = [], [], []
    periods = set()
    for source_row, raw in enumerate(rows, start=2):
        selected = raw["Series_reference"] == SERIES
        record_id = identity(
            TRANSFORMATION, context["source_object_sha256"], SERIES, source_row
        )
        dispositions.append(
            {
                "source_object_sha256": context["source_object_sha256"],
                "source_locator": context["source_locator"],
                "source_row": source_row,
                "disposition": "selected" if selected else "unselected",
                "reason": "exact_series" if selected else "other_series",
                "record_id": record_id if selected else None,
                "raw_values_json": encode_json(raw),
            }
        )
        if not selected:
            continue
        _require(
            all(raw[key] == value for key, value in METADATA.items())
            and raw["STATUS"] == "FINAL"
        )
        period = _period(raw["Period"])
        _require(period not in periods)
        periods.add(period)
        amount = _amount(raw["Data_value"])
        fact = {
            **context,
            "record_id": record_id,
            "schema_version": "archive-govt-nz.health-cpi-silver/v1",
            "recordset": "price_population_fact",
            "source_row": source_row,
            "series_reference": SERIES,
            "period_token": raw["Period"],
            "period_end": period,
            "amount": amount,
            "value_token": raw["Data_value"],
            "raw_status": raw["STATUS"],
            "unit": "Index",
            "index_base": None,
            "missing_reason": "missing_unknown_reason" if amount is None else None,
            "rights_state": "not_evaluated",
            "quality_flags": [
                "index_base_not_verified",
                "household_prices_not_health_input_costs",
            ],
            "transformation_id": TRANSFORMATION,
            "lineage_id": identity(record_id, "lineage"),
            "raw_values_json": encode_json(raw),
        }
        facts.append(fact)
        for name in HEADERS:
            field = _FIELDS.get(name, f"raw:{name}")
            lineage.append(
                {
                    "lineage_id": fact["lineage_id"],
                    "record_id": record_id,
                    "field": field,
                    "source_object_sha256": context["source_object_sha256"],
                    "source_locator": context["source_locator"],
                    "source_coordinate": f"csv:row={source_row};column={name}",
                    "raw_value": raw[name],
                    "normalized_value": str(fact.get(field, raw[name])),
                    "rule": TRANSFORMATION,
                }
            )
    _require(bool(facts))
    return facts, lineage, dispositions


def normalize_cpi(  # noqa: PLR0913 - explicit provenance plus fail-closed dry-run switch
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    observed_at: str,
    source_vintage: str,
    source_locator: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Preflight by default; explicit writes require a new exclusive directory.

    Only reviewed CPIQ.SE9A profile rows are normalized. Every source row retains
    raw decoded tokens and disposition; CSV quoting remains in immutable Bronze.
    FINAL is preserved as source status, not timelessness or availability proof.
    No base, missing reason, fiscal-year mapping or inflation adjustment inferred.
    On interrupted writing, partial files remain with no completion manifest.
    """
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    _require(not source.is_symlink() and source.is_file())
    _require(not output_dir.exists() and not output_dir.is_symlink())
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    facts, lineage, dispositions = _extract(_rows(payload), context)
    missing = sum(row["amount"] is None for row in facts)
    receipt = {
        "schema_version": "archive-govt-nz.health-cpi-extraction/v1",
        "transformation_id": TRANSFORMATION,
        "status": "planned" if dry_run else "passed",
        "source_object_sha256": expected_sha256,
        "source_locator": source_locator,
        "source_vintage": source_vintage,
        "observed_at": context["observed_at"].isoformat(),
        "rights_state": "not_evaluated",
        "series_reference": SERIES,
        "index_base": None,
        "counts": {
            "input": len(dispositions),
            "selected": len(facts),
            "numeric": len(facts) - missing,
            "missing": missing,
            "unselected": len(dispositions) - len(facts),
        },
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "cpi_facts.parquet": pa.Table.from_pylist(facts, schema=FACT_SCHEMA),
            "field_lineage.parquet": pa.Table.from_pylist(
                lineage, schema=LINEAGE_SCHEMA
            ),
            "row_dispositions.parquet": pa.Table.from_pylist(
                dispositions, schema=DISPOSITION_SCHEMA
            ),
        },
        receipt,
    )
