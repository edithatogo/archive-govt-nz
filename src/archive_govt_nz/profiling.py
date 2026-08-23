"""Optional high-precision CPU/memory profiling via Scalene."""

from __future__ import annotations

import contextlib
import importlib.util
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path

SCALENE_AVAILABLE = importlib.util.find_spec("scalene") is not None


@dataclass(frozen=True, slots=True)
class ProfilingResult:
    """Outcome and metadata from a profiled execution block."""

    enabled: bool
    scalene_available: bool
    output_path: str | None = None
    metadata: dict[str, Any] | None = None


@contextlib.contextmanager
def profile_execution(
    output_path: Path | str | None = None,
    *,
    enabled: bool = True,
) -> Generator[ProfilingResult]:
    """Context manager to scope execution blocks for optional profiling."""
    target_path_str = str(output_path) if output_path else None
    yield ProfilingResult(
        enabled=enabled,
        scalene_available=SCALENE_AVAILABLE,
        output_path=target_path_str,
    )
