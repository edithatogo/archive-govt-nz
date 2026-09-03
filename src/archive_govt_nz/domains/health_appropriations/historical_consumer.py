"""Pure, bounded bridge from verified historical projection to analysis inputs.

This module performs no I/O.  It verifies caller-supplied canonical tables and
their parent projection receipt against a fresh public projection, then returns
deep-copied inputs and reversible accounting for a downstream pure consumer.
It does not establish file fixity, source rights, publication approval, or an
analysis result.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from decimal import DecimalException
from typing import Any, cast

import pyarrow as pa

from archive_govt_nz.domains.health_appropriations.historical_projection import (
    project_historical,
)

_RULE = "historical-health-gdp-canonical/v1"
_TABLES = ("health_spending_fact", "fiscal_context_fact", "field_lineage")
_FACTS = _TABLES[:2]
_MAX_ROWS = 100_000
_MAX_TABLE_BYTES = 64 << 20
_MAX_RECEIPT_BYTES = 4 << 20
_ERROR = "historical_consumer_contract"
_CONSUMER_FIELDS = (
    "record_id",
    "source_object_sha256",
    "source_vintage",
    "year",
    "measure",
    "unit",
    "amount",
    "accounting_basis",
    "valid_time_end",
    "period_end_month",
)


@dataclass(frozen=True)
class HistoricalConsumer:
    """Verified, copied inputs and accounting; not an executed analysis."""

    inputs: tuple[dict[str, Any], ...]
    canonical_lineage: tuple[dict[str, Any], ...]
    parent_receipt: dict[str, Any]
    backward_ids: tuple[dict[str, str], ...]
    field_accounting: tuple[dict[str, Any], ...]
    receipt: dict[str, Any]


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode()


def _verified_receipt(payload: object, expected: dict[str, Any]) -> dict[str, Any]:
    _require(type(payload) is bytes and len(payload) <= _MAX_RECEIPT_BYTES)
    raw = cast("bytes", payload)
    parsed = json.loads(raw)
    _require(isinstance(parsed, dict))
    # Exact canonical bytes deliberately distinguish true, 1 and 1.0.
    _require(raw == _canonical_json(expected))
    return deepcopy(parsed)


def _verified_tables(
    supplied: object, expected: dict[str, pa.Table]
) -> dict[str, pa.Table]:
    _require(isinstance(supplied, dict) and set(supplied) == set(_TABLES))
    mapping = cast("dict[str, object]", supplied)
    result: dict[str, pa.Table] = {}
    for name in _TABLES:
        table = mapping[name]
        _require(isinstance(table, pa.Table))
        table = cast("pa.Table", table)
        _require(0 <= table.num_rows <= _MAX_ROWS and table.nbytes <= _MAX_TABLE_BYTES)
        _require(table.schema.equals(expected[name].schema, check_metadata=True))
        _require(table.equals(expected[name]))
        result[name] = table
    return result


def _backward_ids(tables: dict[str, pa.Table]) -> tuple[dict[str, str], ...]:
    rows = []
    for name in _TABLES:
        for row in tables[name].to_pylist():
            canonical = row["record_id"]
            source = row["source_record_id"]
            _require(isinstance(canonical, str) and isinstance(source, str))
            rows.append(
                {
                    "canonical_record_id": canonical,
                    "source_record_id": source,
                }
            )
    _require(len({row["canonical_record_id"] for row in rows}) == len(rows))
    return tuple(sorted(rows, key=lambda row: row["canonical_record_id"]))


def _field_accounting(
    facts: list[dict[str, Any]], lineage: list[dict[str, Any]]
) -> tuple[dict[str, Any], ...]:
    indexed: dict[tuple[str, str], list[str]] = {}
    for link in lineage:
        key = (link["target_record_id"], link["field"])
        indexed.setdefault(key, []).append(link["record_id"])
    accounting = []
    for fact in facts:
        for field in _CONSUMER_FIELDS:
            ids = sorted(indexed.get((fact["record_id"], field), ()))
            accounting.append(
                {
                    "canonical_record_id": fact["record_id"],
                    "field": field,
                    "state": (
                        "canonical_lineage" if ids else "canonical_metadata_transport"
                    ),
                    "canonical_lineage_record_ids": ids,
                }
            )
    return tuple(
        sorted(accounting, key=lambda row: (row["canonical_record_id"], row["field"]))
    )


def _consumer_facts(tables: dict[str, pa.Table]) -> list[dict[str, Any]]:
    rows = [row for name in _FACTS for row in tables[name].to_pylist()]
    for row in rows:
        end = row["valid_time_end"]
        token = row["period_token"]
        _require(isinstance(end, date))
        end = cast("date", end)
        _require(
            end.month in (3, 6)
            and isinstance(token, str)
            and re.fullmatch(str(end.year) + r"[†*^#]*", token) is not None
        )
        row["year"] = end.year
        row["period_end_month"] = end.month
    return rows


def bridge_historical_inputs(  # noqa: PLR0913 - mirrors the public pure projector plus its verified products
    *,
    manifest: dict[str, Any],
    manifest_sha256: str,
    facts: pa.Table,
    lineage: pa.Table,
    dispositions: pa.Table,
    canonical_tables: dict[str, pa.Table],
    parent_receipt: bytes,
) -> HistoricalConsumer:
    """Verify an exact canonical projection and prepare pure analysis inputs.

    Caller-owned objects are never changed.  Physical canonical row order is
    part of the contract; consumers cannot silently reorder or substitute IDs.
    Base exceptions such as ``KeyboardInterrupt`` propagate unchanged.
    """
    try:
        _require(type(manifest_sha256) is str)
        projected = project_historical(
            manifest=manifest,
            manifest_sha256=manifest_sha256,
            facts=facts,
            lineage=lineage,
            dispositions=dispositions,
        )
        verified = _verified_tables(canonical_tables, projected.tables)
        _require(
            sum(verified[name].num_rows for name in _FACTS) > 0
            and verified["field_lineage"].num_rows > 0
        )
        receipt = _verified_receipt(parent_receipt, projected.receipt)
        fact_rows = _consumer_facts(verified)
        lineage_rows = verified["field_lineage"].to_pylist()
        backward = _backward_ids(verified)
        accounting = _field_accounting(fact_rows, lineage_rows)
        result_receipt = {
            "schema_version": "archive-govt-nz.health-historical-consumer/v1",
            "status": "passed",
            "input_fixity": "not_performed",
            "rights_state": "not_evaluated",
            "publication_approval": "not_granted",
            "analysis_execution": "not_performed",
            "new_semantic_assertions": [],
            "canonical_projection_rule": _RULE,
            "input_manifest_sha256": manifest_sha256,
            "canonical_record_count": sum(verified[name].num_rows for name in _TABLES),
            "consumer_fact_count": len(fact_rows),
            "backward_identity_count": len(backward),
            "field_accounting_count": len(accounting),
        }
        return HistoricalConsumer(
            tuple(deepcopy(fact_rows)),
            tuple(deepcopy(lineage_rows)),
            receipt,
            backward,
            accounting,
            result_receipt,
        )
    except (
        DecimalException,
        KeyError,
        OverflowError,
        TypeError,
        ValueError,
        pa.ArrowException,
    ):
        raise ValueError(_ERROR) from None
