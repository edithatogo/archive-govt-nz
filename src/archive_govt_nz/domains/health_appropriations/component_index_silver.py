# SPDX-License-Identifier: Apache-2.0
"""Source-separated Silver facts for two retained Infoshare component indexes."""

from __future__ import annotations

import calendar
import csv
import io
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import (
    component_index_evidence as evidence,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    identity,
    source_context,
    write_workbook_outputs,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from pathlib import Path

TRANSFORMATION = "stats-nz-health-component-index-context/v1"
FACT_SCHEMA = recordset_schema("price_population_fact")
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


def normalize_component_index(
    cas_root: Path, output_dir: Path, *, family: str, dry_run: bool = True
) -> dict[str, object]:
    """Verify the entire retained cohort and plan or write one contextual series."""
    if (
        family not in evidence.EXPORTS
        or type(dry_run) is not bool
        or output_dir.exists()
        or output_dir.is_symlink()
    ):
        msg = "component_index_silver_contract"
        raise ValueError(msg)
    evidence.inspect_component_source_evidence(cas_root)
    profile = evidence.EXPORTS[family]
    capture = next(
        item for item in evidence.CAPTURES if item["role"] == f"{family}-public-get-1"
    )
    body = evidence._snapshot(cas_root, capture["body_sha256"], capture["body_bytes"])  # noqa: SLF001 - reuse exact retained-object verification
    query = evidence._snapshot(cas_root, profile.query_sha256, profile.query_bytes)  # noqa: SLF001 - reuse exact retained-object verification
    evidence.inspect_export(body, query, profile)
    context = source_context(
        capture["body_sha256"],
        capture["requested_url"],
        "2026Q2",
        capture["observed_at"],
    )
    rows = list(csv.reader(io.StringIO(body.decode("utf-8"), newline=""), strict=True))
    rows = rows[len(profile.headers) : len(profile.headers) + len(profile.periods)]
    facts: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    dispositions: list[dict[str, Any]] = []
    for source_row, (period, value) in enumerate(rows, start=len(profile.headers) + 1):
        year, quarter = int(period[:4]), int(period[-1])
        month = quarter * 3
        record_id = identity(
            TRANSFORMATION, capture["body_sha256"], profile.table, source_row
        )
        lineage_id = identity(record_id, "lineage")
        raw = {"period": period, "value": value}
        amount = None if value == ".." else Decimal(value)
        fact = {
            **context,
            "record_id": record_id,
            "schema_version": "archive-govt-nz.health-recordsets/v1",
            "recordset": "price_population_fact",
            "domain": "health_appropriations",
            "valid_time_start": date(year, month - 2, 1),
            "valid_time_end": date(year, month, calendar.monthrange(year, month)[1]),
            "valid_time_status": "source_quarter",
            "period_token": period,
            "observation_context": profile.scope,
            "rights_state": "not_evaluated",
            "quality_flags": [
                "context_only_not_analytically_selected",
                "rights_not_evaluated",
                "source_status_unflagged_unknown",
            ],
            "transformation_id": TRANSFORMATION,
            "lineage_id": lineage_id,
            "source_record_id": None,
            "source_schema_version": (
                "archive-govt-nz.health-component-source-evidence/v1"
            ),
            "measure": f"{family}_health_component_index",
            "amount": amount,
            "value_token": value,
            "null_reason": "publisher_figure_not_available" if amount is None else None,
            "source_decimal_precision": None,
            "source_decimal_scale": (
                len(value.partition(".")[2]) if amount is not None else None
            ),
            "unit": "Index",
            "currency": None,
            "price_basis": None,
            "base_period": "2009Q2=1000" if family == "lci" else "2010Q4=1000",
            "denominator_definition": None,
            "amount_type": "index",
            "source_label": profile.scope,
            "series_id": ":".join(
                [profile.table, *(item[1] for item in profile.selectors)]
            ),
            "geography": "New Zealand",
            "population_definition": None,
            "seasonal_adjustment": None,
        }
        facts.append(fact)
        dispositions.append(
            {
                "source_object_sha256": capture["body_sha256"],
                "source_locator": context["source_locator"],
                "source_row": source_row,
                "disposition": "selected",
                "reason": "source_literal_preserved",
                "record_id": record_id,
                "raw_values_json": encode_json(raw),
            }
        )
        for field, token, column in (
            ("period_token", period, 1),
            ("amount", value, 2),
        ):
            lineage.append(
                {
                    "lineage_id": lineage_id,
                    "record_id": record_id,
                    "field": field,
                    "source_object_sha256": capture["body_sha256"],
                    "source_locator": context["source_locator"],
                    "source_coordinate": f"csv:row={source_row};column={column}",
                    "raw_value": token,
                    "normalized_value": token,
                    "rule": TRANSFORMATION,
                }
            )
    receipt: dict[str, object] = {
        "schema_version": "archive-govt-nz.health-component-index-silver/v1",
        "status": "planned" if dry_run else "passed",
        "family": family,
        "table": profile.table,
        "query_sha256": profile.query_sha256,
        "source_object_sha256": capture["body_sha256"],
        "rights_state": "not_evaluated",
        "analytical_selection": "not_selected",
        "counts": {
            "facts": len(facts),
            "numeric": sum(item["amount"] is not None for item in facts),
            "missing": sum(item["amount"] is None for item in facts),
            "lineage": len(lineage),
        },
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "component_facts.parquet": pa.Table.from_pylist(facts, schema=FACT_SCHEMA),
            "field_lineage.parquet": pa.Table.from_pylist(
                lineage, schema=LINEAGE_SCHEMA
            ),
            "row_dispositions.parquet": pa.Table.from_pylist(
                dispositions, schema=DISPOSITION_SCHEMA
            ),
        },
        receipt,
    )
