"""Fiscal shares keep source, period, reporting basis and lineage explicit."""

import hashlib
from copy import deepcopy
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

from archive_govt_nz.domains.health_appropriations import (
    fiscal_share_analysis as subject,
)
from archive_govt_nz.domains.health_appropriations.fiscal_crown_literals import (
    SOURCE_SHA256,
    VINTAGE,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
)


@pytest.fixture
def period_evidence(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "period-evidence.json"
    path.write_bytes(b"test period evidence")
    monkeypatch.setattr(
        subject, "PERIOD_EVIDENCE_SHA256", hashlib.sha256(path.read_bytes()).hexdigest()
    )
    return path


def rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    common = {
        "source_object_sha256": SOURCE_SHA256,
        "source_vintage": VINTAGE,
        "valid_time_end": date(2025, 6, 30),
        "valid_time_start": None,
        "valid_time_status": "end_known_start_unknown",
        "unit": "NZD_millions",
        "accounting_basis": "PBE Standards",
        "quality_flags": [],
    }
    health = {
        **common,
        "record_id": "health",
        "measure": "health_spending",
        "amount": Decimal(30311),
    }
    gdp = {
        **common,
        "record_id": "gdp",
        "measure": "nominal_gdp",
        "amount": Decimal(436103),
    }
    crowns = [
        {
            **common,
            "record_id": key,
            "measure": key + "_crown_expenses",
            "unit": "$ millions",
            "valid_time_status": "june_year_end_start_unqualified",
            "amount": Decimal(amount),
        }
        for key, amount in (("core", 141675), ("total", 183502))
    ]
    return [health], [gdp], crowns


def test_exact_shares_preserve_period_scope_and_input_ids(
    period_evidence: Path,
) -> None:
    inputs = rows()
    before = deepcopy(inputs)
    with localcontext() as context:
        context.prec = 2
        output = subject.derive_fiscal_health_shares(
            *inputs, period_evidence=period_evidence
        ).to_pylist()
    assert inputs == before
    results = {r["measure"]: r for r in output}
    assert results["health_share_gdp"]["percent"] == Decimal("6.950422262631")
    assert results["health_share_core_crown"]["percent"] == Decimal("21.394741485795")
    assert results["health_share_total_crown"]["percent"] == Decimal("16.518076097263")
    assert all(r["period_start"] == date(2024, 7, 1) for r in output)
    assert all(r["period_end"] == date(2025, 6, 30) for r in output)
    assert all(r["numerator_coverage"] == "core_crown_health_function" for r in output)
    assert results["health_share_total_crown"]["denominator_coverage"] == "total_crown"
    assert results["health_share_total_crown"]["numerator_id"] == "health"
    assert results["health_share_total_crown"]["denominator_id"] == "total"
    assert all(r["status"] == "calculated" for r in output)
    assert subject.derive_fiscal_health_shares(
        *inputs, period_evidence=period_evidence
    ).equals(
        subject.derive_fiscal_health_shares(*inputs, period_evidence=period_evidence)
    )


def test_share_ratios_are_period_specific_and_not_additive(
    period_evidence: Path,
) -> None:
    health, gdp, _ = rows()
    prior_health = deepcopy(health[0])
    prior_gdp = deepcopy(gdp[0])
    prior_health.update(
        record_id="health-prior", valid_time_end=date(2024, 6, 30), amount=Decimal(10)
    )
    prior_gdp.update(
        record_id="gdp-prior", valid_time_end=date(2024, 6, 30), amount=Decimal(10)
    )

    result = subject.derive_fiscal_health_shares(
        [prior_health, *health],
        [prior_gdp, *gdp],
        [],
        period_evidence=period_evidence,
    ).to_pylist()
    gdp_shares = {
        row["period_end"]: row for row in result if row["measure"] == "health_share_gdp"
    }

    assert set(gdp_shares) == {date(2024, 6, 30), date(2025, 6, 30)}
    assert gdp_shares[date(2024, 6, 30)]["percent"] == Decimal("100.000000000000")
    assert gdp_shares[date(2025, 6, 30)]["percent"] == Decimal("6.950422262631")
    assert gdp_shares[date(2024, 6, 30)]["numerator_id"] == "health-prior"
    assert gdp_shares[date(2025, 6, 30)]["numerator_id"] == "health"
    assert sum(row["percent"] for row in gdp_shares.values()) != Decimal(
        "100.000000000000"
    )


def test_cash_march_year_retains_missing_crown_denominators(
    period_evidence: Path,
) -> None:
    health, gdp, _ = rows()
    for r in [*health, *gdp]:
        r["valid_time_end"] = date(1989, 3, 31)
        r["accounting_basis"] = "Cash" if r["measure"] == "health_spending" else None
    output = subject.derive_fiscal_health_shares(
        health, gdp, [], period_evidence=period_evidence
    ).to_pylist()
    assert {r["period_start"] for r in output} == {date(1988, 4, 1)}
    assert {r["numerator_coverage"] for r in output} == {"cash_health_function"}
    assert [r["status"] for r in output].count("missing_denominator") == 2
    assert all(r["percent"] is None for r in output if r["status"] != "calculated")


@pytest.mark.parametrize(
    "change",
    ["source", "vintage", "unit", "period", "basis", "amount", "duplicate", "id"],
)
def test_incompatible_or_ambiguous_inputs_fail(
    change: str, period_evidence: Path
) -> None:
    health, gdp, crowns = rows()
    if change == "duplicate":
        crowns.append(deepcopy(crowns[0]))
    else:
        key, value = {
            "source": ("source_object_sha256", "a" * 64),
            "vintage": ("source_vintage", "other"),
            "unit": ("unit", "NZD_thousands"),
            "period": ("valid_time_end", date(2025, 3, 31)),
            "basis": ("accounting_basis", "Cash"),
            "amount": ("amount", Decimal("NaN")),
            "id": ("record_id", "health"),
        }[change]
        crowns[0][key] = value
    with pytest.raises(ValueError, match="fiscal_share_input_invalid"):
        subject.derive_fiscal_health_shares(
            health, gdp, crowns, period_evidence=period_evidence
        )


@pytest.mark.parametrize("amount", [Decimal(0), Decimal(-1)])
def test_nonpositive_denominator_is_reported(
    amount: Decimal, period_evidence: Path
) -> None:
    health, gdp, crowns = rows()
    gdp[0]["amount"] = amount
    result = subject.derive_fiscal_health_shares(
        health, gdp, crowns, period_evidence=period_evidence
    ).to_pylist()[0]
    assert result["status"] == "nonpositive_denominator"
    assert result["percent"] is None
    assert result["denominator_id"] == "gdp"


@pytest.mark.parametrize(
    ("year", "basis"), [(1990, "Cash"), (1994, "old-GAAP"), (1997, "IFRS")]
)
def test_reporting_transitions_remain_source_separated(
    year: int, basis: str, period_evidence: Path
) -> None:
    health, gdp, _ = rows()
    for row in [*health, *gdp]:
        row["valid_time_end"] = date(year, 6, 30)
        row["accounting_basis"] = basis if row["measure"] == "health_spending" else None
    health[0]["quality_flags"] = ["source_footnote_retained"]
    result = subject.derive_fiscal_health_shares(
        health, gdp, [], period_evidence=period_evidence
    ).to_pylist()[0]
    assert result["accounting_basis"] == basis
    assert result["period_start"] == date(year - 1, 7, 1)
    assert result["source_quality_flags"] == ["source_footnote_retained"]


def test_negative_numerator_and_unrepresentable_percent_are_not_published(
    period_evidence: Path,
) -> None:
    health, gdp, crowns = rows()
    health[0]["amount"] = Decimal(-1)
    result = subject.derive_fiscal_health_shares(
        health, gdp, crowns, period_evidence=period_evidence
    ).to_pylist()[0]
    assert result["status"] == "negative_numerator"
    assert result["percent"] is None
    health[0]["amount"] = Decimal("1e19")
    gdp[0]["amount"] = Decimal("1e-18")
    result = subject.derive_fiscal_health_shares(
        health, gdp, crowns, period_evidence=period_evidence
    ).to_pylist()[0]
    assert result["status"] == "unrepresentable_percentage"
    assert result["percent"] is None


def test_verified_query_keeps_receipt_and_uses_original_for_crown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, period_evidence: Path
) -> None:
    health, gdp, crowns = rows()
    package = CanonicalPackageInput(
        "historical",
        tmp_path / "canonical",
        "a" * 64,
        tmp_path / "original",
        tmp_path / "raw",
        "b" * 64,
    )
    seen = []
    monkeypatch.setattr(
        subject,
        "read_verified_canonical_tables",
        lambda value: (
            {
                "health_spending_fact": pa.Table.from_pylist(health),
                "fiscal_context_fact": pa.Table.from_pylist(gdp),
            },
            {"marker_sha256": value.marker_sha256},
        ),
    )

    def project(path: Path) -> tuple[pa.Table, pa.Table, dict[str, Any]]:
        seen.append(path)
        return (
            pa.Table.from_pylist(crowns),
            pa.table({}),
            {"status": "verified_source_faithful_projection"},
        )

    monkeypatch.setattr(
        subject.fiscal_crown_canonical_projection, "project_fiscal_crown", project
    )
    table, receipt = subject.query_fiscal_health_shares(
        package, period_evidence=period_evidence
    )
    assert seen == [package.original]
    assert table.num_rows == 3
    assert receipt["publication"] == "not_performed"
    assert receipt["canonical_input"]["marker_sha256"] == package.marker_sha256
    assert receipt["source_object_sha256"] == SOURCE_SHA256
    assert receipt["counts"] == {"calculated": 3}
    with pytest.raises(ValueError, match="fiscal_share_input_invalid"):
        subject.query_fiscal_health_shares(
            CanonicalPackageInput(
                "budget",
                package.root,
                package.marker_sha256,
                package.original,
                package.raw_root,
                package.raw_manifest_sha256,
            ),
            period_evidence=period_evidence,
        )


def test_period_evidence_must_match_pin(period_evidence: Path) -> None:
    period_evidence.write_bytes(b"changed observation")
    with pytest.raises(ValueError, match="fiscal_share_input_invalid"):
        subject.derive_fiscal_health_shares(*rows(), period_evidence=period_evidence)
    period_evidence.unlink()
    with pytest.raises(ValueError, match="fiscal_share_input_invalid"):
        subject.derive_fiscal_health_shares(*rows(), period_evidence=period_evidence)
