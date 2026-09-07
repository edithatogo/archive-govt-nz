"""Pure, bounded assertion contracts; not verified mappings or source authority.

Keys retain literal labels and inclusive effective dates. Unknown endpoints
conservatively overlap every possible date. A snapshot has one assertion per
dimension key; compare separate snapshots for vintage/version changes. Evidence
digests are references only: this module performs no I/O or factual verification.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from itertools import combinations
from typing import TYPE_CHECKING

from archive_govt_nz.schemas.health_recordset_normalization import validate_table

if TYPE_CHECKING:
    import pyarrow as pa

KINDS = frozenset(
    {
        "vote",
        "appropriation",
        "department",
        "portfolio",
        "amount_type",
        "functional_classification",
        "economic_classification",
        "measure",
        "unit",
        "period",
    }
)
MAX_ROWS = 1000
MAX_TEXT = 4096
MAX_EVIDENCE = 32


@dataclass(frozen=True)
class Dimension:
    """Literal source namespace (including scheme version), label and period."""

    kind: str
    scheme: str
    label: str
    start: date | None = None
    end: date | None = None
    period_token: str | None = None


@dataclass(frozen=True)
class Mapping:
    """Caller assertion; target None means unresolved, never an inferred match."""

    dimension: Dimension
    vintage: str
    version: str
    target: str | None = None
    method: str | None = None
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class Drift:
    """Deterministic differences, not approval of either snapshot."""

    key: str
    changes: tuple[str, ...]


def _require(condition: object) -> None:
    if not condition:
        message = "dimension_mapping_contract"
        raise ValueError(message)


def _text(value: object) -> None:
    _require(type(value) is str)
    _require(isinstance(value, str) and 0 < len(value) <= MAX_TEXT and value.strip())


def dimension_key(value: Dimension) -> str:
    """Validate and hash literal identity, without case folding or date inference."""
    _require(type(value) is Dimension)
    for text in (value.kind, value.scheme, value.label):
        _text(text)
    _require(value.kind in KINDS)
    for endpoint in (value.start, value.end):
        _require(endpoint is None or type(endpoint) is date)
    _require(value.start is None or value.end is None or value.start <= value.end)
    if value.period_token is not None:
        _text(value.period_token)
    payload = json.dumps(
        [
            "health-dimension/v1",
            value.kind,
            value.scheme,
            value.label,
            str(value.start),
            str(value.end),
            value.period_token,
        ],
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _mapping(value: Mapping) -> str:
    _require(type(value) is Mapping)
    key = dimension_key(value.dimension)
    _text(value.vintage)
    _text(value.version)
    _require(type(value.evidence) is tuple and len(value.evidence) <= MAX_EVIDENCE)
    for digest in value.evidence:
        _require(type(digest) is str and re.fullmatch(r"[0-9a-f]{64}", digest))
    _require(tuple(sorted(set(value.evidence))) == value.evidence)
    if value.target is None:
        _require(value.method is None and not value.evidence)
    else:
        _text(value.target)
        _text(value.method)
        _require(bool(value.evidence))
    return key


def _overlap(left: Dimension, right: Dimension) -> bool:
    return max(left.start or date.min, right.start or date.min) <= min(
        left.end or date.max,
        right.end or date.max,
    )


def validate_mappings(rows: tuple[Mapping, ...]) -> tuple[Mapping, ...]:
    """Reject duplicate identities and overlapping incompatible assertions.

    This intentionally bounded snapshot check compares at most 499,500 pairs.
    Different vintages/versions belong in separate snapshots, not a precedence
    rule. Unknown versus mapped is also a conflict on overlapping periods.
    """
    _require(type(rows) is tuple and len(rows) <= MAX_ROWS)
    indexed: dict[str, Mapping] = {}
    for row in rows:
        key = _mapping(row)
        _require(key not in indexed)
        indexed[key] = row
    for left, right in combinations(rows, 2):
        a, b = left.dimension, right.dimension
        if (a.kind, a.scheme, a.label) == (b.kind, b.scheme, b.label) and _overlap(
            a, b
        ):
            _require(
                (left.target, left.vintage, left.version)
                == (right.target, right.vintage, right.version)
            )
    return tuple(indexed[key] for key in sorted(indexed))


def compare_mappings(
    before: tuple[Mapping, ...],
    after: tuple[Mapping, ...],
) -> tuple[Drift, ...]:
    """Report additions/removals and target, evidence, method or version drift.

    Effective-period or label changes are removed/added identities, never
    silently joined. Unchanged is structural equality, not factual validation.
    """
    old = {dimension_key(row.dimension): row for row in validate_mappings(before)}
    new = {dimension_key(row.dimension): row for row in validate_mappings(after)}
    result = []
    for key in sorted(old.keys() | new.keys()):
        if key not in old:
            changes = ("added",)
        elif key not in new:
            changes = ("removed",)
        else:
            changes = tuple(
                field
                for field in ("vintage", "version", "target", "method", "evidence")
                if getattr(old[key], field) != getattr(new[key], field)
            )
        if changes:
            result.append(Drift(key, changes))
    return tuple(result)


def unresolved_classification_dimensions(table: pa.Table) -> tuple[Dimension, ...]:
    """Reuse canonical unmapped projections without changing occurrence records.

    This is only a literal dimension view. Source occurrences/lineage remain in
    the caller's original table; pooled keys convey no factual equivalence.
    Mapped rows must instead pass an explicit, evidence-bearing Mapping contract.
    """
    _require(table.num_rows <= MAX_ROWS)
    validate_table("classification_dimension", table)
    dimensions: dict[str, Dimension] = {}
    for row in table.to_pylist():
        _require(row["mapping_state"] == "unmapped")
        _require(row["normalized_identifier"] is None)
        # Only the existing Budget occurrence scheme has a known dimension kind.
        _require(
            row["scheme"] == "budget_workbook_functional_classification_source_label"
        )
        _require(row["scheme_version"] is None)
        value = Dimension(
            "functional_classification",
            row["scheme"],
            row["source_label"],
            row["valid_time_start"],
            row["valid_time_end"],
            row["period_token"],
        )
        dimensions[dimension_key(value)] = value
    return tuple(dimensions[key] for key in sorted(dimensions))
