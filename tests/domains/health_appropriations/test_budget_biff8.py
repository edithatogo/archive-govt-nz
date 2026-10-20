"""Closed edition profiles retain numeric evidence and every source row."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from tests.domains.health_appropriations.biff8_fixture import grid_fixture

from archive_govt_nz.domains.health_appropriations import (
    budget_biff8,
    budget_biff8_adapter,
)


def _fixture(
    kind: str, *, amount: object = 123, edition: int = 2019
) -> tuple[bytes, budget_biff8.BiffBudgetProfile]:
    profile = getattr(
        budget_biff8, "PROFILES" if edition == 2019 else f"PROFILES_{edition}"
    )[kind]
    selected: dict[str, Any] = {
        "department": "Fictional ministry",
        "vote": "Health",
        "app_id": 387,
        "parent_id": 387,
        "appropriation_name": "Fictional care",
        "category_name": "Fictional care",
        "group_type": "MCOA" if edition < 2019 else "Single",
        "appropriation_or_category_type": "Non-Departmental Output Expenses",
        "restriction_type": None,
        "functional_classification": "Health",
        "amount": amount,
        "year": edition,
        "amount_type": "Estimated Actual",
        "periodicity": "A",
        "current_scope": None,
        "m_number": 36,
        "portfolio_name": "Health",
        "description": "Fictional receipt",
        "revenue_type": "Non-Tax Revenue",
    }
    row = tuple(selected[field] for _, field in profile.fields)
    other = tuple(
        "Other" if field == "vote" else value
        for (_, field), value in zip(profile.fields, row, strict=True)
    )
    explanation: list[tuple[object, ...]] = [(None, None)] * max(
        number for number, _ in profile.definitions
    )
    for number, value in profile.definitions:
        explanation[number - 1] = (None, value)
    payload = grid_fixture(
        (
            (
                "Raw Data",
                (
                    tuple(header for header, _ in profile.fields),
                    row,
                    (None,) * len(row),
                    other,
                ),
            ),
            ("Explanation", tuple(explanation)),
            ("Intro", (("Fictional preservation context",),)),
        )
    )
    return payload, replace(
        profile, source_sha256=hashlib.sha256(payload).hexdigest(), max_rows=3
    )


@pytest.mark.parametrize("edition", [2016, 2017, 2018, 2019])
@pytest.mark.parametrize("kind", ["expenditure", "revenue"])
def test_closed_biff_budget_profiles_have_complete_repeatable_typed_packages(
    kind: str,
    edition: int,
) -> None:
    payload, profile = _fixture(kind, edition=edition)
    parsed = budget_biff8.parse_snapshot(
        payload, profile=profile, observed_at="2026-10-20T00:00:00Z"
    )
    repeated = budget_biff8.parse_snapshot(
        payload, profile=profile, observed_at="2026-10-20T00:00:00Z"
    )
    assert parsed.metadata["source_vintage"] == f"Budget-{edition}"
    assert profile.profile_id == f"budget-{kind}-{edition}-biff8/v1"
    assert parsed.metadata == repeated.metadata
    assert all(
        table.equals(repeated.tables[name]) for name, table in parsed.tables.items()
    )
    assert parsed.metadata["counts"] == {
        "input": 3,
        "normalized": 1,
        "out_of_scope": 1,
        "blank": 1,
        "rejected": 0,
    }
    fact = parsed.tables["budget_facts.parquet"].to_pylist()[0]
    assert fact["amount"] == Decimal("123.000")
    assert fact["canonical_stored_integer"] == "123"
    assert fact["value_basis"] == "biff8_stored_integer/v1"
    assert fact["currency"] is None
    assert fact["valid_time_start"] is None
    assert "source_number_token" not in fact
    witnesses = parsed.tables["numeric_evidence.parquet"]
    assert witnesses.num_rows == len(profile.numeric_columns)
    assert set(witnesses["source_object_sha256"].to_pylist()) == {profile.source_sha256}
    numeric_links = [
        row
        for row in parsed.tables["field_lineage.parquet"].to_pylist()
        if row["numeric_evidence_id"] is not None
    ]
    assert len(numeric_links) == len(profile.numeric_columns)
    assert all(row["raw_value"] is None for row in numeric_links)
    if edition == 2016 and kind == "revenue":
        links = parsed.tables["field_lineage.parquet"].to_pylist()
        expected = {
            ("unit", "'Explanation'!B33"),
            ("valid_time_end", "'Explanation'!B34"),
            ("amount_type", "'Explanation'!B35"),
            ("app_id", "'Explanation'!B39"),
        }
        assert expected <= {(row["field"], row["source_coordinate"]) for row in links}
    assert parsed.metadata["rights_state"] == "not_evaluated"


@pytest.mark.parametrize("amount", [1.5, 1e17])
def test_bad_amounts_are_dispositioned_without_silent_rounding(amount: float) -> None:
    payload, profile = _fixture("revenue", amount=amount)
    parsed = budget_biff8.parse_snapshot(
        payload, profile=profile, observed_at="2026-10-20T00:00:00Z"
    )
    assert parsed.metadata["status"] == "partial"
    assert parsed.tables["budget_facts.parquet"].num_rows == 0
    assert parsed.tables["numeric_evidence.parquet"].num_rows == 0
    assert parsed.metadata["counts"]["rejected"] == 1
    reasons = parsed.tables["row_dispositions.parquet"]["reason"].to_pylist()
    assert reasons[0] in {"nonintegral_biff8_stored_number", "invalid_amount_range"}
    held = budget_biff8_adapter.BiffBudgetAdapter(
        profile, "2026-10-20T00:00:00Z"
    ).extract(payload, source_sha256=profile.source_sha256)
    assert held.status == "preserved_only"
    assert held.profiles == ()


def test_source_and_definition_changes_fail_before_admission() -> None:
    payload, profile = _fixture("revenue")
    with pytest.raises(ValueError, match="invalid_biff8_snapshot"):
        budget_biff8.parse_snapshot(
            payload,
            profile=replace(profile, source_sha256="0" * 64),
            observed_at="2026-10-20T00:00:00Z",
        )
    with pytest.raises(ValueError, match="budget_biff8_contract"):
        budget_biff8.parse_snapshot(
            payload,
            profile=replace(profile, definitions=((4, "Changed definition"),)),
            observed_at="2026-10-20T00:00:00Z",
        )


@pytest.mark.parametrize("edition", [2016, 2017, 2019])
@pytest.mark.parametrize("kind", ["expenditure", "revenue"])
def test_biff_budget_operations_and_native_dispatch_retain_all_four_tables(
    kind: str, edition: int, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from archive_govt_nz.domains.health_appropriations import (  # noqa: PLC0415 - Exercise the new integration boundary after core collection.
        source_operations,
    )
    from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (  # noqa: PLC0415 - Integration boundary.
        dispatch_bronze,
        dispatch_native_bronze,
    )
    from archive_govt_nz.domains.health_appropriations.adapter_registry import (  # noqa: PLC0415 - Integration boundary.
        AdapterContext,
        biff_budget_registrations,
    )

    payload, profile = _fixture(kind, edition=edition)
    profiles = getattr(
        budget_biff8, "PROFILES" if edition == 2019 else f"PROFILES_{edition}"
    )
    monkeypatch.setitem(profiles, kind, profile)
    source = tmp_path / "fictional.xls"
    source.write_bytes(payload)
    request = source_operations.SourceRequest(
        source,
        tmp_path / "dry-run",
        profile.profile_id,
        profile.source_sha256,
        f"Budget-{edition}",
        profile.source_locator,
        "2026-10-20T00:00:00Z",
    )
    preflight = source_operations.operate_source(request)
    assert preflight["status"] == "preflight_passed"
    assert not request.output_dir.exists()
    written = source_operations.operate_source(
        replace(request, output_dir=tmp_path / "first"), dry_run=False
    )
    repeat = source_operations.operate_source(
        replace(request, output_dir=tmp_path / "second"), dry_run=False
    )
    assert written["status"] == repeat["status"] == "written_local"
    assert written["output_sha256"] == repeat["output_sha256"]
    assert len(written["output_sha256"]) == 4
    assert (
        source_operations.operate_source(
            replace(request, source_locator="https://example.org/wrong")
        )["status"]
        == "failed"
    )
    registrations = biff_budget_registrations(
        (
            AdapterContext(
                profile.source_locator, f"Budget-{edition}", request.observed_at
            ),
        )
    )
    native = dispatch_native_bronze(
        payload,
        source_sha256=profile.source_sha256,
        media_type=budget_biff8_adapter.MEDIA_TYPE,
        registrations=registrations,
    )
    assert native.selection.status == "selected"
    from archive_govt_nz.domains.health_appropriations.adapter_protocol import (  # noqa: PLC0415 - Integration boundary.
        CompoundAdapterOutput,
    )

    assert isinstance(native.output, CompoundAdapterOutput)
    assert (
        native.output.profiles[0].metadata["output_sha256"] == written["output_sha256"]
    )
    assert len(native.output.profiles[0].recordsets) == 4
    classic_registrations: Any = registrations
    with pytest.raises(TypeError, match="invalid_adapter_registration"):
        dispatch_bronze(
            payload,
            source_sha256=profile.source_sha256,
            media_type=budget_biff8_adapter.MEDIA_TYPE,
            registrations=classic_registrations,
        )
