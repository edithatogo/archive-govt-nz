"""Contract tests for the pytest-gremlins dependency and configuration."""

import tomllib
from pathlib import Path

from pytest_gremlins.config import load_config

ROOT = Path(__file__).resolve().parents[1]


def test_pytest_gremlins_is_bounded_and_configured() -> None:
    """Require a locked major series and deterministic mutation policy."""
    configuration = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert "pytest-gremlins>=1.9.0,<2" in configuration["dependency-groups"]["dev"]
    assert configuration["tool"]["pytest-gremlins"] == {
        "operators": ["comparison", "arithmetic", "boolean", "boundary", "return"],
        "paths": ["src/archive_govt_nz"],
        "exclude": ["**/__pycache__/**"],
        "report": ["console", "json"],
        "workers": "auto",
        "cache": True,
        "max-pardons-pct": 0.0,
    }

    loaded = load_config(ROOT)
    assert loaded.paths == ["src/archive_govt_nz"]
    assert loaded.report == ["console", "json"]
    assert loaded.workers == "auto"
    assert loaded.cache is True
    assert loaded.max_pardons_pct == 0.0
