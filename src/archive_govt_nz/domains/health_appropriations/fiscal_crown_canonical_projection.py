"""Bronze-bound canonical context for historical Fiscal Crown expenses."""

from __future__ import annotations

import hashlib
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import fiscal_crown_literals
from archive_govt_nz.schemas.health_recordsets import recordset_schema

if TYPE_CHECKING:
    from pathlib import Path

TRANSFORMATION = "treasury-fiscal-crown-canonical-source-faithful/v1"
_MAX_PRECISION = 38
_EXPECTED_FACT_COUNT = 61
_EXPECTED_FAMILIES = {"core_crown": 32, "total_crown": 29}
_ERROR = "fiscal_crown_canonical_projection_invalid"


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def canonicalize_fiscal_crown_literals(
    source_facts: list[dict[str, Any]],
) -> tuple[pa.Table, pa.Table]:
    """Map the reviewed Crown literals into canonical facts and direct lineage."""
    _require(len(source_facts) == _EXPECTED_FACT_COUNT)
    _require(len({row["record_id"] for row in source_facts}) == _EXPECTED_FACT_COUNT)
    facts: list[dict[str, Any]] = []
    lineage: list[dict[str, Any]] = []
    for source in source_facts:
        family = source["family"]
        _require(family in {"core_crown", "total_crown"})
        amount = source["amount"]
        amount_token = source["source_number_token"]
        _require(isinstance(amount, Decimal) and amount.is_finite())
        source_amount = Decimal(amount_token)
        _require(source_amount == amount)
        parts = source_amount.as_tuple()
        precision = len(parts.digits)
        scale = max(0, -cast("int", parts.exponent))
        _require(1 <= precision <= _MAX_PRECISION and scale <= precision)
        source_id = source["record_id"]
        identifier = (
            "sha256:"
            + hashlib.sha256(f"{TRANSFORMATION}\0{source_id}".encode()).hexdigest()
        )
        measure = (
            "core_crown_expenses" if family == "core_crown" else "total_crown_expenses"
        )
        year_label = source["year_label"]
        raw = source["raw_context"]
        record = {
            "record_id": identifier,
            "schema_version": "archive-govt-nz.health-recordsets/v1",
            "recordset": "fiscal_context_fact",
            "domain": "health_appropriations",
            "source_object_sha256": source["source_object_sha256"],
            "source_observation_id": source_id,
            "source_locator": source["source_locator"],
            "source_vintage": source["source_vintage"],
            "valid_time_start": None,
            "valid_time_end": source["period_end"],
            "valid_time_status": "june_year_end_start_unqualified",
            "period_token": f"year_label:{year_label}",
            "observed_at": source["observed_at"],
            "observation_context": ("treasury_fiscal_time_series_crown_as_published"),
            "rights_state": "not_evaluated",
            "quality_flags": sorted(
                {
                    "historical_amount_type_as_published",
                    "accounting_basis_source_label_preserved",
                    "consolidation_equivalence_not_asserted",
                    *(
                        f"source_year_note:{item['marker']}"
                        for item in source["source_year_notes"]
                    ),
                }
            ),
            "transformation_id": TRANSFORMATION,
            "lineage_id": hashlib.sha256(f"{identifier}\0lineage".encode()).hexdigest(),
            "source_record_id": source_id,
            "source_schema_version": fiscal_crown_literals.TRANSFORMATION,
            "measure": measure,
            "amount": source_amount,
            "value_token": amount_token,
            "null_reason": None,
            "source_decimal_precision": precision,
            "source_decimal_scale": scale,
            "unit": source["unit"],
            "currency": source["currency"],
            "price_basis": source["price_basis"],
            "base_period": None,
            "denominator_definition": None,
            "amount_type": source["amount_type"],
            "source_label": source["label"],
            "institutional_coverage": family,
            "accounting_basis": source["accounting_basis"],
            "seasonal_adjustment": None,
        }
        facts.append(record)
        links = source["lineage"]
        mappings = (
            ("measure", "label", "measure"),
            ("amount", "amount", "amount"),
            ("value_token", "source_number_token", "value_token"),
            ("period_token", "year_label", "period_token"),
            ("valid_time_end", "period_end", "valid_time_end"),
            ("unit", "unit", "unit"),
            ("amount_type", "year_label", "amount_type"),
            ("source_label", "label", "source_label"),
            ("institutional_coverage", "label", "institutional_coverage"),
            ("accounting_basis", "accounting_basis", "accounting_basis"),
        )
        values = {
            "measure": measure,
            "amount": str(amount),
            "value_token": amount_token,
            "period_token": f"year_label:{year_label}",
            "valid_time_end": source["period_end"].isoformat(),
            "unit": source["unit"],
            "amount_type": source["amount_type"],
            "source_label": source["label"],
            "institutional_coverage": family,
            "accounting_basis": source["accounting_basis"],
        }
        derived_rules = {
            "measure": "/source-label-measure-classification",
            "amount_type": "/historical-as-published-policy",
            "institutional_coverage": "/source-label-coverage-classification",
        }
        for target_field, evidence_field, normalized_field in mappings:
            coordinate = links[evidence_field]
            raw_value = (
                amount_token
                if evidence_field in {"amount", "source_number_token"}
                else str(raw[coordinate])
            )
            lineage.append(
                {
                    "record_id": "sha256:"
                    + hashlib.sha256(
                        f"{identifier}\0{target_field}\0{coordinate}".encode()
                    ).hexdigest(),
                    "schema_version": "archive-govt-nz.health-recordsets/v1",
                    "recordset": "field_lineage",
                    "domain": "health_appropriations",
                    "source_object_sha256": source["source_object_sha256"],
                    "source_observation_id": source_id,
                    "source_locator": source["source_locator"],
                    "source_vintage": source["source_vintage"],
                    "valid_time_start": None,
                    "valid_time_end": source["period_end"],
                    "valid_time_status": "june_year_end_start_unqualified",
                    "period_token": f"year_label:{year_label}",
                    "observed_at": source["observed_at"],
                    "observation_context": (
                        "treasury_fiscal_time_series_crown_as_published"
                    ),
                    "rights_state": "not_evaluated",
                    "quality_flags": record["quality_flags"],
                    "transformation_id": TRANSFORMATION,
                    "lineage_id": record["lineage_id"],
                    "source_record_id": source_id,
                    "source_schema_version": fiscal_crown_literals.TRANSFORMATION,
                    "target_record_id": identifier,
                    "field": target_field,
                    "source_coordinate": coordinate,
                    "raw_value": raw_value,
                    "normalized_value": values[normalized_field],
                    "rule": TRANSFORMATION + derived_rules.get(target_field, ""),
                }
            )
        lineage.append(
            {
                "record_id": "sha256:"
                + hashlib.sha256(
                    f"{identifier}\0valid_time_status\0{links['period_end']}".encode()
                ).hexdigest(),
                "schema_version": "archive-govt-nz.health-recordsets/v1",
                "recordset": "field_lineage",
                "domain": "health_appropriations",
                "source_object_sha256": source["source_object_sha256"],
                "source_observation_id": source_id,
                "source_locator": source["source_locator"],
                "source_vintage": source["source_vintage"],
                "valid_time_start": None,
                "valid_time_end": source["period_end"],
                "valid_time_status": "june_year_end_start_unqualified",
                "period_token": f"year_label:{year_label}",
                "observed_at": source["observed_at"],
                "observation_context": (
                    "treasury_fiscal_time_series_crown_as_published"
                ),
                "rights_state": "not_evaluated",
                "quality_flags": record["quality_flags"],
                "transformation_id": TRANSFORMATION,
                "lineage_id": record["lineage_id"],
                "source_record_id": source_id,
                "source_schema_version": fiscal_crown_literals.TRANSFORMATION,
                "target_record_id": identifier,
                "field": "valid_time_status",
                "source_coordinate": links["period_end"],
                "raw_value": str(raw[links["period_end"]]),
                "normalized_value": record["valid_time_status"],
                "rule": TRANSFORMATION + "/june-year-end-without-start-inference",
            }
        )
    return (
        pa.Table.from_pylist(facts, schema=recordset_schema("fiscal_context_fact")),
        pa.Table.from_pylist(lineage, schema=recordset_schema("field_lineage")),
    )


def project_fiscal_crown(
    source_path: Path,
) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
    """Verify the exact retained Fiscal workbook and project its 61 Crown facts."""
    admitted = fiscal_crown_literals.admit_fiscal_crown(source_path)
    source_facts = admitted["facts"]
    _require(isinstance(source_facts, list))
    _require(admitted["counts"] == _EXPECTED_FAMILIES)
    facts, lineage = canonicalize_fiscal_crown_literals(source_facts)
    return (
        facts,
        lineage,
        {
            "schema_version": (
                "archive-govt-nz.health-fiscal-crown-canonical-projection/v1"
            ),
            "status": "verified_source_faithful_projection",
            "source_object_sha256": fiscal_crown_literals.SOURCE_SHA256,
            "source_vintage": fiscal_crown_literals.VINTAGE,
            "input_records": len(source_facts),
            "output_records": facts.num_rows,
            "output_lineage_rows": lineage.num_rows,
            "core_crown_records": _EXPECTED_FAMILIES["core_crown"],
            "total_crown_records": _EXPECTED_FAMILIES["total_crown"],
            "input_identity_closed": True,
            "currency": "unknown",
            "accounting_basis": "source_label_retained",
            "financial_year_start": "unqualified",
            "rights_state": "not_evaluated",
            "denominator_selection": "not_performed",
            "cross_measure_comparison": "not_performed",
            "publication": "not_performed",
        },
    )
