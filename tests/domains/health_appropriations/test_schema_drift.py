"""Contracts for deterministic schema and source-layout drift reports."""

from __future__ import annotations

import pyarrow as pa
import pytest

from archive_govt_nz.domains.health_appropriations.schema_drift import (
    compare_fingerprints,
    layout_fingerprint,
    schema_fingerprint,
)


def test_arrow_schema_and_layout_fingerprints_are_stable_and_sensitive() -> None:
    first = pa.schema([("period", pa.string()), ("amount", pa.decimal128(20, 3))])
    same = pa.schema([("period", pa.string()), ("amount", pa.decimal128(20, 3))])
    changed = pa.schema([("period", pa.string()), ("amount", pa.decimal128(20, 2))])
    assert schema_fingerprint(first) == schema_fingerprint(same)
    assert schema_fingerprint(first) != schema_fingerprint(changed)
    assert layout_fingerprint(
        {"sheet": "Raw Data", "columns": [1, 2]}
    ) == layout_fingerprint({"columns": [1, 2], "sheet": "Raw Data"})


def test_fingerprint_comparison_is_deterministic_and_fail_closed() -> None:
    left = {"a": "a" * 64, "b": "b" * 64}
    right = {"a": "c" * 64, "c": "d" * 64}
    report = compare_fingerprints(left, right)
    assert report == compare_fingerprints(dict(reversed(tuple(left.items()))), right)
    assert report["status"] == "drift"
    assert report["changes"] == [
        {"key": "a", "change": "changed"},
        {"key": "b", "change": "removed"},
        {"key": "c", "change": "added"},
    ]
    assert compare_fingerprints(left, left)["status"] == "matching"
    with pytest.raises(ValueError, match="invalid_fingerprint_snapshot"):
        compare_fingerprints({"a": "bad"}, {})
