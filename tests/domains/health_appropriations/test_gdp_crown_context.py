"""Synthetic source binding and wrong-profile admission regressions."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations import gdp_crown_context as subject

TRACK = (
    Path(__file__).resolve().parents[3]
    / "conductor/tracks/health_appropriations_medallion_assimilation_20260829"
)
PAYLOAD = b"synthetic source identity only; no workbook or official values"


@pytest.fixture
def _synthetic_pins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        subject,
        "SOURCE_PINS",
        dict.fromkeys(subject.SOURCE_PINS, hashlib.sha256(PAYLOAD).hexdigest()),
    )


def test_register_matches_reviewed_receipt() -> None:
    expected = json.loads((TRACK / "gdp-crown-context.json").read_text())
    assert subject.context_register() == expected


@pytest.mark.parametrize(
    "profile",
    [
        "stats-gdp-2026q1",
        "fiscal-gdp-2025",
        "fiscal-core-2025",
        "fiscal-total-2025",
        "befu-core-2026",
        "hyefu-core-2025",
    ],
)
@pytest.mark.usefixtures("_synthetic_pins")
def test_profile_metadata_does_not_admit_numbers(
    profile: str,
) -> None:
    result = subject.qualify_context(profile, PAYLOAD)
    assert result["context_qualification"] == "reviewed_metadata_hash_bound"
    assert result["numeric_admission"] == "not_admitted"
    assert result["rights"] == "not_evaluated"
    assert result["analytical_selection"] == "not_selected"
    assert result["currency"] is None
    assert result["gaps"]


@pytest.mark.usefixtures("_synthetic_pins")
def test_native_gdp_preflight_receipt_is_exact() -> None:
    receipt = subject.expected_gdp_receipt()
    result = subject.qualify_context(
        "stats-gdp-2026q1", PAYLOAD, native_receipt=receipt
    )
    assert result["numeric_admission"] == "native_receipt_matched"
    assert result["receipt_evidence"] == "caller_supplied_not_execution_attestation"
    assert result["native_receipt"] == receipt
    assert result["analytical_selection"] == "not_selected"
    assert result["promotion"] == "not_performed"


@pytest.mark.parametrize(
    "field",
    [
        "status",
        "source_vintage",
        "source_object_sha256",
        "source_locator",
        "transformation_id",
        "source_observation_id",
        "observed_at",
        "currency",
        "rights_state",
        "schema_version",
        "counts",
    ],
)
@pytest.mark.usefixtures("_synthetic_pins")
def test_wrong_gdp_receipt_rejected(field: str) -> None:
    receipt = subject.expected_gdp_receipt()
    receipt[field] = (
        {"facts": 60.0, "lineage": 900, "dispositions": 2287}
        if field == "counts"
        else "wrong"
    )
    with pytest.raises(ValueError, match="gdp_crown_contract"):
        subject.qualify_context("stats-gdp-2026q1", PAYLOAD, native_receipt=receipt)


@pytest.mark.parametrize(
    "profile",
    [
        "fiscal-gdp-2025",
        "fiscal-core-2025",
        "fiscal-total-2025",
        "befu-core-2026",
        "hyefu-core-2025",
    ],
)
@pytest.mark.usefixtures("_synthetic_pins")
def test_other_successful_receipt_cannot_admit_crown(
    profile: str,
) -> None:
    with pytest.raises(ValueError, match="gdp_crown_contract"):
        subject.qualify_context(
            profile, PAYLOAD, native_receipt=subject.expected_gdp_receipt()
        )


@pytest.mark.usefixtures("_synthetic_pins")
def test_wrong_original_unknown_profile_and_size_fail() -> None:
    for profile, payload in [
        ("stats-gdp-2026q1", PAYLOAD + b"altered"),
        ("unknown", PAYLOAD),
        ("stats-gdp-2026q1", b"x" * (subject.MAX_BYTES + 1)),
        ("stats-gdp-2026q1", bytearray(PAYLOAD)),
    ]:
        with pytest.raises(ValueError, match="gdp_crown_contract"):
            subject.qualify_context(profile, payload)  # type: ignore[arg-type]


@pytest.mark.usefixtures("_synthetic_pins")
def test_returned_register_and_receipt_are_isolated() -> None:
    first = subject.context_register()
    first["profiles"][0]["family"] = "total_crown"
    assert subject.context_register()["profiles"][0]["family"] == "gdp"
    receipt = subject.expected_gdp_receipt()
    result = subject.qualify_context(
        "stats-gdp-2026q1", PAYLOAD, native_receipt=receipt
    )
    receipt["status"] = "changed"
    assert result["native_receipt"]["status"] == "planned"


@pytest.mark.usefixtures("_synthetic_pins")
def test_reuses_gdp_public_reader_without_writes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source, probe = tmp_path / "source", tmp_path / "unused"
    source.write_bytes(PAYLOAD)
    calls: list[dict[str, Any]] = []

    def adapter(path: Path, output: Path, **kwargs: object) -> dict[str, Any]:
        assert path == source
        assert output == probe
        calls.append(kwargs)
        return subject.expected_gdp_receipt()

    monkeypatch.setattr(subject.gdp, "normalize_gdp", adapter)
    result = subject.preflight_stats_gdp(source, probe)
    assert len(calls) == 1
    assert calls[0]["dry_run"] is True
    assert calls[0]["expected_sha256"] == hashlib.sha256(PAYLOAD).hexdigest()
    assert result["numeric_admission"] == "native_source_preflight_passed"
    assert "native_preflight_required" not in result["gaps"]
    assert "ISO_currency_unqualified" in result["gaps"]
    assert "annual_join_unselected" in result["gaps"]
    assert not probe.exists()


def test_source_native_failure_propagates(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="gdp_source_contract"):
        subject.preflight_stats_gdp(tmp_path / "missing", tmp_path / "unused")
