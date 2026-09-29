"""Historical Fiscal Crown canonical facts retain source and period boundaries."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest

from archive_govt_nz.domains.health_appropriations import (
    fiscal_crown_canonical_projection as subject,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_crown_literals,
)


def _literal(  # noqa: PLR0913 - mirrors the independent parsed source-fact contract.
    *,
    record_id: str,
    family: str,
    year: int,
    label: str,
    coordinate: str,
    token: str,
    year_label: str,
    basis: str,
    note: str | None = None,
) -> dict[str, Any]:
    period_end = date(year, 6, 30)
    unit = "$ millions"
    raw = {
        "Spending!A23": "Cash, June Years",
        "Spending!A27": "old-GAAP",
        "Spending!A30": "IFRS, June Years",
        "Spending!A38": "PBE Standards, June Years",
        "Spending!A3": unit,
        f"Spending!B{year - 1967}": year_label,
        f"Spending!{coordinate}": token,
        f"Spending!{coordinate}@number_format": "test-format",
        f"Spending!{coordinate[0]}4": label,
    }
    lineage = {
        "label": f"Spending!{coordinate[0]}4",
        "amount": f"Spending!{coordinate}",
        "source_number_token": f"Spending!{coordinate}",
        "year_label": f"Spending!B{year - 1967}",
        "period_end": "Spending!A23",
        "unit": "Spending!A3",
        "accounting_basis": "Spending!A27",
    }
    return {
        "record_id": record_id,
        "family": family,
        "source_object_sha256": fiscal_crown_literals.SOURCE_SHA256,
        "source_locator": fiscal_crown_literals.SOURCE_URL,
        "source_vintage": fiscal_crown_literals.VINTAGE,
        "observed_at": datetime.fromisoformat("2026-08-29T09:00:17+00:00"),
        "year": year,
        "year_label": year_label,
        "label": label,
        "period_end": period_end,
        "accounting_basis": basis,
        "amount": Decimal(token),
        "source_number_token": token,
        "unit": unit,
        "currency": None,
        "price_basis": None,
        "amount_type": "historical_as_published",
        "source_year_notes": [] if note is None else [{"marker": note}],
        "lineage": lineage,
        "raw_context": raw,
    }


def test_canonicalization_preserves_core_total_and_historical_uncertainty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = [
        _literal(
            record_id=f"source-{index}",
            family="core_crown" if index < 32 else "total_crown",
            year=1994 + index,
            label="Core Crown Expenses" if index < 32 else "Total Crown Expenses",
            coordinate="D27" if index < 32 else "E30",
            token=(
                "28476" if index == 0 else "36632.50" if index == 32 else str(index + 1)
            ),
            year_label="1994*" if index == 0 else str(1994 + index),
            basis="old-GAAP"
            if index == 0
            else "IFRS"
            if index < 4
            else "PBE Standards",
            note="*" if index == 0 else None,
        )
        for index in range(61)
    ]

    def admit(_path: Path) -> dict[str, Any]:
        return {"facts": source, "counts": {"core_crown": 32, "total_crown": 29}}

    monkeypatch.setattr(fiscal_crown_literals, "admit_fiscal_crown", admit)
    facts, lineage, _ = subject.project_fiscal_crown(tmp_path / "pinned-source")
    rows = facts.to_pylist()
    assert [rows[index]["measure"] for index in (0, 32)] == [
        "core_crown_expenses",
        "total_crown_expenses",
    ]
    assert [rows[index]["institutional_coverage"] for index in (0, 32)] == [
        "core_crown",
        "total_crown",
    ]
    assert [rows[index]["amount"] for index in (0, 32)] == [
        Decimal(28476),
        Decimal("36632.50"),
    ]
    assert [rows[index]["period_token"] for index in (0, 32)] == [
        "year_label:1994*",
        "year_label:2026",
    ]
    assert [rows[index]["valid_time_end"] for index in (0, 32)] == [
        date(1994, 6, 30),
        date(2026, 6, 30),
    ]
    assert all(row["valid_time_start"] is None for row in rows)
    assert all(row["currency"] is None and row["price_basis"] is None for row in rows)
    assert all(row["rights_state"] == "not_evaluated" for row in rows)
    assert "source_year_note:*" in rows[0]["quality_flags"]
    assert len(lineage) == 671
    links = lineage.to_pylist()
    amount_link = next(
        item
        for item in links
        if item["target_record_id"] == rows[0]["record_id"]
        and item["field"] == "amount"
    )
    assert amount_link["source_coordinate"] == "Spending!D27"
    assert amount_link["raw_value"] == "28476"
    assert amount_link["normalized_value"] == "28476"
    assert any(item["field"] == "valid_time_status" for item in links)


def test_projection_uses_exact_retained_literal_parser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = [
        _literal(
            record_id=f"source-{index}",
            family="core_crown" if index < 32 else "total_crown",
            year=1994 + index,
            label="Core Crown Expenses" if index < 32 else "Total Crown Expenses",
            coordinate="D27" if index < 32 else "E30",
            token=str(index + 1),
            year_label=str(1994 + index),
            basis="PBE Standards",
        )
        for index in range(61)
    ]
    captured: list[Path] = []

    def admit(path: Path) -> dict[str, Any]:
        captured.append(path)
        return {
            "facts": source,
            "counts": {"core_crown": 32, "total_crown": 29},
        }

    monkeypatch.setattr(fiscal_crown_literals, "admit_fiscal_crown", admit)
    facts, lineage, receipt = subject.project_fiscal_crown(tmp_path / "pinned-source")
    assert captured == [tmp_path / "pinned-source"]
    assert facts.num_rows == 61
    assert lineage.num_rows == 671
    assert receipt["status"] == "verified_source_faithful_projection"
    assert receipt["denominator_selection"] == "not_performed"
    assert receipt["cross_measure_comparison"] == "not_performed"
    assert receipt["publication"] == "not_performed"
