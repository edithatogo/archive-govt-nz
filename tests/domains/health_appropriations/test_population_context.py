"""Population metadata qualification keeps enumeration and analysis separate."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from archive_govt_nz.domains.health_appropriations.population_context import (
    PopulationContext,
    qualification,
)

TRACK = Path(__file__).resolve().parents[3] / (
    "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
)


def document() -> dict:
    return json.loads((TRACK / "population-context.json").read_text())


def test_enumeration_does_not_require_analytical_admission() -> None:
    context = PopulationContext.model_validate(document())
    result = qualification(context)
    assert result == {
        "definition_enumeration": "complete",
        "query_metadata_export": "verified",
        "numeric_export_response": "not_verified",
        "analytical_selection": "not_selected",
        "rights": "not_evaluated",
    }
    assert result == qualification(
        PopulationContext.model_validate_json(context.model_dump_json())
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("table_id", "HLFS"),
        ("population_code", "M"),
        ("age_code", "15PLUS"),
        ("unit", "thousands"),
        ("reference_date", "2026-06-29"),
        ("reference_period", "2026Q3"),
        ("basis_date", "2018-06-30"),
        ("release_date", "2026-06-30"),
        ("numeric_export_response", "verified"),
        ("analytical_selection", "annual_mean"),
    ],
)
def test_rejects_definition_or_state_drift(field: str, value: str) -> None:
    data = document()
    data[field] = value
    with pytest.raises(ValidationError):
        PopulationContext.model_validate(data)


def test_rejects_estimate_code_label_swap() -> None:
    data = document()
    data["estimates"][0]["label"] = "Mean year ended"
    with pytest.raises(ValidationError, match="estimate"):
        PopulationContext.model_validate(data)


def test_rejects_duplicate_estimate_and_missing_mean() -> None:
    for choices in ([document()["estimates"][0]] * 2, [document()["estimates"][0]]):
        data = document()
        data["estimates"] = choices
        with pytest.raises(ValidationError, match="estimate"):
            PopulationContext.model_validate(data)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("http_status", 403),
        ("http_status", 200),
    ],
)
def test_http_status_alone_does_not_prove_query_export(field: str, value: int) -> None:
    data = document()
    data["query_export"][field] = value
    data["query_export"]["response_kind"] = "html_catalogue"
    with pytest.raises(ValidationError):
        PopulationContext.model_validate(data)


def test_missing_query_digest_is_rejected() -> None:
    data = document()
    data["query_export"]["sha256"] = ""
    with pytest.raises(ValidationError):
        PopulationContext.model_validate(data)


def test_session_url_cannot_be_a_stable_endpoint() -> None:
    data = document()
    data["export_entry_url"] += "?pxID=session"
    with pytest.raises(ValidationError):
        PopulationContext.model_validate(data)


def test_legacy_identifiers_are_enumerated_without_inferred_code_mapping() -> None:
    data = document()
    data["legacy_identifiers_found"] = ["DPEQ.SG1CTOT"]
    with pytest.raises(ValidationError, match="identifier"):
        PopulationContext.model_validate(data)
