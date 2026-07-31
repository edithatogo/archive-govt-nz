"""Bootstrap contract tests for the installable package."""

from importlib.metadata import version
from pathlib import Path

import archive_govt_nz
from archive_govt_nz.config import Settings


def test_package_version_matches_distribution_metadata() -> None:
    """The public package version matches installed distribution metadata."""
    assert archive_govt_nz.__version__ == version("archive-govt-nz")


def test_settings_resolve_only_the_explicit_state_directory(
    tmp_path: Path,
) -> None:
    """Bootstrap configuration has a deterministic explicit input."""
    state_directory = tmp_path / "state"

    settings = Settings.from_state_directory(state_directory)

    assert settings.state_directory == state_directory.resolve()
