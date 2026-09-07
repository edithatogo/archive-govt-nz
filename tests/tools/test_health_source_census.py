"""Tests for the health appropriations source census validator."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))

from tools.validate_health_source_census import validate  # noqa: I001


ROOT = Path(__file__).parents[2]
CENSUS = (
    ROOT / "conductor/tracks/health_appropriations_medallion_assimilation_20260829/"
    "source-census.json"
)


def test_canonical_census_has_one_evidenced_disposition_per_source() -> None:
    """Accept the canonical census and preserve its declared record count."""
    result = validate(CENSUS)
    assert result["records"] == json.loads(CENSUS.read_text())["record_count"]


@pytest.mark.parametrize(
    ("field", "value"), [("disposition", "not-a-disposition"), ("reason", "")]
)
def test_census_rejects_unsupported_or_unevidenced_dispositions(
    tmp_path: Path, field: str, value: str
) -> None:
    """Reject unsupported dispositions and missing evidence."""
    data = json.loads(CENSUS.read_text())
    data["records"][0][field] = value
    path = tmp_path / "census.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="record"):
        validate(path)


"""Tests for the health appropriations source census validator."""
