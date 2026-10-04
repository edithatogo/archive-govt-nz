"""Fiscal CPI benchmarks retain quarters, bases and source provenance."""

import hashlib
from datetime import date
from decimal import Decimal, localcontext
from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

from archive_govt_nz.domains.health_appropriations import (
    fiscal_cpi_benchmark as subject,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
)


def inputs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    health = {
        "source_object_sha256": subject.fiscal.SOURCE_SHA256,
        "source_vintage": subject.fiscal.VINTAGE,
        "measure": "health_share_gdp",
        "formula_policy": subject.fiscal.FORMULA_POLICY,
        "period_definition_evidence_sha256": subject.fiscal.PERIOD_EVIDENCE_SHA256,
        "period_start": date(2023, 7, 1),
        "period_end": date(2024, 6, 30),
        "numerator_id": "health",
        "numerator_amount": Decimal(50),
        "numerator_source_time_status": "end_known_start_unknown",
        "accounting_basis": "PBE Standards",
        "numerator_coverage": "core_crown_health_function",
        "source_quality_flags": ["source_footnote_retained"],
    }
    records = []
    for year in (2024, 2025):
        start = date(year - 1, 7, 1)
        for end in subject.quarter_ends(start):
            month = end.month - 2
            records.append(
                {
                    "record_id": f"cpi-{end}",
                    "valid_time_start": date(end.year, month, 1),
                    "valid_time_end": end,
                    "valid_time_status": "source_quarter_ended",
                    "source_object_sha256": subject.cpi.SOURCE_SHA256,
                    "source_vintage": subject.cpi.SOURCE_VINTAGE,
                    "measure": "consumer_price_index_all_groups",
                    "unit": "Index",
                    "amount": Decimal(100 if year == 2024 else 200),
                    "quality_flags": ["index_base_not_verified"],
                }
            )
    return [health], records


def test_exact_benchmark_is_independent_of_ambient_precision_and_uniform_rebase() -> (
    None
):
    health, indexes = inputs()
    with localcontext() as ambient:
        ambient.prec = 2
        result = subject.derive_fiscal_cpi_benchmark(health, indexes).to_pylist()[0]
    assert result["cpi_benchmark_millions"] == Decimal(100)
    assert result["period_cpi_mean"] == Decimal(100)
    assert result["benchmark_cpi_mean"] == Decimal(200)
    assert len(result["period_cpi_ids"]) == 4
    assert len(result["benchmark_cpi_ids"]) == 4
    assert result["numerator_source_time_status"] == "end_known_start_unknown"
    assert result["period_cpi_source_time_statuses"] == ["source_quarter_ended"] * 4
    assert result["cpi_source_quality_flags"] == ["index_base_not_verified"]
    assert result["numerator_gst_basis"] == "exclusive"
    for row in indexes:
        row["amount"] *= 3
    rebased = subject.derive_fiscal_cpi_benchmark(health, indexes).to_pylist()[0]
    assert rebased["cpi_benchmark_millions"] == result["cpi_benchmark_millions"]


@pytest.mark.parametrize(
    "case",
    [
        "missing_period",
        "missing_base",
        "zero_period",
        "zero_base",
        "negative",
        "overflow",
    ],
)
def test_exclusions_keep_input_lineage(case: str) -> None:
    health, indexes = inputs()
    expected = {
        "missing_period": "missing_period_cpi",
        "missing_base": "missing_benchmark_cpi",
        "zero_period": "nonpositive_period_cpi",
        "zero_base": "nonpositive_benchmark_cpi",
        "negative": "negative_numerator",
        "overflow": "unrepresentable_benchmark",
    }[case]
    if case == "missing_period":
        indexes.pop(0)
    elif case == "missing_base":
        indexes[-1]["amount"] = None
    elif case == "zero_period":
        indexes[0]["amount"] = Decimal(0)
    elif case == "zero_base":
        indexes[-1]["amount"] = Decimal(-1)
    elif case == "negative":
        health[0]["numerator_amount"] = Decimal(-1)
    else:
        health[0]["numerator_amount"] = Decimal("1e19")
        for row in indexes[:4]:
            row["amount"] = Decimal("1e-18")
    result = subject.derive_fiscal_cpi_benchmark(health, indexes).to_pylist()[0]
    assert result["status"] == expected
    assert result["cpi_benchmark_millions"] is None
    assert result["numerator_id"] == "health"
    assert len(result["period_cpi_ids"]) == 4


@pytest.mark.parametrize(
    "case", ["source", "vintage", "unit", "period", "nonfinite", "duplicate"]
)
def test_incompatible_index_inputs_fail(case: str) -> None:
    health, indexes = inputs()
    if case == "duplicate":
        indexes.append(dict(indexes[0]))
    else:
        key, value = {
            "source": ("source_object_sha256", "a" * 64),
            "vintage": ("source_vintage", "other"),
            "unit": ("unit", "percent_change"),
            "period": ("valid_time_end", date(2023, 9, 29)),
            "nonfinite": ("amount", Decimal("NaN")),
        }[case]
        indexes[0][key] = value
    with pytest.raises(ValueError, match="fiscal_cpi_benchmark_invalid"):
        subject.derive_fiscal_cpi_benchmark(health, indexes)


def test_march_year_keeps_gst_basis_and_quarter_ids() -> None:
    health, indexes = inputs()
    health[0].update(
        period_start=date(1988, 4, 1),
        period_end=date(1989, 3, 31),
        accounting_basis="Cash",
    )
    for row, end in zip(
        indexes[:4], subject.quarter_ends(date(1988, 4, 1)), strict=True
    ):
        row.update(
            record_id=f"cpi-{end}",
            valid_time_start=date(end.year, end.month - 2, 1),
            valid_time_end=end,
        )
    row = subject.derive_fiscal_cpi_benchmark(health, indexes).to_pylist()[0]
    assert row["status"] == "calculated"
    assert row["numerator_gst_basis"] == "inclusive"
    assert row["period_cpi_ids"][-1] == "cpi-1989-03-31"


@pytest.mark.parametrize("case", ["source", "duplicate"])
def test_unqualified_health_inputs_fail(case: str) -> None:
    health, indexes = inputs()
    if case == "source":
        health[0]["source_object_sha256"] = "a" * 64
    else:
        health.append(dict(health[0]))
    with pytest.raises(ValueError, match="fiscal_cpi_benchmark_invalid"):
        subject.derive_fiscal_cpi_benchmark(health, indexes)
    with pytest.raises(ValueError, match="fiscal_cpi_benchmark_invalid"):
        subject.quarter_ends(date(2024, 7, 2))


def test_verified_wrapper_binds_reference_point_and_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    definition = tmp_path / "definition.json"
    definition.write_bytes(b"synthetic definition observation")
    monkeypatch.setattr(
        subject,
        "CPI_DEFINITION_SHA256",
        hashlib.sha256(definition.read_bytes()).hexdigest(),
    )
    health, indexes = inputs()
    reference = {
        **indexes[0],
        "record_id": "reference",
        "valid_time_start": date(2017, 4, 1),
        "valid_time_end": date(2017, 6, 30),
        "amount": Decimal(1000),
    }
    indexes.append(reference)
    package = CanonicalPackageInput(
        "historical",
        tmp_path / "canonical",
        "a" * 64,
        tmp_path / "original",
        tmp_path / "raw",
        "b" * 64,
    )
    cpi_input = subject.CpiInput(tmp_path / "cpi", "c" * 64, tmp_path / "cas")
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
        return pa.Table.from_pylist(indexes), pa.table({}), {"source": "verified_cpi"}

    monkeypatch.setattr(subject.fiscal, "query_fiscal_health_shares", shares)
    monkeypatch.setattr(subject.cpi, "project_cpi", project)
    kwargs = {
        "fiscal_period_evidence": tmp_path / "fiscal",
        "cpi_definition_evidence": definition,
        "cpi_input": cpi_input,
    }
    table, receipt = subject.query_fiscal_cpi_benchmark(package, **kwargs)
    assert table.num_rows == 1
    assert receipt["fiscal_input"] == {"source": "verified_fiscal"}
    assert receipt["cpi_input"] == {"source": "verified_cpi"}
    assert receipt["counts"] == {"calculated": 1}
    assert receipt["publication"] == "not_performed"
    assert calls == [
        (package, kwargs["fiscal_period_evidence"]),
        (cpi_input.silver_root, cpi_input.manifest_sha256, cpi_input.cas_root),
    ]
    reference["amount"] = Decimal(999)
    with pytest.raises(ValueError, match="fiscal_cpi_benchmark_invalid"):
        subject.query_fiscal_cpi_benchmark(package, **kwargs)
    definition.write_bytes(b"changed")
    with pytest.raises(ValueError, match="fiscal_cpi_benchmark_invalid"):
        subject.query_fiscal_cpi_benchmark(package, **kwargs)
    definition.unlink()
    with pytest.raises(ValueError, match="fiscal_cpi_benchmark_invalid"):
        subject.query_fiscal_cpi_benchmark(package, **kwargs)
