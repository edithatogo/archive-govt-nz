"""Declared interpreter bounds are enforced at both ends."""

from __future__ import annotations

import pytest

from archive_govt_nz.python_runtime import is_supported_python


@pytest.mark.parametrize(
    ("version", "expected_status"),
    [
        ((3, 15, 0), "unsupported"),
        ((3, 15, 1), "supported"),
        ((3, 15, 9), "supported"),
        ((3, 16, 0), "unsupported"),
        ((4, 0, 0), "unsupported"),
    ],
)
def test_supported_python_enforces_lower_and_upper_bounds(
    version: tuple[int, ...], expected_status: str
) -> None:
    """Accept only versions within the declared lower and upper bounds."""
    assert is_supported_python(version) is (expected_status == "supported")
