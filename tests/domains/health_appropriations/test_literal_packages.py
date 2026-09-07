"""Persistence of admitted literals without reinterpreting source semantics."""

import hashlib
import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, cast

import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import literal_packages as packages


@pytest.mark.parametrize("profile", ["befu-detail", "hyefu-detail", "crown"])
@pytest.mark.parametrize("fault", ["none", "pin", "duplicate", "empty", "write"])
def test_admission_wrapper_and_failure_contracts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, profile: str, fault: str
) -> None:
    """Package the admission exactly; reject bad joins and retain failed writes."""
    digest = (
        packages.SOURCE_SHA256
        if profile == "crown"
        else packages.DETAIL_PROFILES[packages.PROFILES[profile]][0]
    )
    context = {
        "source_object_sha256": digest,
        "source_locator": "synthetic",
        "source_vintage": packages.PROFILES[profile],
        "observed_at": "2030-01-01T00:00:00Z",
    }
    record = {
        **context,
        "record_id": "retained-id",
        "source_observation_id": "retained-observation-id",
        "source_coordinate": "Sheet!A1",
        "sheet": "Sheet",
        "coordinate": "A1",
        "amount": Decimal("2.5"),
        "source_number_token": "2.5",
        "currency": None,
        "observed_at": datetime(2026, 1, 1, tzinfo=UTC),
        "raw_context": {"Sheet!A2" if profile == "crown" else "A2": "year"},
    }
    records = (
        []
        if fault == "empty"
        else [record, record]
        if fault == "duplicate"
        else [record]
    )
    admission = {
        "facts": records,
        "records": records,
        "workbook_inventory": {"sheets": [{"title": "Sheet"}]},
        "formula_totals": {
            "range": "A3:B3",
            "disposition": "excluded_formula_cache_not_admitted",
        },
    }
    calls = []

    def admit(*args: object) -> dict[str, Any]:
        calls.append(args)
        return admission

    monkeypatch.setattr(packages, "admit_fiscal_crown", admit)
    monkeypatch.setattr(packages, "admit_donor_health_detail", admit)
    if fault == "pin":
        context["source_object_sha256"] = "0" * 64
    if fault == "write":

        def fail(*_args: object, **_kwargs: object) -> None:
            message = "synthetic_io_failure"
            raise OSError(message)

        monkeypatch.setattr(pq, "write_table", fail)
    output = tmp_path / "package"
    if fault != "none":
        with pytest.raises((ValueError, IndexError, OSError)):
            packages.package_admitted_source(
                tmp_path / "source", output, profile=profile, context=context
            )
        assert not (output / "MANIFEST.json").exists()
        if fault == "pin":
            assert not calls
        if fault == "write":
            assert (output / "literal_facts.parquet").exists()
        return
    receipt = packages.package_admitted_source(
        tmp_path / "source", output, profile=profile, context=context
    )
    row = pq.read_table(output / "literal_facts.parquet").to_pylist()[0]
    expected_time = (
        record["observed_at"]
        if profile == "crown"
        else datetime(2030, 1, 1, tzinfo=UTC)
    )
    assert row["observed_at"] == expected_time
    if profile == "crown":
        assert row["source_observation_id"] == record["source_observation_id"]
    assert json.loads(row["source_record_json"])["source_number_token"] == str(
        Decimal("2.5")
    )
    assert row["amount"] == Decimal("2.5")
    assert receipt["promotion"] == "not_performed"
    links = pq.read_table(output / "field_lineage.parquet").to_pylist()
    assert {(r["source_coordinate"], r["field"]) for r in links} == {
        ("Sheet!A1", "amount"),
        ("Sheet!A2", "source_context"),
    }
    areas = pq.read_table(output / "area_dispositions.parquet").to_pylist()
    assert areas[-1]["except_selectors"] == (
        ["A1"] if profile == "crown" else ["A1", "A3:B3"]
    )


def test_package_round_trip_and_exclusive_output(tmp_path: Path) -> None:
    """Every nested admission field survives, with exact amount and stable links."""
    record = {
        "coordinate": "F102",
        "sheet": "Core Crown Expense Tables",
        "amount": Decimal("1.00000000000000001"),
        "source_number_token": "1.00000000000000001",
        "raw_context": {"F99": "=F5", "F5": "2020", "D102": "Synthetic"},
        "currency": None,
        "period_end": None,
    }
    context = {
        "source_object_sha256": "a" * 64,
        "source_locator": "data/raw/test.xlsx",
        "source_vintage": "BEFU-2025",
        "observed_at": "2026-08-30T08:58:00Z",
    }
    admission = {
        "records": [record],
        "workbook_inventory": {
            "sheets": [{"title": record["sheet"]}, {"title": "Other"}]
        },
        "formula_totals": {
            "range": "F111:O111",
            "disposition": "excluded_formula_cache_not_admitted",
        },
    }
    first = cast(
        "dict[str, Any]",
        packages.write_literal_package(
            tmp_path / "one", admission, profile="befu-detail", context=context
        ),
    )
    second = packages.write_literal_package(
        tmp_path / "two", admission, profile="befu-detail", context=context
    )
    assert first == second
    rows = pq.read_table(tmp_path / "one/literal_facts.parquet").to_pylist()
    assert rows[0]["amount"] == record["amount"]
    assert rows[0]["currency"] is None
    assert "=F5" in rows[0]["source_record_json"]
    assert first["counts"]["facts"] == 1
    assert first["rights_state"] == "not_evaluated"
    for name, digest in first["output_sha256"].items():
        assert (
            hashlib.sha256((tmp_path / "one" / name).read_bytes()).hexdigest() == digest
        )
    with pytest.raises(FileExistsError):
        packages.write_literal_package(
            tmp_path / "one", admission, profile="befu-detail", context=context
        )
