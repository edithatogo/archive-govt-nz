"""2020 binds its own definitions and observation; shared integrity stays intact."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_budget_2021 import (
    OBSERVED,
    fixture_source,
    normalize,
)

from archive_govt_nz.domains.health_appropriations import source_operations
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_registry import (
    AdapterContext,
    context_adapter_registrations,
)


@pytest.mark.parametrize("kind", ["expenditure", "revenue"])
def test_2020_period_definition_lineage_and_all_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    path, digest = fixture_source(tmp_path, monkeypatch, kind, edition=2020)
    args = {
        "expected_sha256": digest,
        "source_locator": f"https://www.treasury.govt.nz/sites/default/files/2020-05/b20-{kind}-data.xlsx",
        "source_vintage": "Budget-2020",
        "observed_at": OBSERVED,
    }
    output = tmp_path / "first"
    receipt = normalize(kind, path, output, args)
    assert receipt["counts"] == {
        "input": 3,
        "normalized": 3,
        "out_of_scope": 0,
        "blank": 0,
        "rejected": 0,
    }
    fact_file = (
        "budget_facts.parquet" if kind == "expenditure" else "revenue_facts.parquet"
    )
    facts = pq.read_table(output / fact_file).to_pylist()
    assert [f["valid_time_end"] for f in facts] == [
        date(y, 6, 30) for y in (2016, 2020, 2021)
    ]
    assert all(
        f["currency"] is None
        and f["valid_time_start"] is None
        and f["rights_state"] == "not_evaluated"
        and f["unit"] == "$000"
        for f in facts
    )
    lineage = pq.read_table(output / "field_lineage.parquet").to_pylist()
    unit_coordinate = "B38" if kind == "expenditure" else "B36"
    intro_coordinate = "B3" if kind == "expenditure" else "B4"
    assert any(
        f["field"] == "unit"
        and f["source_coordinate"] == f"'Explanation'!{unit_coordinate}"
        and f["raw_value"].startswith("Amount $000:")
        for f in lineage
    )
    assert any(
        f["field"] == "source_vintage"
        and f["source_coordinate"] == f"'Explanation'!{intro_coordinate}"
        and f["raw_value"].endswith("as published in Budget 2020.")
        for f in lineage
    )
    context = AdapterContext(args["source_locator"], args["source_vintage"], OBSERVED)
    registrations = context_adapter_registrations(
        cpi=context,
        population=context,
        qes=context,
        gdp=context,
        budget_expenditure=context if kind == "expenditure" else None,
        budget_revenue=context if kind == "revenue" else None,
    )
    common = dispatch_bronze(
        path.read_bytes(),
        source_sha256=digest,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        registrations=registrations,
    )
    assert list(common.output.records) == facts
    request = source_operations.SourceRequest(
        path,
        tmp_path / "operation",
        f"budget-{kind}-2020/v1",
        digest,
        args["source_vintage"],
        args["source_locator"],
        OBSERVED,
    )
    result = source_operations.operate_source(request, dry_run=False)
    assert result["status"] == "written_local"
    for name in (
        fact_file,
        "field_lineage.parquet",
        "row_dispositions.parquet",
        "MANIFEST.json",
    ):
        assert (output / name).read_bytes() == (request.output_dir / name).read_bytes()
    for key, value in {
        "expected_sha256": "0" * 64,
        "source_vintage": "Budget-2021",
        "source_locator": "https://www.treasury.govt.nz/unreviewed.xlsx",
    }.items():
        rejected = tmp_path / key
        with pytest.raises(ValueError, match="contract"):
            normalize(kind, path, rejected, args | {key: value})
        assert not rejected.exists()
