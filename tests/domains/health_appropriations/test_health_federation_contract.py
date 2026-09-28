"""Fail-closed contracts for offline Health federation evidence fixtures."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from jsonschema import Draft202012Validator, ValidationError

from archive_govt_nz.domains.health_appropriations.health_federation_contract import (
    validate_health_federation_period,
)

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).parents[3]
SCHEMA = ROOT / "schemas/health-federation-record-v1.schema.json"
FIXTURE = ROOT / "tests/fixtures/health-federation-record-v1.json"
AMBIGUOUS_FIXTURE = ROOT / "tests/fixtures/health-federation-ambiguous-record-v1.json"


def test_federation_fixture_binds_versioned_keys_period_and_lineage() -> None:
    """The offline fixture preserves both namespaces and exact source context."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(fixture)
    assert fixture["observation_mode"] == "offline_fixture"
    assert fixture["source"]["scheme_version"] == "pharmac-cpb/v1"
    assert fixture["target"]["scheme_version"] == "gma-product/2026-01"
    assert fixture["mapping"] == {"method": "none", "confidence": None}
    assert fixture["period"]["basis"] == "july-june-financial-year"
    assert fixture["lineage"]["source_record_ids"] == ["fixture:source:cpb-item-001"]
    assert fixture["disposition"] == "unmatched"


def test_ambiguous_federation_fixture_keeps_all_candidate_lineage() -> None:
    """Ambiguous targets remain separate candidates without a chosen link."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    fixture = json.loads(AMBIGUOUS_FIXTURE.read_text(encoding="utf-8"))

    Draft202012Validator(schema).validate(fixture)
    assert fixture["disposition"] == "ambiguous"
    assert fixture["target"]["key"] is None
    assert len(fixture["lineage"]["target_record_ids"]) == 2


@pytest.mark.parametrize(
    "mutate",
    [
        pytest.param(
            lambda row: row.update(observation_mode="live_runtime"), id="live-runtime"
        ),
        pytest.param(
            lambda row: row.update(disposition="mapped"), id="unproven-mapping"
        ),
        pytest.param(
            lambda row: row["mapping"].update(method="exact_key", confidence=0.99),
            id="unsupported-confidence",
        ),
        pytest.param(
            lambda row: row["lineage"].update(source_manifest_sha256="missing"),
            id="missing-lineage-fixity",
        ),
        pytest.param(
            lambda row: row["source"].update(scheme_version=""), id="unversioned-key"
        ),
        pytest.param(
            lambda row: row["source"].update(key=None), id="missing-source-key"
        ),
        pytest.param(
            lambda row: row["source"].update(key="   "), id="blank-source-key"
        ),
        pytest.param(
            lambda row: row["period"].update(start="2026-99"), id="invalid-month-shape"
        ),
    ],
)
def test_federation_fixture_rejects_unproven_or_live_mapping(
    mutate: Callable[[dict[str, object]], None],
) -> None:
    """Only explicit offline unmatched evidence can pass before review exists."""
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    fixture = copy.deepcopy(json.loads(FIXTURE.read_text(encoding="utf-8")))
    mutate(fixture)

    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(fixture)


@pytest.mark.parametrize(
    ("start", "end"),
    [
        pytest.param("2026-99", "2026-99", id="invalid-month"),
        pytest.param("2025-02-29", "2025-02-29", id="invalid-day"),
        pytest.param("2026-01", "2025-12", id="reversed-months"),
        pytest.param("2025", "2025-12", id="mixed-precision"),
    ],
)
def test_federation_period_rejects_invalid_or_unordered_intervals(
    start: str, end: str
) -> None:
    """Period semantics reject impossible dates and ambiguous ordering."""
    with pytest.raises(
        ValueError, match=r"^health_federation_period_(?:invalid|order_invalid)$"
    ):
        validate_health_federation_period(start, end)


def test_federation_period_accepts_valid_inclusive_periods() -> None:
    """Date, month and year periods remain available at their own precision."""
    validate_health_federation_period("2024-02-29", "2024-02-29")
    validate_health_federation_period("2025-07", "2026-06")
    validate_health_federation_period("1991", "2026")


@pytest.mark.parametrize("value", [None, "2026-Q1", "0000"])
def test_federation_period_rejects_invalid_tokens(value: object) -> None:
    """Period parsing rejects non-text, wrong shapes, and year zero."""
    with pytest.raises(
        (TypeError, ValueError),
        match=r"^health_federation_period_invalid$",
    ):
        validate_health_federation_period(value, value)
