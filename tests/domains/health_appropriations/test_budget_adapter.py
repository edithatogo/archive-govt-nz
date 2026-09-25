"""Budget workbook adapter wiring through the Bronze dispatch boundary."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from io import BytesIO
from typing import TYPE_CHECKING, Any, Never

import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import (
    budget_adapter,
    source_dimensions,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    DispatchResult,
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.budget_adapter import (
    BudgetExpenditureAdapter,
    budget_expenditure_registration,
)
from archive_govt_nz.domains.health_appropriations.budget_revenue_adapter import (
    budget_revenue_registration,
)
from archive_govt_nz.domains.health_appropriations.dimension_mapping import (
    dimension_key,
)
from archive_govt_nz.domains.health_appropriations.source_dimensions import (
    budget_source_dimensions,
)

if TYPE_CHECKING:
    from openpyxl.worksheet.worksheet import Worksheet

_HEADERS = [
    "Vote",
    "Year",
    "Department",
    "Appropriation Name",
    "Functional Classification",
    "Amount $000",
    "Amount Type",
    "Portfolio Name",
    "Current Scope",
]
_ROW = [
    "Health",
    2025,
    "Health",
    "Care",
    "Health",
    123,
    "Main Estimates",
    "Health",
    "scope",
]
_EXTRACTOR_FAILURE = "extractor_failure"


def _workbook(
    *, sheet_name: str = "Raw Data", headers: list[str] | None = None
) -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    assert sheet is not None
    sheet.title = sheet_name
    sheet.append(_HEADERS if headers is None else headers)
    if sheet_name == "Raw Data":
        sheet.append(_ROW)
        sheet.append([None] * len(_HEADERS))
        sheet.append(["Education", *_ROW[1:]])
    workbook.create_sheet("Explanation")
    output = BytesIO()
    workbook.save(output)
    workbook.close()
    return output.getvalue()


def _dispatch(payload: bytes) -> tuple[str, DispatchResult]:
    digest = hashlib.sha256(payload).hexdigest()
    result = dispatch_bronze(
        payload,
        source_sha256=digest,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        registrations=(
            budget_expenditure_registration(
                source_locator="data/raw/b25-expenditure-data.xlsx",
                source_vintage="Budget-2025",
                observed_at="2026-08-30T00:00:00Z",
            ),
            budget_revenue_registration(
                source_locator="data/raw/b25-revenue-data.xlsx",
                source_vintage="Budget-2025",
                observed_at="2026-08-30T00:00:00Z",
            ),
        ),
    )
    return digest, result


def test_dispatch_emits_budget_facts_row_losses_and_cell_lineage() -> None:
    payload = _workbook()
    original = payload
    digest, result = _dispatch(payload)

    assert result.selection.status == "selected"
    assert result.selection.source_sha256 == digest
    assert result.selection.adapter_id == "nz-budget-health-expenditure"
    assert result.output.layout == "budget-expenditure/v1"
    assert len(result.output.records) == 1
    fact = result.output.records[0]
    assert fact["source_object_sha256"] == digest
    assert fact["source_vintage"] == "Budget-2025"
    assert fact["amount"] == 123
    assert fact["rights_state"] == "not_evaluated"
    assert {(row.disposition, row.reason) for row in result.output.losses} == {
        ("out_of_scope", "non_health_vote"),
        ("blank", "empty_row"),
        ("excluded", "not_budget_raw_data_inventoried_only"),
    }
    amount = next(row for row in result.output.lineage if row.field == "amount")
    assert amount.record_id == fact["record_id"]
    assert amount.source_coordinate == "'Raw Data'!F2"
    assert amount.raw_value == "123"
    assert amount.normalized_value == "123.000"
    assert amount.rule == "budget-expenditure/v1"
    assert {row.dimension.kind for row in result.output.dimensions} == {
        "vote",
        "appropriation",
        "department",
        "portfolio",
        "amount_type",
        "functional_classification",
        "measure",
        "unit",
        "period",
    }
    assert all(
        row.target is None
        and row.method is None
        and row.evidence == ()
        and row.vintage == "Budget-2025"
        for row in result.output.dimensions
    )
    period = next(
        row.dimension
        for row in result.output.dimensions
        if row.dimension.kind == "period"
    )
    assert period.label == str(2025)
    assert period.period_token == str(2025)
    unit_link = next(row for row in result.output.dimension_links if row.kind == "unit")
    assert unit_link.dimension_key == dimension_key(
        next(
            row.dimension
            for row in result.output.dimensions
            if row.dimension.kind == "unit"
        )
    )
    assert unit_link.source_coordinate == "'Raw Data'!F1"
    assert unit_link.raw_value == "Amount $000"
    measure_link = next(
        row for row in result.output.dimension_links if row.kind == "measure"
    )
    assert measure_link.normalized_value == "appropriation_amount"
    assert measure_link.rule == "budget-expenditure/measure-rule/v1"
    assert "economic_classification" not in {
        row.dimension.kind for row in result.output.dimensions
    }
    repeated_digest, repeated = _dispatch(payload)
    assert repeated_digest == digest
    assert repeated.output.dimensions == result.output.dimensions
    assert repeated.output.dimension_links == result.output.dimension_links
    assert payload == original


def test_unknown_workbook_layout_is_preserved_without_facts() -> None:
    digest, result = _dispatch(_workbook(sheet_name="Sheet1"))

    assert result.selection.status == "preserved_only"
    assert result.selection.source_sha256 == digest
    assert result.selection.reason == "no_matching_layout"
    assert result.output.layout == "unknown"
    assert result.output.records == ()
    assert result.output.lineage == ()
    assert result.output.dimensions == ()
    assert len(result.output.losses) == 1
    assert result.output.losses[0].disposition == "preserved_only"
    assert result.output.losses[0].reason == "no_matching_layout"


def test_unknown_budget_headers_are_preserved_without_facts() -> None:
    digest, result = _dispatch(
        _workbook(headers=["Vote", "Year", "Unrecognized layout"])
    )

    assert result.selection.source_sha256 == digest
    assert result.output.records == ()
    assert result.output.lineage == ()
    assert result.output.losses[0].disposition == "preserved_only"
    assert result.output.losses[0].reason == "no_matching_layout"


def test_adapter_enforces_byte_limit_and_hash_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = BudgetExpenditureAdapter("source", "vintage", "2026-08-30T00:00:00Z")
    monkeypatch.setattr(budget_adapter, "_MAX_SOURCE_BYTES", 1)
    with pytest.raises(ValueError, match="source_byte_limit"):
        adapter.extract(
            b"too long", source_sha256=hashlib.sha256(b"too long").hexdigest()
        )

    monkeypatch.setattr(budget_adapter, "_MAX_SOURCE_BYTES", 1024)
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        adapter.extract(b"different", source_sha256="0" * 64)


def test_invalid_xlsx_is_returned_as_preserved_only() -> None:
    payload = b"not an xlsx package"
    adapter = BudgetExpenditureAdapter("source", "vintage", "2026-08-30T00:00:00Z")
    output = adapter.extract(payload, source_sha256=hashlib.sha256(payload).hexdigest())

    assert output.layout == "unknown"
    assert output.records == ()
    assert output.lineage == ()
    assert output.losses[0].disposition == "preserved_only"
    assert output.losses[0].reason == "invalid_budget_workbook"


def test_expenditure_layout_probe_rejects_invalid_and_oversized_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = BudgetExpenditureAdapter("source", "vintage", "2026-08-30T00:00:00Z")
    monkeypatch.setattr(budget_adapter, "_MAX_SOURCE_BYTES", 0)
    assert not adapter.matches_layout(_workbook())
    monkeypatch.setattr(budget_adapter, "_MAX_SOURCE_BYTES", 1024 * 1024)
    assert not adapter.matches_layout(b"not an XLSX")


def test_unexpected_extractor_value_error_is_not_hidden(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = _workbook()

    def fail_extraction(_sheet: Worksheet, _context: dict[str, Any]) -> Never:
        raise ValueError(_EXTRACTOR_FAILURE)

    monkeypatch.setattr(budget_adapter, "_extract", fail_extraction)
    adapter = BudgetExpenditureAdapter("source", "vintage", "2026-08-30T00:00:00Z")
    with pytest.raises(ValueError, match=_EXTRACTOR_FAILURE):
        adapter.extract(payload, source_sha256=hashlib.sha256(payload).hexdigest())


def test_source_dimensions_reject_mixed_vintages_and_fact_lineage_drift() -> None:
    _, output = _dispatch(_workbook())
    fact = output.output.records[0]
    same_literals_other_vintage, _ = budget_source_dimensions(
        ({**fact, "source_vintage": "Budget-2026"},), output.output.lineage
    )
    assert {dimension_key(row.dimension) for row in same_literals_other_vintage} == {
        dimension_key(row.dimension) for row in output.output.dimensions
    }
    assert {row.vintage for row in same_literals_other_vintage} == {"Budget-2026"}

    with pytest.raises(ValueError, match="budget_dimension_single_vintage_required"):
        budget_source_dimensions(
            (fact, {**fact, "record_id": "another", "source_vintage": "Budget-2026"}),
            output.output.lineage,
        )

    changed_fact = {**fact, "department": "Different"}
    with pytest.raises(ValueError, match="budget_dimension_fact_lineage_mismatch"):
        budget_source_dimensions((changed_fact,), output.output.lineage)


def test_source_dimensions_reject_missing_fields_and_bad_coordinates() -> None:
    _, output = _dispatch(_workbook())
    fact = output.output.records[0]
    without_classification = tuple(
        row for row in output.output.lineage if row.field != "functional_classification"
    )
    with pytest.raises(ValueError, match="budget_dimension_source_field_missing"):
        budget_source_dimensions((fact,), without_classification)

    without_period = tuple(row for row in output.output.lineage if row.field != "year")
    with pytest.raises(ValueError, match="budget_period_source_field_missing"):
        budget_source_dimensions((fact,), without_period)

    without_amount = tuple(
        row for row in output.output.lineage if row.field != "amount"
    )
    with pytest.raises(ValueError, match="budget_amount_source_field_missing"):
        budget_source_dimensions((fact,), without_amount)

    amount = next(row for row in output.output.lineage if row.field == "amount")
    bad_amount = replace(amount, source_coordinate="'Raw Data'!$F$2")
    bad_lineage = tuple(
        bad_amount if row is amount else row for row in output.output.lineage
    )
    with pytest.raises(ValueError, match="budget_amount_coordinate_invalid"):
        budget_source_dimensions((fact,), bad_lineage)


def test_source_dimensions_enforce_bounded_fact_count(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _, output = _dispatch(_workbook())
    monkeypatch.setattr(source_dimensions, "_MAX_FACTS", 0)
    with pytest.raises(ValueError, match="budget_dimension_fact_limit"):
        budget_source_dimensions(output.output.records, output.output.lineage)
