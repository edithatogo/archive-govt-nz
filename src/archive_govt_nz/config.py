"""Deterministic bootstrap configuration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    """Filesystem settings resolved from explicit caller input."""

    state_directory: Path

    @classmethod
    def from_state_directory(cls, state_directory: Path) -> Settings:
        """Normalize an explicit state directory without ambient discovery."""
        return cls(state_directory=state_directory.expanduser().resolve())
