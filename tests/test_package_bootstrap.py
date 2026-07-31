"""Bootstrap contract tests for the installable package."""

from importlib.metadata import version

import archive_govt_nz


def test_package_version_matches_distribution_metadata() -> None:
    """The public package version matches installed distribution metadata."""
    assert archive_govt_nz.__version__ == version("archive-govt-nz")
