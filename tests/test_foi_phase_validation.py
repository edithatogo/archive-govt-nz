"""Phase acceptance checks for the global FOI source catalogue."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from archive_govt_nz.foi_discovery import build_reviewed_catalogue
from archive_govt_nz.foi_phase_validation import validate_catalogue_phase

SEEDS = Path(__file__).parents[1] / "config/foi"
SPEC = importlib.util.spec_from_file_location(
    "validate_foi_catalogue_phase_tool",
    Path(__file__).parents[1] / "tools/validate_foi_catalogue_phase.py",
)
assert SPEC is not None
assert SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


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
        ("unknown_jurisdiction_entity", "unknown_jurisdiction_entity"),
        ("missing_review_inventory", "directory_review_missing"),
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
    elif mutation == "unknown_jurisdiction_entity":
        catalogue["jurisdictions"][0]["entity_id"] = "missing-entity"
    elif mutation == "missing_review_inventory":
        del catalogue["provenance"]["directory_review"]["entities"]
    else:
        catalogue["coverage"]["verified_complete"] = 1

    with pytest.raises(ValueError, match=reason):
        validate_catalogue_phase(catalogue)


def test_fully_evidenced_catalogue_satisfies_phase_acceptance() -> None:
    """Acceptance is reachable only when every geographic entity is verified."""
    catalogue = copy.deepcopy(build_reviewed_catalogue(SEEDS))
    for row in catalogue["provenance"]["directory_review"]["entities"]:
        row["broader_discovery"] = "complete"
    geographic = 0
    for row in catalogue["entities"]:
        if row["kind"] != "supranational":
            row["complete_verified"] = True
            geographic += 1
    catalogue["coverage"]["verified_complete"] = geographic

    result = validate_catalogue_phase(catalogue)
    assert result["status"] == "passed"
    assert result["phase_acceptance"] == "satisfied"
    assert result["blockers"] == []


def test_cli_writes_blocked_receipt_and_returns_two(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The command preserves blocked acceptance in file, stdout, and exit code."""
    output = tmp_path / "nested" / "phase.json"
    monkeypatch.setattr(
        sys, "argv", ["validate-foi-catalogue-phase", "--output", str(output)]
    )

    assert TOOL.main() == 2
    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "blocked"
    assert json.loads(capsys.readouterr().out)["status"] == "blocked"
