"""Stored encodings remain distinct from source text and formula caches."""

from __future__ import annotations

import struct
from typing import cast

import pytest

from archive_govt_nz.domains.health_appropriations import biff8_numeric


def _number(value: float) -> bytes:
    return struct.pack("<d", value)


def _rk_integer(value: int, *, scaled: bool = False) -> bytes:
    return struct.pack("<I", ((value << 2) & 0xFFFFFFFF) | 2 | int(scaled))


def _rk_float(value: float, *, scaled: bool = False) -> bytes:
    low, high = struct.unpack("<II", _number(value))
    assert low == 0, "fixture must fit the RK floating encoding"
    assert high & 3 == 0, "fixture must fit the RK floating encoding"
    return struct.pack("<I", high | int(scaled))


@pytest.mark.parametrize(
    ("record_type", "encoded", "expected"),
    [
        (0x0203, _number(42), 42),
        (0x0203, _number(-0.0), 0),
        (0x0203, _number(-(2**63)), -(2**63)),
        (0x027E, _rk_float(42), 42),
        (0x027E, _rk_integer(-7), -7),
        (0x027E, _rk_integer(4200, scaled=True), 42),
        (0x027E, _rk_float(4200, scaled=True), 42),
        (0x00BD, _rk_integer(9), 9),
    ],
)
def test_exact_integer_from_each_stored_encoding(
    record_type: int, encoded: bytes, expected: int
) -> None:
    original = bytes(encoded)
    assert biff8_numeric.stored_integer(record_type, encoded) == expected
    assert type(biff8_numeric.stored_integer(record_type, encoded)) is int
    assert encoded == original


@pytest.mark.parametrize(
    ("record_type", "encoded", "error"),
    [
        (0x0006, _number(42), "invalid_biff8_numeric_encoding"),
        (0x0203, _rk_integer(42), "invalid_biff8_numeric_encoding"),
        (0x027E, _number(42), "invalid_biff8_numeric_encoding"),
        (0x0203, _number(float("nan")), "nonfinite_biff8_stored_number"),
        (0x0203, _number(1.25), "nonintegral_biff8_stored_number"),
        (0x027E, _rk_integer(125, scaled=True), "nonintegral_biff8_stored_number"),
        (0x0203, _number(2**63), "biff8_stored_integer_out_of_range"),
        (0x0203, bytearray(_number(42)), "invalid_biff8_numeric_encoding"),
        (float(0x0203), _number(42), "invalid_biff8_numeric_encoding"),
    ],
)
def test_refuses_nonconstant_or_inexact_encodings(
    record_type: object, encoded: object, error: str
) -> None:
    # Casts deliberately preserve invalid runtime types for the boundary check.
    with pytest.raises(ValueError, match=f"^{error}$"):
        biff8_numeric.stored_integer(cast("int", record_type), cast("bytes", encoded))
