"""Explicit legacy population projection; full common evidence stays in manifest.

The legacy table retains two lineage fields, a raw-year normalized token and
native rule. The common representation has three fields including publisher
status and dedicated rules; these are not silently substituted or dropped.
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations.population_annual_silver import (
    DISPOSITION_SCHEMA,
    FACT_SCHEMA,
    TRANSFORMATION,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.domains.health_appropriations.workbook_common import encode_json

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
        AdapterOutput,
    )


def project_population(
    output: AdapterOutput, context: dict[str, Any]
) -> tuple[dict[str, pa.Table], dict[str, int]]:
    """Consume common rows and source links; explicitly render the native schema."""
    expected_sha256 = context["source_object_sha256"]
    source_locator = context["source_locator"]
    facts: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    dispositions: list[dict[str, Any]] = []
    for item in output.records:
        record_id = item["record_id"]
        lineage_id = f"{record_id}:lineage"
        year = int(str(item["reference_period"])[2:])
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
            "amount": item["amount"],
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
        common_fields = {
            row.field: row for row in output.lineage if row.record_id == record_id
        }
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
                    "source_coordinate": common_fields[field].source_coordinate,
                    "raw_value": common_fields[field].raw_value,
                    "normalized_value": normalized,
                    "rule": TRANSFORMATION,
                }
            )
    numeric = sum(fact["amount"] is not None for fact in facts)
    return {
        "population_facts.parquet": pa.Table.from_pylist(facts, FACT_SCHEMA),
        "field_lineage.parquet": pa.Table.from_pylist(lineage, LINEAGE_SCHEMA),
        "row_dispositions.parquet": pa.Table.from_pylist(
            dispositions, DISPOSITION_SCHEMA
        ),
    }, {
        "input": len(facts),
        "facts": len(facts),
        "numeric": numeric,
        "missing": len(facts) - numeric,
        "provisional": sum(item["status"] == "P" for item in output.records),
        "lineage": len(lineage),
    }
