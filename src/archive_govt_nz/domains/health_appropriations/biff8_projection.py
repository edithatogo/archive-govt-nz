"""Explicit numeric projection for BIFF8 facts; literal-token consumers stay closed."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import pyarrow as pa
from openpyxl.utils.cell import get_column_letter

from archive_govt_nz.domains.health_appropriations.biff8_records import NumericWitness
from archive_govt_nz.domains.health_appropriations.workbook_common import exact_number

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from archive_govt_nz.domains.health_appropriations.biff8_records import BiffSheet

VALUE_BASIS = "biff8_stored_integer/v1"
NUMERIC_SCHEMA = pa.schema(
    [
        ("schema_version", pa.string()),
        ("value_basis", pa.string()),
        ("decoder_version", pa.string()),
        ("numeric_evidence_id", pa.string()),
        ("source_sha256", pa.string()),
        ("stream_sha256", pa.string()),
        ("sheet", pa.string()),
        ("sheet_bof_offset", pa.int64()),
        ("source_row", pa.int64()),
        ("source_column", pa.int64()),
        ("record_offset", pa.int64()),
        ("record_type", pa.int64()),
        ("member_index", pa.int64()),
        ("record_payload_sha256", pa.string()),
        ("encoded_value_hex", pa.string()),
        ("canonical_stored_integer", pa.string()),
    ]
)
_ERROR = "invalid_biff8_numeric_projection"


@dataclass(frozen=True, slots=True)
class ProjectedStoredValue:
    """Carry interpretation and original evidence into downstream numeric lineage."""

    field: str
    canonical_stored_integer: int
    value_basis: str
    numeric_evidence_id: str
    source_sha256: str
    source_coordinate: str


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _typed_equal(actual: object, expected: object) -> bool:
    return type(actual) is type(expected) and actual == expected


def _replay(
    sheet: BiffSheet,
    fact: Mapping[str, Any],
    witnesses: Sequence[Mapping[str, Any]],
    lineage: Sequence[Mapping[str, Any]],
    columns: Mapping[str, int],
) -> tuple[ProjectedStoredValue, ...]:
    _require(
        fact["value_basis"] == VALUE_BASIS
        and "source_number_token" not in fact
        and fact["source_object_sha256"] == sheet.source_sha256
        and type(fact["source_row"]) is int
        and type(fact["record_id"]) is str
        and type(fact["lineage_id"]) is str
        and bool(fact["record_id"])
        and bool(fact["lineage_id"])
    )
    _require(
        "amount" in columns
        and len(witnesses) == len(lineage) == len(columns)
        and all(type(c) is int and c > 0 for c in columns.values())
        and len(set(columns.values())) == len(columns)
    )
    by_id = {w["numeric_evidence_id"]: NumericWitness(**w) for w in witnesses}
    by_field = {link["field"]: link for link in lineage}
    _require(len(by_id) == len(witnesses) and set(by_field) == set(columns))
    _require({link["numeric_evidence_id"] for link in lineage} == set(by_id))
    result = []
    for field, column in columns.items():
        link = by_field[field]
        expected = {
            "record_id": fact["record_id"],
            "lineage_id": fact["lineage_id"],
            "source_object_sha256": sheet.source_sha256,
            "source_row": fact["source_row"],
            "source_column": column,
            "value_basis": VALUE_BASIS,
            "raw_value": None,
            "normalized_value": str(fact[field]),
        }
        _require(all(_typed_equal(link[k], v) for k, v in expected.items()))
        witness = by_id[link["numeric_evidence_id"]]
        value = sheet.verify_integer(witness, row=fact["source_row"], column=column)
        if field == "amount":
            amount = exact_number(value)
            _require(type(fact[field]) is Decimal and amount is not None)
            _require(fact[field] == amount)
            _require(fact["canonical_stored_integer"] == str(value))
            _require(fact["numeric_evidence_id"] == witness.numeric_evidence_id)
        else:
            _require(_typed_equal(fact[field], value))
        title = sheet.binding.name.replace("'", "''")
        result.append(
            ProjectedStoredValue(
                field,
                value,
                VALUE_BASIS,
                witness.numeric_evidence_id,
                sheet.source_sha256,
                f"'{title}'!{get_column_letter(column)}{fact['source_row']}",
            )
        )
    return tuple(result)


def replay_projection(
    sheet: BiffSheet,
    fact: Mapping[str, Any],
    witnesses: Sequence[Mapping[str, Any]],
    lineage: Sequence[Mapping[str, Any]],
    *,
    columns: Mapping[str, int],
) -> tuple[ProjectedStoredValue, ...]:
    """Resolve all numeric fields from a caller-declared source-column contract.

    The caller supplies its trusted schema/profile column map. This is a numeric
    admission boundary, not approval of a canonical classification, currency,
    period alignment, aggregation, join or source rights. Whole-package readers
    must additionally verify complete fact/disposition/lineage closure.
    """
    try:
        return _replay(sheet, fact, witnesses, lineage, columns)
    except ValueError, TypeError, KeyError, OverflowError, ArithmeticError:
        raise ValueError(_ERROR) from None
