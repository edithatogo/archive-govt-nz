"""Synthetic normalization contracts complement main's transport fixtures."""

from copy import deepcopy
from decimal import Decimal, localcontext
from io import BytesIO
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.schemas.health_recordset_normalization import normalize_rows
from archive_govt_nz.schemas.health_recordsets import RECORDSETS, recordset_schema


def row_for(name: str) -> dict[str, Any]:
    """Build explicitly synthetic context without rights or source claims."""
    row: dict[str, Any] = {
        field.name: None
        if field.nullable
        else []
        if pa.types.is_list(field.type)
        else "synthetic"
        for field in recordset_schema(name)
    }
    row.update(
        domain="health_appropriations",
        recordset=name,
        schema_version="archive-govt-nz.health-recordsets/v1",
        observed_at="2026-09-05T10:00:00.123456+10:00",
        rights_state="not_evaluated",
        valid_time_status="not_established",
    )
    if "amount" in row:
        row.update(amount="123.450", source_decimal_precision=6, source_decimal_scale=3)
    return row


@pytest.mark.parametrize("name", tuple(RECORDSETS))
def test_exact_roundtrip_and_input_preservation(name: str) -> None:
    """All eight sets retain values, schema, unknowns and deterministic order."""
    row = row_for(name)
    before = deepcopy(row)
    table = normalize_rows(name, [row])
    assert row == before
    assert table.schema.equals(recordset_schema(name), check_metadata=True)
    result = table.to_pylist()[0]
    assert result["rights_state"] == "not_evaluated"
    assert result["valid_time_start"] is None
    assert result["observed_at"].isoformat() == "2026-09-05T00:00:00.123456+00:00"
    if "amount" in row:
        assert result["amount"] == Decimal("123.450")
        assert result["unit"] is None
    streams = [BytesIO(), BytesIO()]
    for stream in streams:
        pq.write_table(normalize_rows(name, [row]), stream)
        stream.seek(0)
        assert pq.read_table(stream).equals(table, check_metadata=True)
    assert streams[0].getvalue() == streams[1].getvalue()
    assert normalize_rows(name, []).num_rows == 0


@pytest.mark.parametrize(
    "changes",
    [
        {"record_id": " "},
        {"amount": 1.5},
        {"amount": "1e3"},
        {"amount": None},
        {"null_reason": "blank"},
        {"source_decimal_precision": None},
        {"source_decimal_scale": None},
        {"source_decimal_precision": 0},
        {"source_decimal_scale": -1},
        {"source_decimal_precision": 2, "source_decimal_scale": 3},
        {"source_decimal_precision": 5},
        {"amount": "123.4501"},
        {"valid_time_start": "2026-01-02", "valid_time_end": "2026-01-01"},
        {"observed_at": "2026-09-05T00:00:00.1234567Z"},
        {"observed_at": "2026-09-05T00:00:00Zsecret"},
        {"schema_version": "unknown"},
    ],
)
def test_invalid_rows_fail_without_payload_disclosure(changes: dict[str, Any]) -> None:
    """Invalid transport and contradictory declarations fail closed."""
    row = row_for("appropriation_fact")
    row.update(changes)
    with pytest.raises(ValueError, match=r"^health_recordset_normalization$"):
        normalize_rows("appropriation_fact", [row])


def test_duplicates_and_unknown_contracts() -> None:
    """IDs must be unique within the requested record set."""
    row = row_for("source_inventory")
    with pytest.raises(ValueError, match="health_recordset_normalization"):
        normalize_rows("source_inventory", [row, row])
    with pytest.raises(KeyError):
        normalize_rows("unknown", [])
    with pytest.raises(KeyError):
        normalize_rows("source_inventory", [], version="unknown")


@pytest.mark.parametrize(
    ("amount", "reason", "precision", "scale"),
    [
        (None, "source_blank", None, None),
        (None, "suppressed", 6, 3),
        ("0", None, 1, 0),
        ("-0.000", None, 1, 0),
        ("-999.999", None, 6, 3),
        ("0.001", None, 3, 3),
    ],
)
def test_nullable_and_precision_boundaries(
    amount: str | None,
    reason: str | None,
    precision: int | None,
    scale: int | None,
) -> None:
    """Null reasons and exact trailing-zero rescaling never manufacture values."""
    row = row_for("fiscal_context_fact")
    row.update(
        amount=amount,
        null_reason=reason,
        source_decimal_precision=precision,
        source_decimal_scale=scale,
        valid_time_start="2026-01-01",
        valid_time_end="2026-01-01",
    )
    assert normalize_rows("fiscal_context_fact", [row]).num_rows == 1


@given(st.integers(min_value=-(10**18 - 1), max_value=10**18 - 1))
def test_decimal_context_cannot_round_values(coefficient: int) -> None:
    """Caller precision and traps do not affect exact conversion."""
    amount = Decimal(f"{coefficient}e-9")
    row = row_for("fiscal_context_fact")
    row.update(
        amount=format(amount, "f"), source_decimal_precision=18, source_decimal_scale=9
    )
    with localcontext() as context:
        context.prec = 2
        assert (
            normalize_rows("fiscal_context_fact", [row])["amount"][0].as_py() == amount
        )
