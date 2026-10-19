"""Pinned 2024 expenditure preserves source qualifiers without assumed currency."""

from __future__ import annotations

import hashlib
import json
from datetime import date
from decimal import localcontext
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from openpyxl import Workbook

from archive_govt_nz.domains.health_appropriations import budget_expenditure_2024 as exp
from archive_govt_nz.domains.health_appropriations import (
    source_operations as operations,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    context_adapter_registrations,
)
from archive_govt_nz.domains.health_appropriations.budget import (
    normalize_budget_workbook,
)
from archive_govt_nz.domains.health_appropriations.budget_adapter import (
    budget_expenditure_registration,
)

ROW = [
    "Ministry of Health",
    "Health",
    101,
    100,
    "Health services",
    "Hospital care",
    "MCA",
    "Non-Departmental Output Expenses",
    None,
    "Health",
    1234.125,
    2025,
    "Main Estimates",
    "M",
    "Hospital services scope",
    36,
    "Health",
]
OBSERVED = "2026-10-18T03:01:13Z"


def fixture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    rows: list | None = None,
    *,
    changed_definition: bool = False,
) -> tuple[Path, str]:
    book = Workbook()
    raw = book.active
    assert raw is not None
    raw.title = "Raw Data"
    raw.append(list(exp.FIELDS))
    for row in [ROW] if rows is None else rows:
        raw.append(row)
    definitions = book.create_sheet("Explanation")
    for coordinate, value in exp.DEFINITIONS.items():
        definitions[coordinate] = value
    if changed_definition:
        definitions["B40"] = "Amounts in an unreviewed unit"
    intro = book.create_sheet("Intro")
    for coordinate in ("A10", "A13", "A14"):
        intro[coordinate] = "Synthetic notice, not rights approval."
    book.create_sheet("Pivot context")
    path = tmp_path / "source.xlsx"
    book.save(path)
    book.close()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(exp, "SOURCE_SHA256", digest)
    return path, digest


def context(digest: str) -> dict:
    return {
        "expected_sha256": digest,
        "source_locator": exp.SOURCE_LOCATOR,
        "source_vintage": exp.VINTAGE,
        "observed_at": OBSERVED,
    }


def test_qualifiers_tokens_lineage_and_repeat_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, digest = fixture(tmp_path, monkeypatch)
    first, second = tmp_path / "first", tmp_path / "second"
    with localcontext() as caller_context:
        caller_context.prec = 4
        result = exp.normalize(path, first, **context(digest))
    exp.normalize(path, second, **context(digest))
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }
    assert result["counts"] == {
        "input": 1,
        "normalized": 1,
        "out_of_scope": 0,
        "blank": 0,
        "rejected": 0,
    }
    fact = pq.read_table(first / "budget_facts.parquet").to_pylist()[0]
    assert fact["app_id"] == 101
    assert fact["parent_id"] == 100
    assert fact["category_name"] == "Hospital care"
    assert fact["group_type"] == "MCA"
    assert fact["periodicity"] == "M"
    assert fact["restriction_type"] is None
    assert fact["source_number_token"] == str(ROW[10])
    assert fact["currency"] is None
    assert fact["unit"] == "$000"
    assert fact["valid_time_start"] is None
    assert fact["valid_time_end"] == date(2025, 6, 30)
    assert fact["rights_state"] == "not_evaluated"
    assert len(json.loads(fact["raw_values_json"])) == 17
    links = pq.read_table(first / "field_lineage.parquet").to_pylist()
    assert any(r["field"] == "amount" and r["raw_value"] == "1234.125" for r in links)
    assert any(
        r["field"] == "periodicity" and r["source_coordinate"] == "'Explanation'!B39"
        for r in links
    )
    adapter_context = AdapterContext(
        source_locator=exp.SOURCE_LOCATOR,
        source_vintage=exp.VINTAGE,
        observed_at=OBSERVED,
    )
    routed = dispatch_bronze(
        path.read_bytes(),
        source_sha256=digest,
        media_type=exp.MEDIA_TYPE,
        registrations=context_adapter_registrations(
            cpi=adapter_context,
            population=adapter_context,
            qes=adapter_context,
            gdp=adapter_context,
            budget_expenditure=adapter_context,
        ),
    )
    assert list(routed.output.records) == [fact]
    legacy = tmp_path / "legacy"
    normalize_budget_workbook(path, legacy, **context(digest))
    assert {p.name: p.read_bytes() for p in legacy.iterdir()} == {
        p.name: p.read_bytes() for p in first.iterdir()
    }


def test_all_rows_accounted_and_unqualified_rows_not_changed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    other = list(ROW)
    other[1] = "Education"
    formula = list(ROW)
    formula[10] = "=1+1"
    invalid = list(ROW)
    invalid[13] = "annual"
    path, digest = fixture(
        tmp_path, monkeypatch, [ROW, other, [None] * 17, formula, invalid]
    )
    result = exp.normalize(path, tmp_path / "result", **context(digest))
    assert result["status"] == "partial"
    assert result["counts"] == {
        "input": 5,
        "normalized": 1,
        "out_of_scope": 1,
        "blank": 1,
        "rejected": 2,
    }
    dispositions = pq.read_table(
        tmp_path / "result/row_dispositions.parquet"
    ).to_pylist()
    assert [r["source_row"] for r in dispositions] == list(range(2, 7))
    assert [r["reason"] for r in dispositions][-2:] == [
        "formula_not_evaluated",
        "invalid_periodicity",
    ]


@pytest.mark.parametrize("change", ["digest", "locator", "vintage"])
def test_source_binding_refused_before_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    path, digest = fixture(tmp_path, monkeypatch)
    args = context(digest)
    args[
        {
            "digest": "expected_sha256",
            "locator": "source_locator",
            "vintage": "source_vintage",
        }[change]
    ] = {
        "digest": "0" * 64,
        "locator": "https://example.org/other.xlsx",
        "vintage": "Budget-2023",
    }[change]
    with pytest.raises(ValueError, match="budget_2024_expenditure_contract"):
        exp.normalize(path, tmp_path / "absent", **args)
    assert not (tmp_path / "absent").exists()


def test_dispatch_and_supported_source_operation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, digest = fixture(tmp_path, monkeypatch)
    args = {k: v for k, v in context(digest).items() if k != "expected_sha256"}
    dispatch = dispatch_bronze(
        path.read_bytes(),
        source_sha256=digest,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        registrations=(
            budget_expenditure_registration(**args),
            exp.registration(**args),
        ),
    )
    assert dispatch.selection.adapter_id == "nz-budget-2024-health-expenditure"
    assert dispatch.output.records[0]["currency"] is None
    request = operations.SourceRequest(
        path,
        tmp_path / "operation",
        exp.PROFILE,
        digest,
        exp.VINTAGE,
        exp.SOURCE_LOCATOR,
        OBSERVED,
    )
    result = operations.operate_source(request, dry_run=True)
    assert result["status"] == "preflight_passed"
    assert result["counts"]["normalized"] == 1
    assert not request.output_dir.exists()


@pytest.mark.parametrize("extra", [0, 1])
def test_complete_source_row_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, extra: int
) -> None:
    other = list(ROW)
    other[1] = "Education"
    path, digest = fixture(
        tmp_path, monkeypatch, [other] * (exp.MAX_ROWS - 1 + extra) + [ROW]
    )
    target = tmp_path / "bounded"
    if extra:
        with pytest.raises(ValueError, match="budget_2024_expenditure_contract"):
            exp.normalize(path, target, **context(digest))
        assert not target.exists()
    else:
        result = exp.normalize(path, target, **context(digest))
        assert result["counts"]["input"] == 6645
        fact = pq.read_table(target / "budget_facts.parquet").to_pylist()[0]
        assert fact["source_row"] == 6646


def test_unreviewed_metadata_or_bytes_never_emit_facts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path, digest = fixture(tmp_path, monkeypatch, changed_definition=True)
    with pytest.raises(ValueError, match="budget_revenue_contract"):
        exp.normalize(path, tmp_path / "absent", **context(digest))
    assert not (tmp_path / "absent").exists()
    adapter = exp.Budget2024ExpenditureAdapter(
        exp.SOURCE_LOCATOR, exp.VINTAGE, OBSERVED
    )
    changed = path.read_bytes() + b"changed"
    result = adapter.extract(changed, source_sha256=hashlib.sha256(changed).hexdigest())
    assert result.records == ()
    assert result.losses[0].disposition == "preserved_only"
