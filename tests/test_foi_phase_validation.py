"""Phase acceptance checks for the global FOI source catalogue."""

import copy
from pathlib import Path

import pytest

from archive_govt_nz.foi_discovery import build_reviewed_catalogue
from archive_govt_nz.foi_phase_validation import validate_catalogue_phase

SEEDS = Path(__file__).parents[1] / "config/foi"


def test_current_catalogue_is_structurally_valid_but_not_phase_complete() -> None:
    """Keep structural success distinct from incomplete discovery acceptance."""
    result = validate_catalogue_phase(build_reviewed_catalogue(SEEDS))

    assert result["status"] == "blocked"
    assert result["structural_validation"] == "passed"
    assert result["phase_acceptance"] == "not_satisfied"
    assert result["counts"] == {
        "entities": 251,
        "sources": 30,
        "jurisdictions": 42,
        "entities_without_named_sources": 223,
        "entities_requiring_broader_discovery": 251,
        "countries_verified_complete": 0,
    }
    assert result["blockers"] == [
        "broader_discovery_incomplete",
        "country_completion_unverified",
    ]


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("duplicate_entity", "duplicate_entity"),
        ("unknown_source", "entity_source_mismatch"),
        ("wrong_coverage", "coverage_count_mismatch"),
        ("missing_review", "directory_review_incomplete"),
        ("false_completion", "completion_evidence_mismatch"),
        ("unknown_source_entity", "unknown_source_entity"),
    ],
)
def test_inconsistent_catalogues_fail_closed(mutation: str, reason: str) -> None:
    """Reject contradictory counts, links, reviews, and completion claims."""
    catalogue = copy.deepcopy(build_reviewed_catalogue(SEEDS))
    if mutation == "duplicate_entity":
        catalogue["entities"].append(copy.deepcopy(catalogue["entities"][0]))
    elif mutation == "unknown_source":
        catalogue["entities"][0]["source_ids"] = ["missing-source"]
    elif mutation == "wrong_coverage":
        catalogue["coverage"]["known_sources"] += 1
    elif mutation == "missing_review":
        catalogue["provenance"]["directory_review"]["entities"].pop()
    elif mutation == "unknown_source_entity":
        catalogue["sources"][0]["entity_id"] = "missing-entity"
    else:
        catalogue["coverage"]["verified_complete"] = 1

    with pytest.raises(ValueError, match=reason):
        validate_catalogue_phase(catalogue)
