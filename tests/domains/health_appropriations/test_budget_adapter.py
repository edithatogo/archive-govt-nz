"""Budget workbook adapter wiring through the Bronze dispatch boundary."""

from __future__ import annotations

import hashlib
from io import BytesIO
from typing import TYPE_CHECKING, Any, Never

import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import budget_adapter
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    DispatchResult,
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.budget_adapter import (
    BudgetExpenditureAdapter,
    budget_expenditure_registration,
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
    assert payload == original


def test_unknown_workbook_layout_is_preserved_without_facts() -> None:
    digest, result = _dispatch(_workbook(sheet_name="Sheet1"))

    assert result.selection.status == "selected"
    assert result.selection.source_sha256 == digest
    assert result.output.layout == "unknown"
    assert result.output.records == ()
    assert result.output.lineage == ()
    assert len(result.output.losses) == 1
    assert result.output.losses[0].disposition == "preserved_only"
    assert result.output.losses[0].reason == "unsupported_budget_layout"


def test_unknown_budget_headers_are_preserved_without_facts() -> None:
    digest, result = _dispatch(
        _workbook(headers=["Vote", "Year", "Unrecognized layout"])
    )

    assert result.selection.source_sha256 == digest
    assert result.output.records == ()
    assert result.output.lineage == ()
    assert result.output.losses[0].disposition == "preserved_only"
    assert result.output.losses[0].reason == "unsupported_budget_headers"


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
