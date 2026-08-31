"""Pure canonical Budget facts; extraction tokens are not original OOXML tokens."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from types import MappingProxyType
from typing import Any

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations.budget_classification import (
    project_budget_classification,
)
from archive_govt_nz.domains.health_appropriations.silver import SILVER_SCHEMA
from archive_govt_nz.schemas.health_recordsets import recordset_schema

RULE = "budget-appropriation-canonical/v1"
_SOURCE_PRECISION = 20
_SOURCE_SCALE = 3
_MAX_TOKEN_LENGTH = 256
_TARGETS = MappingProxyType(
    {
        "amount": ("amount", "value_token"),
        "year": ("period_token",),
        "department": ("department",),
        "appropriation_name": ("appropriation", "source_label"),
        "portfolio_name": ("portfolio",),
        "amount_type": ("amount_type",),
        "raw:Vote": ("vote",),
        "functional_classification": ("classification_ids",),
    }
)
_CONTEXT = (
    "source_object_sha256",
    "source_observation_id",
    "source_locator",
    "source_vintage",
    "observed_at",
    "rights_state",
)
_SOURCE_FIELDS = MappingProxyType(
    {
        "record_id": ("source_record_id",),
        "schema_version": ("source_schema_version",),
        "recordset": ("recordset",),
        **{name: (name,) for name in _CONTEXT},
        "valid_time_start": ("valid_time_start",),
        "quality_flags": ("quality_flags",),
        "year": ("period_token",),
        "department": ("department",),
        "appropriation_name": ("appropriation", "source_label"),
        "functional_classification": ("classification_ids",),
        "amount_type": ("amount_type",),
        "portfolio_name": ("portfolio",),
        "measure": ("measure",),
        "amount": ("amount",),
        "unit": ("unit",),
    }
)


@dataclass(frozen=True)
class BudgetProjection:
    """Fresh canonical tables and complete original lineage/field accounting."""

    tables: dict[str, pa.Table]
    receipt: dict[str, Any]


def _require(condition: object) -> None:
    if not condition:
        message = "budget_projection_contract"
        raise ValueError(message)


def _id(*parts: object) -> str:
    payload = json.dumps(
        parts,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def _amount(value: object, token: object) -> Decimal:
    _require(isinstance(value, Decimal) and value.is_finite())
    _require(isinstance(token, str) and 0 < len(token) <= _MAX_TOKEN_LENGTH)
    number = Decimal(str(token))
    _require(number.is_finite() and number == value)
    amount = Decimal(str(value))
    parts = amount.as_tuple()
    _require(
        parts.exponent == -_SOURCE_SCALE and len(parts.digits) <= _SOURCE_PRECISION
    )
    return amount


def _normalized(value: object) -> str:
    if isinstance(value, Decimal):
        return format(value, ".18f")
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def _fact(
    row: dict[str, Any],
    links: dict[str, dict[str, Any]],
    dimension: dict[str, Any],
    pin: str,
) -> dict[str, Any]:
    record = dict.fromkeys(recordset_schema("appropriation_fact").names)
    for field in _CONTEXT:
        record[field] = row[field]
    record_id = _id(
        RULE,
        pin,
        row["source_object_sha256"],
        row["source_vintage"],
        row["record_id"],
        "appropriation_fact",
    )
    record.update(
        record_id=record_id,
        schema_version="archive-govt-nz.health-recordsets/v1",
        recordset="appropriation_fact",
        domain="health_appropriations",
        source_record_id=row["record_id"],
        source_schema_version=row["schema_version"],
        transformation_id=RULE,
        lineage_id=_id(record_id, "lineage"),
        observation_context="caller_supplied_extraction_observation",
        valid_time_status="not_established",
        period_token=links["year"]["raw_value"],
        quality_flags=[
            *row["quality_flags"],
            "value_token_from_extraction_lineage",
            "source_classification_label_unmapped",
            "unit_inherited_from_source_adapter",
            "currency_not_independently_established",
        ],
        measure=row["measure"],
        amount=_amount(row["amount"], links["amount"]["raw_value"]),
        value_token=links["amount"]["raw_value"],
        source_decimal_precision=_SOURCE_PRECISION,
        source_decimal_scale=_SOURCE_SCALE,
        unit=row["unit"],
        amount_type=row["amount_type"],
        source_label=row["appropriation_name"],
        vote=links["raw:Vote"]["raw_value"],
        appropriation=row["appropriation_name"],
        department=row["department"],
        portfolio=row["portfolio_name"],
        classification_ids=[dimension["record_id"]],
    )
    return record


def project_budget_appropriations(
    *,
    manifest: dict[str, Any],
    manifest_sha256: str,
    facts: pa.Table,
    lineage: pa.Table,
    dispositions: pa.Table,
) -> BudgetProjection:
    """Compose pure source validation; never read files or grant publication rights.

    Caller retains and verifies source packages. Decimal(20,3) source amounts are
    copied exactly into Decimal(38,18); value tokens describe extraction lineage,
    not independently verified literal workbook numeric tokens. The parent uses
    bounded Decimal arithmetic, isolated here from caller precision/traps.
    """
    with localcontext(Context(prec=50)):
        parent = project_budget_classification(
            manifest=manifest,
            manifest_sha256=manifest_sha256,
            facts=facts,
            lineage=lineage,
            dispositions=dispositions,
        )
    dimensions = {
        row["source_record_id"]: row
        for row in parent.tables["classification_dimension"].to_pylist()
    }
    links = lineage.to_pylist()
    grouped: dict[str, dict[str, dict[str, Any]]] = {}
    for link in links:
        grouped.setdefault(link["record_id"], {})[link["field"]] = link
    records = {
        row["record_id"]: _fact(
            row,
            grouped[row["record_id"]],
            dimensions[row["record_id"]],
            manifest_sha256,
        )
        for row in facts.to_pylist()
    }
    accounting = {
        entry["source_lineage_id"]: {
            **entry,
            "target_lineage_record_ids": list(entry["target_lineage_record_ids"]),
        }
        for entry in parent.receipt["lineage_accounting"]
    }
    output_links = parent.tables["field_lineage"].to_pylist()
    for link in links:
        source_id = _id(manifest_sha256, link)
        fact = records[link["record_id"]]
        entry = accounting[source_id]
        for target in _TARGETS.get(link["field"], ()):
            record = {
                key: fact[key]
                for key in recordset_schema("field_lineage").names
                if key in fact
            }
            record_id = _id(
                RULE,
                manifest_sha256,
                fact["source_object_sha256"],
                fact["source_vintage"],
                fact["source_record_id"],
                target,
            )
            value = fact[target]
            record.update(
                record_id=record_id,
                recordset="field_lineage",
                source_schema_version=manifest["schema_version"],
                target_record_id=fact["record_id"],
                field=target,
                source_coordinate=link["source_coordinate"],
                raw_value=link["raw_value"],
                normalized_value=_normalized(value),
                rule=RULE,
            )
            output_links.append(record)
            entry["target_lineage_record_ids"].append(record_id)
            entry["state"] = "mapped"
    for entry in accounting.values():
        entry["target_lineage_record_ids"].sort()
    tables = {
        name: pa.Table.from_pylist(
            sorted(values, key=lambda row: row["record_id"]),
            schema=recordset_schema(name),
        )
        for name, values in (
            ("appropriation_fact", list(records.values())),
            ("field_lineage", output_links),
        )
    }
    tables["classification_dimension"] = parent.tables["classification_dimension"]
    return BudgetProjection(
        tables,
        {
            "schema_version": (
                "archive-govt-nz.health-budget-appropriation-projection/v1"
            ),
            "status": "passed",
            "input_fixity": "not_performed",
            "input_manifest_sha256": manifest_sha256,
            "rights_state": "not_evaluated",
            "publication_approval": "not_granted",
            "authoritative_mapping": "not_performed",
            "inherited_field_scope": {
                "unit": "source_adapter_assertion_not_independently_established",
                "measure": "source_adapter_assertion",
                "source_decimal_precision": "physical_source_arrow_schema",
                "source_decimal_scale": "physical_source_arrow_schema",
                "source_observation_id": (
                    "caller_extraction_context_format_checked_not_preimage_verified"
                ),
                "observed_at": (
                    "caller_supplied_extraction_observation_not_capture_attestation"
                ),
            },
            "value_token_scope": "source_extraction_lineage_not_original_ooxml_token",
            "lineage_accounting": sorted(
                accounting.values(), key=lambda row: row["source_lineage_id"]
            ),
            "retained_source_fields": [
                name for name in SILVER_SCHEMA.names if name not in _SOURCE_FIELDS
            ],
            "source_field_accounting": [
                {
                    "field": name,
                    "state": "mapped" if name in _SOURCE_FIELDS else "retained_only",
                    "target_fields": list(_SOURCE_FIELDS.get(name, ())),
                }
                for name in SILVER_SCHEMA.names
            ],
        },
    )
