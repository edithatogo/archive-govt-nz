"""Supplemental definitions must not replace source adapters or select deflators."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from archive_govt_nz.domains.health_appropriations import cpi, qes
from archive_govt_nz.domains.health_appropriations.price_wage_context import (
    PriceWageContext,
    admit_retained,
)

TRACK = (
    Path(__file__).resolve().parents[3]
    / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
)


def documents() -> list[dict[str, Any]]:
    return json.loads((TRACK / "price-wage-context.json").read_text())["definitions"]


@pytest.mark.parametrize("index", [0, 1])
def test_exact_definitions_keep_analysis_unselected(index: int) -> None:
    definition = PriceWageContext.model_validate(documents()[index])
    assert definition.analytical_selection == "not_selected"
    assert definition.annual_weighting == "not_selected"
    assert definition.currency_code is None
    assert definition == PriceWageContext.model_validate_json(
        definition.model_dump_json()
    )


@pytest.mark.parametrize(
    ("index", "field", "value"),
    [
        (0, "base_period", "2020Q1"),
        (0, "base_value", 100),
        (0, "series", "CPIQ.SE9"),
        (0, "adjustment", "seasonally_adjusted"),
        (1, "sex", "Male"),
        (1, "base_value", 1000),
        (1, "unit_label", "Index"),
        (1, "adjustment", "unadjusted"),
        (1, "currency_code", "NZD"),
        (0, "analytical_selection", "deflator"),
        (1, "annual_weighting", "simple_mean"),
        (0, "rights", "approved"),
        (0, "source_sha256", "0" * 64),
        (1, "source_vintage", "QES-2025-Q2"),
        (0, "metadata_response_sha256", "0" * 64),
    ],
)
def test_rejects_semantic_drift(index: int, field: str, value: object) -> None:
    data = documents()[index]
    data[field] = value
    with pytest.raises(ValidationError):
        PriceWageContext.model_validate(data)


@pytest.mark.parametrize("index", [0, 1])
def test_reuses_public_adapter_only_in_dry_run(
    index: int,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    definition = PriceWageContext.model_validate(documents()[index])
    original = {
        "counts": {"selected": 449} if index == 0 else {"normalized": 9},
        "rights_state": "not_evaluated",
        "index_base": None,
    }
    before = copy.deepcopy(original)
    calls = []

    def adapter(source: Path, output: Path, **kwargs: object) -> dict[str, Any]:
        calls.append((source, output, kwargs))
        return original

    module, name = (cpi, "normalize_cpi") if index == 0 else (qes, "normalize_qes")
    monkeypatch.setattr(module, name, adapter)
    source, output = tmp_path / "original", tmp_path / "unused"
    result = admit_retained(source, output, definition)
    assert len(calls) == 1
    assert calls[0][2]["dry_run"] is True
    assert calls[0][2]["expected_sha256"] == definition.source_sha256
    assert calls[0][2]["source_locator"] == definition.source_url
    assert calls[0][2]["source_vintage"] == definition.source_vintage
    assert calls[0][2]["observed_at"] == definition.source_observed_at
    assert original == before
    assert result["native_receipt"] == original
    assert result["supplemental_definition"] == definition.model_dump()
    assert result["numeric_admission"] == "preflight_passed"
    assert result["promotion"] == "not_performed"
    assert result["supplemental_qualification"] == "not_independently_replayable"
    assert calls[0][:2] == (source, output)
    assert not output.exists()


def test_registered_sources_match_existing_census() -> None:
    census = json.loads((TRACK / "context-census.json").read_text())
    for definition in documents():
        row = next(
            row for row in census["series"] if row["family"] == definition["family"]
        )
        assert row["series_id"] == definition["series"]
        assert row["vintage"] == definition["source_vintage"]
        assert row["sources"][0]["url"] == definition["source_url"]
        assert row["sources"][0]["object_sha256"] == definition["source_sha256"]
        assert row["sources"][0]["observed_at"] == definition["source_observed_at"]


def test_existing_probe_path_is_not_reused(tmp_path: Path) -> None:
    definition = PriceWageContext.model_validate(documents()[0])
    with pytest.raises(ValueError, match="probe"):
        admit_retained(tmp_path / "source", tmp_path, definition)


def test_native_failure_propagates(tmp_path: Path) -> None:
    definition = PriceWageContext.model_validate(documents()[0])
    with pytest.raises(ValueError, match="cpi_source_contract"):
        admit_retained(tmp_path / "absent", tmp_path / "unused", definition)


@pytest.mark.parametrize("index", [0, 1])
def test_every_snapshot_field_rejects_change(index: int) -> None:
    for field, value in documents()[index].items():
        data = documents()[index]
        data[field] = value + " altered" if isinstance(value, str) else 999
        with pytest.raises(ValidationError):
            PriceWageContext.model_validate(data)


def test_unreviewed_extra_field_is_rejected() -> None:
    data = documents()[0]
    data["annual_deflator"] = "June endpoint"
    with pytest.raises(ValidationError):
        PriceWageContext.model_validate(data)


def test_mutated_model_is_revalidated_before_adapter(tmp_path: Path) -> None:
    definition = PriceWageContext.model_validate(documents()[0])
    definition.base_value = 100
    with pytest.raises(ValidationError):
        admit_retained(tmp_path / "absent", tmp_path / "unused", definition)


def test_dangling_probe_symlink_is_rejected(tmp_path: Path) -> None:
    definition = PriceWageContext.model_validate(documents()[0])
    probe = tmp_path / "probe"
    try:
        probe.symlink_to(tmp_path / "absent", target_is_directory=True)
    except OSError:
        pytest.skip("symlink unavailable")
    with pytest.raises(ValueError, match="probe"):
        admit_retained(tmp_path / "source", probe, definition)


@pytest.mark.parametrize("index", [0, 1])
def test_wrong_retained_bytes_fail_without_outputs(
    index: int,
    tmp_path: Path,
) -> None:
    definition = PriceWageContext.model_validate(documents()[index])
    source, probe = tmp_path / "wrong", tmp_path / "unused"
    source.write_bytes(b"synthetic incorrect bytes")
    with pytest.raises(ValueError, match=r"hash|sha256|checksum"):
        admit_retained(source, probe, definition)
    assert not probe.exists()
