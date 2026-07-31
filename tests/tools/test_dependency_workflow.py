"""Dependency lane safety contracts."""

from pathlib import Path


def test_dependency_lane_cannot_rewrite_production_lock() -> None:
    """The lane is read-only and explicitly observational."""
    text = (
        Path(__file__).parents[2] / ".github/workflows/dependency-lanes.yml"
    ).read_text()
    assert "uv lock --check" in text
    assert "uv lock --upgrade" not in text
    assert "contents: read" in text
    assert "pre-release lane is observational" in text
