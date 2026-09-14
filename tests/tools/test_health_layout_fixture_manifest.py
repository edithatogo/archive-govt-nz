"""Contract for the versioned health layout fixture inventory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from archive_govt_nz.domains.health_appropriations.source_operations import PROFILES

ROOT = Path(__file__).parents[2]
MANIFEST = ROOT / "tests/fixtures/health-layout-fixtures-v1.json"
REQUIRED_FAMILIES = {
    "vote_health",
    "budget",
    "befu_hyefu",
    "treasury_fiscal",
    "ministry_vote_health",
    "pharmac_cpb",
    "cpi",
    "wage",
    "population",
}


def test_layout_fixture_manifest_is_versioned_and_complete() -> None:
    """Require all approved source families to have versioned layout IDs."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["schema_version"] == "archive-govt-nz.health-layout-fixtures/v1"
    rows = data["families"]
    assert {row["family"] for row in rows} == REQUIRED_FAMILIES
    assert (
        len(rows) == len(REQUIRED_FAMILIES) == len({row["layout_id"] for row in rows})
    )
    assert all(row["layout_id"].endswith("/v1") for row in rows)
    assert {row["status"] for row in rows} <= {"available", "required"}
    assert {row["family"] for row in rows if row["status"] == "required"} == {
        "budget",
        "population",
        "vote_health",
    }
    assert all(
        row["status"] == "available" or not row["operation_profiles"] for row in rows
    )
    assert {profile for row in rows for profile in row["operation_profiles"]} <= set(
        PROFILES
    )


@pytest.mark.parametrize(
    "field", ["family", "layout_id", "status", "operation_profiles"]
)
def test_layout_fixture_manifest_rejects_missing_contract_fields(field: str) -> None:
    """Ensure each manifest row exposes every structural contract field."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["families"][0].pop(field)
    with pytest.raises(KeyError):
        _ = data["families"][0][field]
