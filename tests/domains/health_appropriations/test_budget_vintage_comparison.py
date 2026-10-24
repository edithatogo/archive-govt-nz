"""Estimate transitions preserve literal identities and source caveats."""

from __future__ import annotations

import hashlib
from decimal import Decimal, localcontext
from pathlib import Path

import pytest
from tests.domains.health_appropriations.test_budget import ROW, _source

from archive_govt_nz.domains.health_appropriations import (
    budget_vintage_comparison as subject,
)
from archive_govt_nz.domains.health_appropriations.budget import (
    normalize_budget_workbook,
)


def inputs(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    left: list[list[object]],
    right: list[list[object]],
) -> list[subject.BudgetComparisonInput]:
    result = []
    profiles = dict(subject.SOURCE_PINS)
    for year, rows in [(2025, left), (2026, right)]:
        source = tmp_path / f"{year}.xlsx"
        sha = _source(source, rows)
        profiles[f"Budget-{year}"] = (
            sha  # Synthetic transport fixture, not source qualification.
        )
        root = tmp_path / str(year)
        normalize_budget_workbook(
            source,
            root,
            expected_sha256=sha,
            observed_at="2026-08-30T00:00:00Z",
            source_vintage=f"Budget-{year}",
            source_locator=f"data/raw/b{year % 100}-expenditure-data.xlsx",
        )
        result.append(
            subject.BudgetComparisonInput(
                source,
                root,
                hashlib.sha256((root / "MANIFEST.json").read_bytes()).hexdigest(),
            )
        )
    monkeypatch.setattr(subject, "SOURCE_PINS", profiles)
    return result


def row(year: int, kind: str, amount: object, name: str = "Care") -> list[object]:
    value = list(ROW)
    value[1], value[3], value[5], value[6] = year, name, amount, kind
    return value


def test_exact_unique_transitions_and_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = inputs(
        tmp_path,
        monkeypatch,
        [
            row(2025, "Estimated Actual", 0),
            row(2026, "Main Estimates", -10),
            row(2024, "Actuals", 40),
        ],
        [
            row(2025, "Actuals", 5),
            row(2026, "Estimated Actual", -7),
            row(2027, "Main Estimates", 90),
        ],
    )
    with localcontext() as context:
        context.prec = 2
        result = subject.compare_budget_vintages(*data)
    rows = result.table.to_pylist()
    assert [r["difference_later_minus_earlier"] for r in rows] == [
        Decimal("5.000"),
        Decimal("3.000"),
    ]
    assert all(r["state"] == "unique_literal_pair" for r in rows)
    assert all(r["semantic_comparability"] == "not_established" for r in rows)
    assert rows[0]["period_start"].isoformat() == "2024-07-01"
    assert rows[1]["period_end"].isoformat() == "2026-06-30"
    assert result.receipt["input_accounting"] == {
        "earlier": {"selected": 2, "outside_transitions": 1},
        "later": {"selected": 2, "outside_transitions": 1},
    }
    assert result.receipt["rights_state"] == "not_evaluated"
    assert "supplementary_estimates_excluded" in result.receipt["caveats"]
    assert result.table.equals(subject.compare_budget_vintages(*data).table)


def test_duplicates_and_missing_dimensions_are_not_pooled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = inputs(
        tmp_path,
        monkeypatch,
        [
            row(2025, "Estimated Actual", 1),
            row(2025, "Estimated Actual", 2),
            row(2026, "Main Estimates", 3, "Old"),
        ],
        [row(2025, "Actuals", 9), row(2026, "Estimated Actual", 4, "New")],
    )
    result = subject.compare_budget_vintages(*data)
    rows = result.table.to_pylist()
    assert {r["state"] for r in rows} == {
        "ambiguous_literal_group",
        "earlier_only",
        "later_only",
    }
    assert all(r["difference_later_minus_earlier"] is None for r in rows)
    ambiguous = next(r for r in rows if r["state"] == "ambiguous_literal_group")
    assert len(ambiguous["earlier_record_ids"]) == 2
    assert ambiguous["earlier_amounts"] == [Decimal("1.000"), Decimal("2.000")]


def test_source_and_period_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = inputs(
        tmp_path,
        monkeypatch,
        [row(2025, "Estimated Actual", 1)],
        [row(2025, "Actuals", 2)],
    )
    profiles = dict(subject.SOURCE_PINS)
    monkeypatch.setattr(subject, "SOURCE_PINS", {**profiles, "Budget-2025": "0" * 64})
    with pytest.raises(ValueError, match="source_profile_mismatch"):
        subject.compare_budget_vintages(*data)
    monkeypatch.setattr(subject, "SOURCE_PINS", profiles)
    data[0].original.write_bytes(b"changed")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        subject.compare_budget_vintages(*data)


def test_unexpected_amount_type_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    data = inputs(
        tmp_path,
        monkeypatch,
        [row(2025, "Main Estimates", 1)],
        [row(2025, "Actuals", 2)],
    )
    with pytest.raises(ValueError, match="amount_type_period_mismatch"):
        subject.compare_budget_vintages(*data)
