"""Semantic validation for source periods used by federation evidence."""

from __future__ import annotations

import re
from datetime import date

_PERIOD = re.compile(r"^(?P<year>\d{4})(?:-(?P<month>\d{2})(?:-(?P<day>\d{2}))?)?$")
_MONTHS_PER_YEAR = 12
_INVALID_PERIOD = "health_federation_period_invalid"
_INVALID_PERIOD_ORDER = "health_federation_period_order_invalid"


def _period_key(value: object) -> tuple[tuple[int, int, int], int]:
    if not isinstance(value, str):
        raise TypeError(_INVALID_PERIOD)
    match = _PERIOD.fullmatch(value)
    if match is None:
        raise ValueError(_INVALID_PERIOD)
    year = int(match.group("year"))
    month_token = match.group("month")
    day_token = match.group("day")
    if year < 1:
        raise ValueError(_INVALID_PERIOD)
    precision = 1
    month = 0
    day = 0
    if month_token is not None:
        month = int(month_token)
        precision = 2
        if not 1 <= month <= _MONTHS_PER_YEAR:
            raise ValueError(_INVALID_PERIOD)
    if day_token is not None:
        day = int(day_token)
        precision = 3
        try:
            date(year, month, day)
        except ValueError:
            raise ValueError(_INVALID_PERIOD) from None
    return (year, month, day), precision


def validate_health_federation_period(start: object, end: object) -> None:
    """Reject impossible, mixed-precision, and reversed inclusive periods."""
    start_key, start_precision = _period_key(start)
    end_key, end_precision = _period_key(end)
    if start_precision != end_precision or start_key > end_key:
        raise ValueError(_INVALID_PERIOD_ORDER)
