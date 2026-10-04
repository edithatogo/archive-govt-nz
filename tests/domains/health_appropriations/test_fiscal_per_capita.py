"""Mean resident denominators retain exact source identities and exclusions."""

import hashlib
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

from archive_govt_nz.domains.health_appropriations import fiscal_per_capita as subject
from archive_govt_nz.domains.health_appropriations import (
    population_annual_canonical_projection as population,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
)


def inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    health = {
        "period_start": date(2024, 7, 1),
        "period_end": date(2025, 6, 30),
        "source_object_sha256": subject.fiscal.SOURCE_SHA256,
        "source_vintage": subject.fiscal.VINTAGE,
        "measure": "health_share_gdp",
        "formula_policy": subject.fiscal.FORMULA_POLICY,
        "period_definition_evidence_sha256": subject.fiscal.PERIOD_EVIDENCE_SHA256,
        "numerator_id": "health",
        "numerator_amount": Decimal(30311),
        "accounting_basis": "PBE Standards",
        "numerator_coverage": "core_crown_health_function",
        "source_quality_flags": ["source_start_unqualified"],
    }
    resident = {
        "record_id": "population",
        "measure": "estimated_resident_population_mean_year_ended",
        "source_object_sha256": population.SOURCE_SHA256,
        "source_vintage": population.SOURCE_VINTAGE,
        "unit": "persons",
        "source_label": "Total All Ages",
        "period_token": "FY2025",
        "valid_time_start": date(2024, 7, 1),
        "valid_time_end": date(2025, 6, 30),
        "valid_time_status": "source_mean_year_ended",
        "amount": Decimal(5307900),
        "quality_flags": ["source_status_provisional"],
    }
    return [health], [resident]


def test_exact_rate_preserves_two_vintages_and_provisional_state() -> None:
    health, residents = inputs()
    with localcontext() as context:
        context.prec = 2
        result = subject.derive_fiscal_per_capita(health, residents).to_pylist()[0]
    assert result["source_dollars_per_mean_resident"] == Decimal("5710.544659846644")
    assert result["population_source_sha256"] == population.SOURCE_SHA256
    assert result["population_vintage"] == population.SOURCE_VINTAGE
    assert result["population_id"] == "population"
    assert result["numerator_id"] == "health"
    assert result["population_source_quality_flags"] == ["source_status_provisional"]
    assert result["fiscal_source_quality_flags"] == ["source_start_unqualified"]
    assert result["status"] == "calculated"
    assert result["unit"] == "source_dollars_per_mean_resident"


@pytest.mark.parametrize("case", ["march", "absent", "missing", "zero", "negative"])
def test_exclusions_keep_rows_and_lineage(case: str) -> None:
    health, residents = inputs()
    expected = "missing_population"
    if case == "march":
        health[0]["period_start"] = date(1988, 4, 1)
        health[0]["period_end"] = date(1989, 3, 31)
        expected = "unsupported_march_period"
    elif case == "absent":
        residents = []
    elif case == "missing":
        residents[0]["amount"] = None
    elif case == "zero":
        residents[0]["amount"] = Decimal(0)
        expected = "nonpositive_population"
    else:
        health[0]["numerator_amount"] = Decimal(-1)
        expected = "negative_numerator"
    row = subject.derive_fiscal_per_capita(health, residents).to_pylist()[0]
    assert row["status"] == expected
    assert row["source_dollars_per_mean_resident"] is None
    assert row["numerator_id"] == "health"


@pytest.mark.parametrize(
    "case",
    [
        "source",
        "vintage",
        "unit",
        "period",
        "measure",
        "nonfinite",
        "fraction",
        "duplicate",
    ],
)
def test_incompatible_population_fails_closed(case: str) -> None:
    health, residents = inputs()
    if case == "duplicate":
        residents.append(dict(residents[0]))
    else:
        key, value = {
            "source": ("source_object_sha256", "a" * 64),
            "vintage": ("source_vintage", "other"),
            "unit": ("unit", "thousands"),
            "period": ("valid_time_start", date(2024, 1, 1)),
            "measure": ("measure", "population_at_year_end"),
            "nonfinite": ("amount", Decimal("NaN")),
            "fraction": ("amount", Decimal("1.5")),
        }[case]
        residents[0][key] = value
    with pytest.raises(ValueError, match="fiscal_per_capita_invalid"):
        subject.derive_fiscal_per_capita(health, residents)


@pytest.mark.parametrize("case", ["source", "duplicate", "nonfinite"])
def test_unqualified_health_rows_are_rejected(case: str) -> None:
    health, residents = inputs()
    if case == "source":
        health[0]["source_object_sha256"] = "a" * 64
    elif case == "duplicate":
        health.append(dict(health[0]))
    else:
        health[0]["numerator_amount"] = Decimal("NaN")
    with pytest.raises(ValueError, match="fiscal_per_capita_invalid"):
        subject.derive_fiscal_per_capita(health, residents)


def test_verified_wrapper_binds_packages_and_rejects_period_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:

    evidence = tmp_path / "period-observation.json"
    evidence.write_bytes(b"synthetic period observation")
    monkeypatch.setattr(
        subject,
        "POPULATION_PERIOD_EVIDENCE_SHA256",
        hashlib.sha256(evidence.read_bytes()).hexdigest(),
    )
    health, residents = inputs()
    package = CanonicalPackageInput(
        "historical",
        tmp_path / "canonical",
        "a" * 64,
        tmp_path / "original",
        tmp_path / "raw",
        "b" * 64,
    )
    population_input = subject.PopulationInput(
        tmp_path / "population", "c" * 64, tmp_path / "cas"
    )
    calls = []

    def shares(
        value: CanonicalPackageInput, *, period_evidence: Path
    ) -> tuple[pa.Table, dict[str, Any]]:
        calls.append((value, period_evidence))
        return pa.Table.from_pylist(health), {"source": "verified_fiscal"}

    def project(
        root: Path, pin: str, cas: Path
    ) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
        calls.append((root, pin, cas))
        return (
            pa.Table.from_pylist(residents),
            pa.table({}),
            {"source": "verified_population"},
        )

    monkeypatch.setattr(subject.fiscal, "query_fiscal_health_shares", shares)
    monkeypatch.setattr(subject.population, "project_population_annual", project)
    kwargs = {
        "fiscal_period_evidence": tmp_path / "fiscal-observation",
        "population_period_evidence": evidence,
        "population_input": population_input,
    }
    table, receipt = subject.query_fiscal_per_capita(package, **kwargs)
    assert table.num_rows == 1
    assert receipt["fiscal_input"] == {"source": "verified_fiscal"}
    assert receipt["population_input"] == {"source": "verified_population"}
    assert receipt["counts"] == {"calculated": 1}
    assert calls == [
        (package, kwargs["fiscal_period_evidence"]),
        (
            population_input.silver_root,
            population_input.manifest_sha256,
            population_input.cas_root,
        ),
    ]
    assert receipt["publication"] == "not_performed"
    evidence.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="fiscal_per_capita_invalid"):
        subject.query_fiscal_per_capita(package, **kwargs)
    evidence.unlink()
    with pytest.raises(ValueError, match="fiscal_per_capita_invalid"):
        subject.query_fiscal_per_capita(package, **kwargs)
