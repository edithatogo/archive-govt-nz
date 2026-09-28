"""Canonical Gold plots remain bounded, categorical display products."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations import canonical_gold_plots


def _context_row(
    family: str, series_id: str, period: str, record_id: str, value: object
) -> dict[str, Any]:
    return {
        "family": family,
        "series_id": series_id,
        "source_vintage": "fixture-v1",
        "source_sha256": "a" * 64,
        "source_locator": f"fixture:{series_id}",
        "period_token": period,
        "value": value,
        "unit": "source-unit",
        "basis": None,
        "input_record_id": record_id,
        "admission": "eligible_context_only",
    }


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


def test_context_plots_keep_series_separate_and_exclusions_out() -> None:
    first = _context_row("cpi", "CPIQ.SE9A", "2025-Q1", "cpi-1", Decimal("1.2"))
    excluded = _context_row("cpi", "CPIQ.SE9A", "2025-Q2", "cpi-2", None)
    excluded["admission"] = "excluded_from_numeric_series"
    other_series = _context_row(
        "wage", "QEMQ.SASZ9A", "2025-Q1", "wage-1", Decimal("3.4")
    )
    first_files, first_report = canonical_gold_plots.build_context_plots(
        [first, excluded, other_series]
    )
    repeated_files, repeated_report = canonical_gold_plots.build_context_plots(
        [first, excluded, other_series]
    )
    assert first_files == repeated_files
    assert first_report == repeated_report
    assert len(first_files) == 2
    assert all(
        payload.startswith(b"\x89PNG\r\n\x1a\n") for payload in first_files.values()
    )
    assert first_report["period_axis"] == (
        "discrete_source_tokens_no_continuity_inference"
    )
    assert first_report["numeric_conversion"] == "float_for_display_only"
    assert first_report["excluded_observations_plotted"] is False
    by_family = {row["family"]: row for row in first_report["series"]}
    assert by_family["cpi"]["eligible_count"] == 1
    assert by_family["cpi"]["excluded_count"] == 1
    assert by_family["cpi"]["input_record_ids"] == ["cpi-1"]
    assert by_family["wage"]["input_record_ids"] == ["wage-1"]
    assert by_family["cpi"]["path"] != by_family["wage"]["path"]


def test_context_plots_keep_all_excluded_series_as_not_plotted() -> None:
    row = _context_row("population", "DPE056AA", "2025-Jun", "pop-1", None)
    row["admission"] = "excluded_from_numeric_series"
    files, report = canonical_gold_plots.build_context_plots([row])
    assert files == {}
    assert report["series"][0]["status"] == "no_eligible_observations"
    assert report["series"][0]["excluded_count"] == 1
