"""Opt-in exact JSON transport normalization, not source or rights approval.

Callers supply decoded rows, retain originals and enforce package bounds.
Input order and identifiers are preserved. This boundary checks local numeric
and temporal consistency, not ID derivation, unit interpretation, classification
mapping, formula freshness, source fixity or cross-record lineage closure.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any, cast

import jsonschema
import pyarrow as pa

from archive_govt_nz.schemas.health_recordset_json import recordset_json_schema
from archive_govt_nz.schemas.health_recordsets import recordset_schema

_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})"
)
_MAX_PRECISION = 38


def _require(condition: object) -> None:
    if not condition:
        message = "health_recordset_normalization"
        raise ValueError(message)


def _number(row: dict[str, Any]) -> None:
    amount = row["amount"]
    reason = row["null_reason"]
    _require(
        isinstance(reason, str) and bool(reason.strip())
        if amount is None
        else reason is None
    )
    precision, scale = row["source_decimal_precision"], row["source_decimal_scale"]
    if precision is None and scale is None:
        _require(amount is None)
        return
    _require(type(precision) is int and type(scale) is int)
    precision, scale = cast("int", precision), cast("int", scale)
    _require(1 <= precision <= _MAX_PRECISION and 0 <= scale <= precision)
    if amount is None:
        return
    value = Decimal(amount)
    parts = value.as_tuple()
    coefficient = int("".join(map(str, parts.digits)))
    exponent = int(parts.exponent) + scale
    if exponent < 0:
        coefficient, remainder = divmod(coefficient, 10**-exponent)
        _require(remainder == 0)
    else:
        coefficient *= 10**exponent
    _require(coefficient < 10**precision)
    row["amount"] = value


def normalize_rows(
    name: str,
    rows: list[dict[str, Any]],
    *,
    version: str = "v1",
) -> pa.Table:
    """Return fresh typed rows without rounding, dropping or sorting records.

    Unknown contracts raise KeyError. Invalid rows raise a redacted ValueError.
    Nullable units/dates and supplied rights labels are preserved, not approved.
    JSON decoding and duplicate JSON member detection belong to the caller.
    """
    schema = recordset_schema(name, version=version)
    validator = jsonschema.Draft202012Validator(
        recordset_json_schema(name, version=version),
        format_checker=jsonschema.FormatChecker(),
    )
    converted: list[dict[str, Any]] = []
    seen: set[str] = set()
    for original in rows:
        _require(validator.is_valid(original))
        row = dict(original)
        identifier = row["record_id"]
        _require(bool(identifier.strip()) and identifier not in seen)
        seen.add(identifier)
        _require(_TIMESTAMP.fullmatch(row["observed_at"]) is not None)
        row["observed_at"] = datetime.fromisoformat(row["observed_at"].upper())
        for field in ("valid_time_start", "valid_time_end"):
            if row[field] is not None:
                row[field] = date.fromisoformat(row[field])
        start, end = row["valid_time_start"], row["valid_time_end"]
        _require(start is None or end is None or start <= end)
        if "amount" in row:
            _number(row)
        converted.append(row)
    return pa.Table.from_pylist(converted, schema=schema)
