"""Exact BIFF8 stored-number arithmetic; record origin needs separate proof."""

from __future__ import annotations

import math
import struct
from fractions import Fraction
from typing import cast

_NUMBER = 0x0203
_RK_TYPES = frozenset({0x027E, 0x00BD})
_NUMBER_WIDTH = struct.calcsize("<d")
_RK_WIDTH = struct.calcsize("<I")
_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1
_INVALID = "invalid_biff8_numeric_encoding"


def _ieee_value(encoded: bytes) -> Fraction:
    value = cast("float", struct.unpack("<d", encoded)[0])
    if not math.isfinite(value):
        message = "nonfinite_biff8_stored_number"
        raise ValueError(message)
    # The ratio is the exact stored IEEE value, not a decimal display string.
    return Fraction(*value.as_integer_ratio())


def _rk_value(encoded: bytes) -> Fraction:
    bits = int.from_bytes(encoded, "little")
    if bits & 2:
        value = Fraction(int.from_bytes(encoded, "little", signed=True) >> 2)
    else:
        high = (bits & ~3).to_bytes(_RK_WIDTH, "little")
        value = _ieee_value(bytes(_RK_WIDTH) + high)
    return value / 100 if bits & 1 else value


def stored_integer(record_type: int, encoded: bytes) -> int:
    """Decode a classified NUMBER/RK/MULRK value, refusing inexact integers.

    MULRK supplies one member's four numeric bytes. Callers must separately
    verify source/record/cell/member identity and reject formula origins; this
    arithmetic function is not a source witness or a lexical-token producer.
    """
    if type(record_type) is not int or type(encoded) is not bytes:
        raise ValueError(_INVALID)
    if record_type != _NUMBER and record_type not in _RK_TYPES:
        raise ValueError(_INVALID)
    width = _NUMBER_WIDTH if record_type == _NUMBER else _RK_WIDTH
    if len(encoded) != width:
        raise ValueError(_INVALID)
    value = _ieee_value(encoded) if record_type == _NUMBER else _rk_value(encoded)
    if value.denominator != 1:
        message = "nonintegral_biff8_stored_number"
        raise ValueError(message)
    integer = value.numerator
    if not _INT64_MIN <= integer <= _INT64_MAX:
        message = "biff8_stored_integer_out_of_range"
        raise ValueError(message)
    return integer
