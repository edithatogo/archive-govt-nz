"""Published Ministry indicators, not independently reproduced health measures."""

from __future__ import annotations

import csv
import re
from decimal import Decimal
from types import MappingProxyType
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

MAX_BYTES = 64 * 1024
MAX_LINE = 2048
MAX_FIELD = 512
TRANSFORMATION = "moh-hair2024-published-indicators/v1"
PROFILES = MappingProxyType(
    {
        "fig27/v1": (
            "Year",
            "Total appropriations, excluding capital, COVID-19 & DSS - real",
            "Total appropriations, excluding capital, COVID-19 & DSS - nominal",
        ),
        "fig28/v1": (
            "Year",
            "Total appropriations, excluding capital, COVID-19 & DSS, real per capita",
            (
                "Total appropriations, excluding capital, COVID-19 & DSS, "
                "nominal per capita"
            ),
        ),
    }
)
PERIODS = frozenset(f"{year}/{(year + 1) % 100:02}" for year in range(2005, 2025))
FLAGS = (
    "published_not_independently_recomputed",
    "unit_and_scale_not_supplied",
    "price_base_not_supplied",
    "deflator_method_not_supplied",
    "denominator_method_not_supplied",
    "financial_year_dates_not_verified",
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
        ("profile", pa.string()),
        ("source_label", pa.string()),
        ("period_token", pa.string()),
        ("period_start", pa.date32()),
        ("period_end", pa.date32()),
        ("amount", pa.decimal128(38, 18)),
        ("value_token", pa.string()),
        ("price_basis", pa.string()),
        ("per_capita", pa.bool_()),
        ("unit", pa.string()),
        ("price_base", pa.string()),
        ("denominator", pa.string()),
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
        ("record_ids", pa.list_(pa.string())),
        ("raw_values_json", pa.string()),
    ]
)


def _require(condition: object) -> None:
    if not condition:
        message = "moh_source_contract"
        raise ValueError(message)


def parse_amount(token: str) -> Decimal:
    """Parse the bounded exact decimal grammar; never infer a missing value."""
    _require(re.fullmatch(r"[+-]?[0-9]{1,20}(\.[0-9]{1,18})?", token) is not None)
    return Decimal(token)


def _rows(payload: bytes, headers: tuple[str, ...]) -> list[dict[str, str]]:
    # BOM is accepted only at the beginning. No multiline CSV or global parser
    # limit changes; original quoting/BOM/line endings stay in immutable Bronze.
    lines = payload.decode("utf-8-sig", errors="strict").splitlines()
    _require(len(lines) == len(PERIODS) + 1)
    parsed = []
    for line in lines:
        _require(len(line) <= MAX_LINE)
        row = next(csv.reader([line], strict=True))
        _require(
            len(row) == len(headers) and all(len(item) <= MAX_FIELD for item in row)
        )
        parsed.append(row)
    _require(tuple(parsed[0]) == headers)
    rows = [dict(zip(headers, row, strict=True)) for row in parsed[1:]]
    _require({row["Year"] for row in rows} == PERIODS)
    return rows


def _extract(
    rows: list[dict[str, str]], context: dict[str, Any], profile: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    facts, lineage, dispositions = [], [], []
    headers = PROFILES[profile]
    for source_row, raw in enumerate(rows, start=2):
        raw_json = encode_json(raw)
        record_ids = []
        for label, basis in zip(headers[1:], ("real", "nominal"), strict=True):
            record_id = identity(
                TRANSFORMATION,
                context["source_object_sha256"],
                profile,
                source_row,
                label,
            )
            record_ids.append(record_id)
            fact = {
                **context,
                "record_id": record_id,
                "schema_version": "archive-govt-nz.health-moh-indicator-silver/v1",
                "recordset": "published_indicator_fact",
                "source_row": source_row,
                "profile": profile,
                "source_label": label,
                "period_token": raw["Year"],
                "period_start": None,
                "period_end": None,
                "amount": parse_amount(raw[label]),
                "value_token": raw[label],
                "price_basis": basis,
                "per_capita": profile == "fig28/v1",
                "unit": None,
                "price_base": None,
                "denominator": None,
                "rights_state": "not_evaluated",
                "quality_flags": list(FLAGS),
                "transformation_id": TRANSFORMATION,
                "lineage_id": identity(record_id, "lineage"),
                "raw_values_json": raw_json,
            }
            facts.append(fact)
            for name in headers:
                field = (
                    "period_token"
                    if name == "Year"
                    else "amount"
                    if name == label
                    else f"raw:{name}"
                )
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
        dispositions.append(
            {
                "source_object_sha256": context["source_object_sha256"],
                "source_locator": context["source_locator"],
                "source_row": source_row,
                "disposition": "normalized",
                "reason": "published_indicators_unknown_metadata",
                "record_ids": record_ids,
                "raw_values_json": raw_json,
            }
        )
    return facts, lineage, dispositions


def normalize_moh_indicators(  # noqa: PLR0913 - explicit provenance and dry-run boundary
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    profile: str,
    observed_at: str,
    source_vintage: str,
    source_locator: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Preflight a reviewed HAIR2024 profile; explicit writes are exclusive.

    These are supplied real/nominal/per-capita labels, not derived measures.
    Unit, price base, denominator and exact fiscal dates remain unknown. Every
    row retains both facts and all decoded fields. Invalid inputs produce no
    outputs; interrupted writes retain partial files without a final manifest.
    """
    _require(profile in PROFILES and source_vintage == "MoH-HAIR-2024")
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    _require(not source.is_symlink() and source.is_file())
    _require(not output_dir.exists() and not output_dir.is_symlink())
    payload = verified_snapshot(source, expected_sha256, max_bytes=MAX_BYTES)
    facts, lineage, dispositions = _extract(
        _rows(payload, PROFILES[profile]), context, profile
    )
    receipt = {
        "schema_version": "archive-govt-nz.health-moh-indicator-extraction/v1",
        "transformation_id": TRANSFORMATION,
        "status": "planned" if dry_run else "passed",
        "source_object_sha256": expected_sha256,
        "source_locator": source_locator,
        "source_vintage": source_vintage,
        "observed_at": context["observed_at"].isoformat(),
        "profile": profile,
        "rights_state": "not_evaluated",
        "quality_flags": list(FLAGS),
        "counts": {
            "input": len(dispositions),
            "facts": len(facts),
            "lineage": len(lineage),
        },
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "moh_indicator_facts.parquet": pa.Table.from_pylist(
                facts, schema=FACT_SCHEMA
            ),
            "field_lineage.parquet": pa.Table.from_pylist(
                lineage, schema=LINEAGE_SCHEMA
            ),
            "row_dispositions.parquet": pa.Table.from_pylist(
                dispositions, schema=DISPOSITION_SCHEMA
            ),
        },
        receipt,
    )
