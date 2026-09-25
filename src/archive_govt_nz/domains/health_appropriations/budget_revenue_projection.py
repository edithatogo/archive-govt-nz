"""Source-faithful canonical Budget revenue facts, never expenditure facts."""

# ruff: noqa: PLR2004

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, cast

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations.budget_revenue import (
    DISPOSITION_SCHEMA,
    FACT_SCHEMA,
    TRANSFORMATION,
    TRANSFORMATION_2026,
)
from archive_govt_nz.domains.health_appropriations.silver import LINEAGE_SCHEMA
from archive_govt_nz.schemas.health_recordsets import recordset_schema

RULE = "budget-revenue-canonical/v1"
_MANIFEST = "archive-govt-nz.health-budget-revenue-extraction/v1"
_SOURCE_VERSION = "archive-govt-nz.health-budget-revenue-fact/v1"
_MAX_ROWS = 100_000
_CONTEXT = (
    "source_object_sha256",
    "source_observation_id",
    "source_locator",
    "source_vintage",
    "observed_at",
    "rights_state",
)
_LINKS = {
    "amount": ("amount", "value_token"),
    "year": ("period_token",),
    "description": ("source_label",),
    "revenue_type": ("revenue_type",),
    "department": ("department",),
    "vote": ("vote",),
    "app_id": ("source_application_id",),
    "amount_type": ("amount_type",),
}
_FACT_TRANSPORT_SCHEMA = pa.schema(
    [
        field.with_type(pa.list_(pa.field("element", pa.string())))
        if field.name == "quality_flags"
        else field
        for field in FACT_SCHEMA
    ],
    metadata=FACT_SCHEMA.metadata,
)


@dataclass(frozen=True)
class BudgetRevenueProjection:
    """Fresh source-faithful canonical tables and a bounded projection receipt."""

    tables: dict[str, pa.Table]
    receipt: dict[str, Any]


def _require(value: object) -> None:
    if not value:
        message = "budget_revenue_projection_contract"
        raise ValueError(message)


def _id(*parts: object) -> str:
    payload = json.dumps(
        parts, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()


def _amount(value: object, token: object) -> Decimal:
    _require(isinstance(value, Decimal) and value.is_finite())
    _require(isinstance(token, str) and 0 < len(token) <= 256)
    parsed = Decimal(cast("str", token))
    _require(parsed.is_finite() and parsed == value)
    parts = parsed.as_tuple()
    _require(
        len(parts.digits) <= 20
        and isinstance(parts.exponent, int)
        and parts.exponent >= -3
    )
    return parsed


def project_budget_revenue(
    *,
    manifest: dict[str, Any],
    manifest_sha256: str,
    facts: pa.Table,
    lineage: pa.Table,
    dispositions: pa.Table,
) -> BudgetRevenueProjection:
    """Project verified extraction tables without reading files or inferring rights.

    The resulting ``revenue_fact`` table remains a separate recordset.  It must
    never be unioned with appropriations or treated as net expenditure.
    """
    try:
        _require(isinstance(manifest_sha256, str) and len(manifest_sha256) == 64)
        _require(manifest["schema_version"] == _MANIFEST)
        _require(manifest["transformation_id"] in {TRANSFORMATION, TRANSFORMATION_2026})
        _require(manifest["rights_state"] == "not_evaluated")
        _require(manifest["status"] in {"passed", "partial"})
        _require(
            facts.schema.equals(FACT_SCHEMA, check_metadata=True)
            or facts.schema.equals(_FACT_TRANSPORT_SCHEMA, check_metadata=True)
        )
        _require(lineage.schema.equals(LINEAGE_SCHEMA, check_metadata=True))
        _require(dispositions.schema.equals(DISPOSITION_SCHEMA, check_metadata=True))
        _require(0 < facts.num_rows <= _MAX_ROWS)
        _require(datetime.fromisoformat(manifest["observed_at"]).tzinfo is not None)
        rows, source_links, disposition_rows = (
            facts.to_pylist(),
            lineage.to_pylist(),
            dispositions.to_pylist(),
        )
        _require(
            all(
                row["disposition"] != "normalized" or row["record_id"]
                for row in disposition_rows
            )
        )
        _require(manifest["counts"]["normalized"] == len(rows))
        by_record: dict[str, dict[str, dict[str, Any]]] = {}
        for link in sorted(
            source_links,
            key=lambda item: (
                item["record_id"],
                item["field"],
                item["source_coordinate"],
            ),
        ):
            by_record.setdefault(link["record_id"], {})[link["field"]] = link
        _require(len(by_record) == len(rows))
        records, output_links = [], []
        for row in rows:
            _require(
                all(
                    row[key] == manifest[key]
                    for key in _CONTEXT
                    if key not in {"source_observation_id", "observed_at"}
                )
            )
            _require(
                row["observed_at"] == datetime.fromisoformat(manifest["observed_at"])
            )
            _require(row["schema_version"] == _SOURCE_VERSION)
            _require(row["recordset"] == "budget_revenue_fact")
            _require(row["transformation_id"] == manifest["transformation_id"])
            _require(row["revenue_type"] in {"Non-Tax Revenue", "Capital Receipts"})
            links = by_record[row["record_id"]]
            _require(
                {
                    "amount",
                    "year",
                    "description",
                    "revenue_type",
                    "app_id",
                    "amount_type",
                }
                <= set(links)
            )
            record_id = _id(RULE, manifest_sha256, row["record_id"])
            record = dict.fromkeys(recordset_schema("revenue_fact").names)
            for field in _CONTEXT:
                record[field] = row[field]
            record.update(
                record_id=record_id,
                schema_version="archive-govt-nz.health-recordsets/v1",
                recordset="revenue_fact",
                domain="health_appropriations",
                source_record_id=row["record_id"],
                source_schema_version=row["schema_version"],
                transformation_id=RULE,
                lineage_id=_id(record_id, "lineage"),
                observation_context="caller_supplied_extraction_observation",
                valid_time_status="source_period_end_only",
                period_token=str(row["year"]),
                valid_time_end=row["valid_time_end"],
                measure="crown_revenue_or_capital_receipt",
                amount=_amount(row["amount"], row["source_number_token"]),
                value_token=row["source_number_token"],
                source_decimal_precision=20,
                source_decimal_scale=3,
                unit=row["unit"],
                amount_type=row["amount_type"],
                source_label=row["description"],
                vote=row["vote"],
                department=row["department"],
                revenue_type=row["revenue_type"],
                source_application_id=row["app_id"],
                quality_flags=[
                    *row["quality_flags"],
                    "revenue_not_netted_with_expenditure",
                    "currency_not_independently_established",
                ],
            )
            records.append(record)
            for source_field, targets in _LINKS.items():
                link = links.get(source_field)
                if link is None:
                    continue
                for target in targets:
                    value = record[target]
                    output_links.append(
                        {
                            "record_id": _id(
                                RULE, manifest_sha256, row["record_id"], target
                            ),
                            "schema_version": record["schema_version"],
                            "recordset": "field_lineage",
                            "domain": record["domain"],
                            "source_object_sha256": record["source_object_sha256"],
                            "source_observation_id": record["source_observation_id"],
                            "source_locator": record["source_locator"],
                            "source_vintage": record["source_vintage"],
                            "valid_time_start": None,
                            "valid_time_end": None,
                            "valid_time_status": "not_applicable",
                            "period_token": None,
                            "observed_at": record["observed_at"],
                            "observation_context": record["observation_context"],
                            "rights_state": record["rights_state"],
                            "quality_flags": [],
                            "transformation_id": RULE,
                            "lineage_id": record["lineage_id"],
                            "source_record_id": record["source_record_id"],
                            "source_schema_version": record["source_schema_version"],
                            "target_record_id": record_id,
                            "field": target,
                            "source_coordinate": link["source_coordinate"],
                            "raw_value": link["raw_value"],
                            "normalized_value": str(value),
                            "rule": RULE,
                        }
                    )
        _require(len({row["record_id"] for row in records}) == len(records))
        tables = {
            "revenue_fact": pa.Table.from_pylist(
                sorted(records, key=lambda row: row["record_id"]),
                schema=recordset_schema("revenue_fact"),
            ),
            "field_lineage": pa.Table.from_pylist(
                sorted(output_links, key=lambda row: row["record_id"]),
                schema=recordset_schema("field_lineage"),
            ),
        }
        return BudgetRevenueProjection(
            tables,
            {
                "schema_version": "archive-govt-nz.health-budget-revenue-projection/v1",
                "status": "passed",
                "input_fixity": "not_performed",
                "input_manifest_sha256": manifest_sha256,
                "rights_state": "not_evaluated",
                "publication_approval": "not_granted",
                "aggregation": "none",
                "netting": "prohibited",
                "authoritative_mapping": "not_performed",
            },
        )
    except ValueError, TypeError, KeyError, pa.ArrowException:
        message = "budget_revenue_projection_contract"
        raise ValueError(message) from None
