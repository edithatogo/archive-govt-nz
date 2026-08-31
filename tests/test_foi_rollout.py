"""Country rollout plans retain unknown denominators and do not activate sources."""

from pathlib import Path

from archive_govt_nz.foi_discovery import build_reviewed_catalogue
from archive_govt_nz.foi_rollout import build_rollout


def test_every_entity_and_source_has_a_non_activating_next_action() -> None:
    """The plan covers the pinned universe without treating it as capture evidence."""
    catalogue = build_reviewed_catalogue(Path(__file__).parents[1] / "config/foi")
    plan = build_rollout(catalogue)
    assert len(plan["entities"]) == 251
    assert len(plan["sources"]) == 30
    assert {row["entity_id"] for row in plan["entities"]} == {
        row["id"] for row in catalogue["entities"]
    }
    assert all(row["country_complete"] is False for row in plan["entities"])
    assert all(row["country_denominator"] is None for row in plan["entities"])
    assert all(row["schedule_active"] is False for row in plan["sources"])
    assert plan["summary"]["entities_requiring_broader_discovery"] == 251
    assert plan["summary"]["entities_without_named_sources"] == 223
    assert plan["summary"]["public_raw_complete_countries_verified"] == 0


def test_restricted_sources_remain_blocked_and_omit_source_details() -> None:
    """Private source metadata cannot enter the generated rollout plan."""
    catalogue = {
        "sources": [{"id": "s", "entity_id": "NZ", "rights_status": "restricted"}],
        "entities": [{"id": "NZ", "source_ids": ["s"]}],
    }
    row = build_rollout(catalogue)["sources"][0]
    assert row["next_action"] == "retain_restriction_review"
    assert row["publication_group"] == "restricted_or_unclear"


def test_group_candidates_do_not_constitute_eligibility() -> None:
    """Open institutional candidates and mixed correspondence stay unapproved."""
    catalogue = build_reviewed_catalogue(Path(__file__).parents[1] / "config/foi")
    sources = {row["source_id"]: row for row in build_rollout(catalogue)["sources"]}
    assert sources["ca-federal-atip"]["publication_group"] == "institutional_open_data"
    assert sources["us-federal-foia"]["publication_group"] == "institutional_open_data"
    assert sources["nz-fyi"]["publication_group"] == "mixed_correspondence"
    assert sources["nz-fyi"]["publication_approved"] is False
    assert sources["ca-federal-atip"]["publication_approved"] is False
