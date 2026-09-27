"""Canonical Gold plots remain bounded, categorical display products."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations import canonical_gold_plots


def _historical_row() -> dict[str, Any]:
    return {
        "source_vintage": "fixture-v1",
        "recordset": "health_spending_fact",
        "period_token": "2025*",
        "measure": "health_spending",
        "unit": "NZD millions",
        "currency": "NZD",
        "price_basis": None,
        "base_period": None,
        "denominator_definition": None,
        "institutional_coverage": "source-defined",
        "accounting_basis": "source-defined",
        "amount": Decimal("12.5"),
        "source_label": "Health",
        "source_locator": "fixture",
        "input_record_id": "record-1",
    }


def test_plot_groups_are_source_bounded_and_discrete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _historical_row()
    monkeypatch.setattr(canonical_gold_plots, "MAX_GROUPS", 0)
    _files, report = canonical_gold_plots.build_discrete_plots(
        {"historical_observations.parquet": [row]}
    )
    assert report["series"][0] == {
        "product": "historical",
        "status": "omitted_group_limit",
        "group_count": 1,
    }
    assert report["status"] == "complete_with_omissions"


def test_plot_point_limit_reports_omission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _historical_row()
    monkeypatch.setattr(canonical_gold_plots, "MAX_POINTS", 0)
    _files, report = canonical_gold_plots.build_discrete_plots(
        {"historical_observations.parquet": [row]}
    )
    historical = [item for item in report["series"] if item["product"] == "historical"]
    assert {item["status"] for item in historical} == {
        "omitted_point_limit",
        "no_eligible_groups",
    }
    omitted = next(
        item for item in historical if item["status"] == "omitted_point_limit"
    )
    assert omitted["point_count"] == 1
    assert report["status"] == "complete_with_omissions"


def test_invalid_value_is_redacted() -> None:
    row = _historical_row()
    row["amount"] = 12.5
    with pytest.raises(ValueError, match=r"^canonical_gold_plot_invalid$"):
        canonical_gold_plots.build_discrete_plots(
            {"historical_observations.parquet": [row]}
        )


def test_plot_size_limit_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(canonical_gold_plots, "MAX_OUTPUT_BYTES", 10_000)
    monkeypatch.setattr(
        canonical_gold_plots, "_render", lambda _context, _points: b"x" * 6_000
    )
    second = _historical_row()
    second["source_vintage"] = "fixture-v2"
    with pytest.raises(ValueError, match=r"^canonical_gold_plot_invalid$"):
        canonical_gold_plots.build_discrete_plots(
            {"historical_observations.parquet": [_historical_row(), second]}
        )
