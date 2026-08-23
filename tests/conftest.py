"""Root pytest configuration and profiling fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.profiling import ProfilingResult, profile_execution

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture
def test_profiler(
    tmp_path: Path,
) -> Generator[ProfilingResult]:
    """Provide a profiling context manager for performance-sensitive tests."""
    profile_out = tmp_path / "test-scalene-profile.json"
    with profile_execution(output_path=profile_out, enabled=True) as res:
        yield res
