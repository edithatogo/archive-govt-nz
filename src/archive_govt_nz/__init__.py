"""Evidence-first archival tooling for New Zealand government data."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("archive-govt-nz")
except PackageNotFoundError:
    __version__ = "0.1.0"

__all__ = ["__version__"]
