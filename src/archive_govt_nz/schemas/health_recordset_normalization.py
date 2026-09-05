"""Opt-in exact JSON transport normalization, not source or rights approval.

Callers supply decoded rows, retain originals and enforce package bounds.
Input order and identifiers are preserved. This boundary checks local numeric
and temporal consistency, not ID derivation, unit interpretation, classification
mapping, formula freshness, source fixity or cross-record lineage closure.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Never, cast

import jsonschema
import pyarrow as pa

from archive_govt_nz.schemas.health_recordset_json import recordset_json_schema
from archive_govt_nz.schemas.health_recordsets import recordset_schema

_TIMESTAMP = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}[Tt][0-9]{2}:[0-9]{2}:[0-9]{2}"
    r"(?:\.[0-9]{1,6})?(?:[Zz]|[+-][0-9]{2}:[0-9]{2})"
)
_MAX_PRECISION = 38
_MAX_ROWS = 100_000
_MAX_BYTES = 8 * 1024 * 1024
_ERROR = "health_recordset_normalization"


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
    max_rows: int = _MAX_ROWS,
) -> pa.Table:
    """Return fresh typed rows without rounding, dropping or sorting records.

    Unknown contracts raise KeyError. Invalid rows raise a redacted ValueError.
    Nullable units/dates and supplied rights labels are preserved, not approved.
    JSON decoding and duplicate JSON member detection belong to the caller.
    """
    schema = recordset_schema(name, version=version)
    _require(type(max_rows) is int and max_rows >= 0)
    _require(isinstance(rows, list) and len(rows) <= max_rows)
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
        # RFC 3339 -00:00 means an unknown local offset, not known UTC.
        _require(not row["observed_at"].endswith("-00:00"))
        try:
            row["observed_at"] = datetime.fromisoformat(
                row["observed_at"].upper()
            ).astimezone(UTC)
        except OverflowError:
            raise ValueError(_ERROR) from None
        for field in ("valid_time_start", "valid_time_end"):
            if row[field] is not None:
                row[field] = date.fromisoformat(row[field])
        start, end = row["valid_time_start"], row["valid_time_end"]
        _require(start is None or end is None or start <= end)
        if "amount" in row:
            _number(row)
        converted.append(row)
    try:
        return pa.Table.from_pylist(converted, schema=schema)
    except UnicodeEncodeError, pa.ArrowException:
        raise ValueError(_ERROR) from None


def _unique_members(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _reject_constant(_value: str) -> Never:
    raise ValueError(_ERROR)


def normalize_json(
    name: str,
    payload: bytes,
    *,
    version: str = "v1",
    max_bytes: int = _MAX_BYTES,
    max_rows: int = _MAX_ROWS,
) -> pa.Table:
    """Normalize a bounded UTF-8 JSON array without binary/text heuristics.

    Reject duplicate members at every depth, nonfinite constants, BOMs and
    malformed UTF-8/JSON. No source format is inferred and no I/O occurs.
    The byte budget bounds parsing; the row budget bounds Arrow conversion.
    """
    recordset_schema(name, version=version)
    _require(type(max_bytes) is int and max_bytes > 0)
    _require(isinstance(payload, bytes) and len(payload) <= max_bytes)
    try:
        rows = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_unique_members,
            parse_constant=_reject_constant,
        )
    except ValueError, RecursionError:
        raise ValueError(_ERROR) from None
    return normalize_rows(name, rows, version=version, max_rows=max_rows)


def validate_table(
    name: str,
    table: pa.Table,
    *,
    version: str = "v1",
    max_rows: int = _MAX_ROWS,
    max_bytes: int = _MAX_BYTES,
) -> None:
    """Revalidate bounded Arrow or caller-decoded Parquet rows and metadata.

    Exact schema equality includes metadata and nullability. Arrow's schema
    alone does not enforce nonnull values or row constants. Readback here checks
    those and the same numeric/time/ID invariants as JSON admission. Parquet
    decoding, file bounds and fixity verification remain caller responsibilities.
    """
    schema = recordset_schema(name, version=version)
    _require(type(max_rows) is int and max_rows >= 0)
    _require(type(max_bytes) is int and max_bytes >= 0)
    _require(isinstance(table, pa.Table))
    _require(table.num_rows <= max_rows and table.nbytes <= max_bytes)
    _require(table.schema.equals(schema, check_metadata=True))
    try:
        rows = table.to_pylist()
    except OverflowError, pa.ArrowException:
        raise ValueError(_ERROR) from None
    for row in rows:
        for field, value in row.items():
            if isinstance(value, date):
                row[field] = value.isoformat()
            elif isinstance(value, Decimal):
                row[field] = format(value, "f")
    normalize_rows(name, rows, version=version, max_rows=max_rows)
