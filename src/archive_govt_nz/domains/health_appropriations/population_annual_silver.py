"""Context-only Silver admission for the Stats NZ annual mean population export."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import population_annual_export
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    source_context,
    verified_snapshot,
    write_workbook_outputs,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from pathlib import Path

TRANSFORMATION = "stats-nz-population-annual-mean-context/v1"
_CONTRACT_ERROR = "annual_population_silver_contract"
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


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_CONTRACT_ERROR)


def normalize_population_annual(  # noqa: PLR0913 - standard explicit extraction context
    source: Path,
    output_dir: Path,
    *,
    expected_sha256: str,
    observed_at: str,
    source_vintage: str,
    source_locator: str,
    dry_run: bool = True,
) -> dict[str, object]:
    """Preflight or write source-faithful annual population context.

    This does not approve the series as an expenditure denominator or evaluate
    rights. Annual mean year-ended estimates retain their source time basis.
    """
    context = source_context(
        expected_sha256, source_locator, source_vintage, observed_at
    )
    _require(not source.is_symlink() and source.is_file())
    _require(not output_dir.exists() and not output_dir.is_symlink())
    payload = verified_snapshot(
        source, expected_sha256, max_bytes=population_annual_export.MAX_BYTES
    )
    inspection = population_annual_export.inspect_export(
        payload,
        transport=population_annual_export.ExportTransport(None, None, expected_sha256),
    )
    facts: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    dispositions: list[dict[str, Any]] = []
    for item in inspection["facts"]:
        record_id = item["record_id"]
        lineage_id = f"{record_id}:lineage"
        year = int(item["reference_period"][2:])
        raw = {
            "year": str(year),
            "value": item["value_token"],
            "status": item["status"] or "",
        }
        fact = {
            **context,
            "record_id": record_id,
            "schema_version": "archive-govt-nz.health-recordsets/v1",
            "recordset": "price_population_fact",
            "domain": "health_appropriations",
            "valid_time_start": date(year - 1, 7, 1),
            "valid_time_end": date(year, 6, 30),
            "valid_time_status": "source_mean_year_ended",
            "period_token": item["reference_period"],
            "observation_context": (
                "Mean year ended; Total; Total All Ages; denominator not selected"
            ),
            "rights_state": "not_evaluated",
            "quality_flags": [
                "context_only_not_selected_as_denominator",
                "rights_not_evaluated",
                "population_revision_and_census_base_vintages_not_fully_resolved",
                "source_status_preserved_separately",
                "transport_metadata_not_observed",
            ],
            "transformation_id": TRANSFORMATION,
            "lineage_id": lineage_id,
            "source_record_id": None,
            "source_schema_version": (
                "archive-govt-nz.population-annual-export-inspection/v1"
            ),
            "measure": "estimated_resident_population_mean_year_ended",
            "amount": Decimal(item["amount"]) if item["amount"] is not None else None,
            "value_token": item["value_token"],
            "null_reason": item["missing_reason"],
            "source_decimal_precision": None,
            "source_decimal_scale": 0 if item["amount"] is not None else None,
            "unit": "persons",
            "currency": None,
            "price_basis": None,
            "base_period": None,
            "denominator_definition": (
                "Stats NZ DPE056AA Total All Ages estimated resident population; "
                "mean year ended; not analytically selected"
            ),
            "amount_type": "population_estimate",
            "source_label": "Total All Ages",
            "series_id": "DPE056AA:Mean year ended:Total:Total All Ages:Annual-Jun",
            "geography": "New Zealand",
            "population_definition": (
                "Total All Ages estimated resident population; mean year ended"
            ),
            "seasonal_adjustment": "not_applicable",
        }
        dispositions.append(
            {
                "source_object_sha256": expected_sha256,
                "source_locator": source_locator,
                "source_row": item["source_row"],
                "disposition": "source_status_preserved",
                "reason": "publisher_status_token_not_a_shared_fact_field",
                "record_id": record_id,
                "raw_values_json": encode_json(raw),
            }
        )
        facts.append(fact)
        lineage_fields = (("period_token", "year"), ("amount", "value"))
        for field, key in lineage_fields:
            normalized = (
                str(fact["amount"])
                if field == "amount" and fact["amount"] is not None
                else raw[key]
            )
            lineage.append(
                {
                    "lineage_id": lineage_id,
                    "record_id": record_id,
                    "field": field,
                    "source_object_sha256": expected_sha256,
                    "source_locator": source_locator,
                    "source_coordinate": f"csv:row={item['source_row']};column={key}",
                    "raw_value": raw[key],
                    "normalized_value": normalized,
                    "rule": TRANSFORMATION,
                }
            )
    numeric = sum(fact["amount"] is not None for fact in facts)
    provisional = sum(item["status"] == "P" for item in inspection["facts"])
    receipt = {
        "schema_version": "archive-govt-nz.health-population-annual-extraction/v1",
        "transformation_id": TRANSFORMATION,
        "status": "planned" if dry_run else "passed",
        "source_object_sha256": expected_sha256,
        "source_locator": source_locator,
        "source_vintage": source_vintage,
        "observed_at": context["observed_at"].isoformat(),
        "rights_state": "not_evaluated",
        "analytical_selection": "not_selected",
        "counts": {
            "input": len(facts),
            "facts": len(facts),
            "numeric": numeric,
            "missing": len(facts) - numeric,
            "provisional": provisional,
            "lineage": len(lineage),
        },
    }
    if dry_run:
        return receipt
    return write_workbook_outputs(
        output_dir,
        {
            "population_facts.parquet": pa.Table.from_pylist(facts, schema=FACT_SCHEMA),
            "field_lineage.parquet": pa.Table.from_pylist(
                lineage, schema=LINEAGE_SCHEMA
            ),
            "row_dispositions.parquet": pa.Table.from_pylist(
                dispositions, schema=DISPOSITION_SCHEMA
            ),
        },
        receipt,
    )
