"""Runtime-version policy shared by CLI, MCP, and verification surfaces."""

from __future__ import annotations

REQUIRED_PYTHON = ">=3.15.1,<3.16"


def is_supported_python(version: tuple[int, ...]) -> bool:
    """Return whether a major/minor/micro tuple satisfies project policy."""
    return version[:3] >= (3, 15, 1) and version[:2] < (3, 16)
