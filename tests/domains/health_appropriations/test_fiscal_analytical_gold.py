"""Analytical package writes are exclusive and readback is bounded and pinned."""

from pathlib import Path
from typing import Any

import pyarrow as pa
import pytest

from archive_govt_nz.domains.health_appropriations import fiscal_analytical_gold as gold


def fixture_inputs(root: Path) -> gold.FiscalAnalyticalInputs:
    return gold.FiscalAnalyticalInputs(
        gold.fiscal.CanonicalPackageInput(
            "historical",
            root / "canonical",
            "0" * 64,
            root / "original",
            root / "raw",
            "0" * 64,
        ),
        root / "fiscal-evidence",
        gold.population.PopulationInput(root / "population", "0" * 64, root / "cas"),
        root / "population-evidence",
        gold.cpi.CpiInput(root / "cpi", "0" * 64, root / "cas"),
        root / "cpi-evidence",
    )


def fixture_tables() -> dict[str, pa.Table]:
    tables = {}
    for name, schema in gold.TABLE_SCHEMAS.items():
        records: list[dict[str, Any]] = [
            {field.name: None for field in schema} for _ in range(2)
        ]
        if "status" in schema.names:
            for row, status in zip(
                records, ["calculated", "missing_denominator"], strict=True
            ):
                row["status"] = status
        tables[name] = pa.Table.from_pylist(records, schema=schema)
    return tables


def test_repeat_build_dry_run_and_bounded_readback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(gold, "build_tables", lambda _: (fixture_tables(), {}))
    inputs = fixture_inputs(tmp_path / "inputs")
    first, second = tmp_path / "first", tmp_path / "second"
    dry = gold.export_fiscal_analytical_gold(inputs, first)
    assert not first.exists()
    result = gold.export_fiscal_analytical_gold(inputs, first, write=True)
    repeated = gold.export_fiscal_analytical_gold(inputs, second, write=True)
    assert dry["manifest_sha256"] == result["manifest_sha256"]
    assert repeated == result
    for path in first.iterdir():
        assert path.read_bytes() == (second / path.name).read_bytes()
    table = gold.read_fiscal_analytical_gold(
        first, result["manifest_sha256"], table="shares", limit=1
    )
    assert table.num_rows == 1
    assert table["status"].to_pylist() == ["calculated"]
    with pytest.raises(FileExistsError):
        gold.export_fiscal_analytical_gold(inputs, first, write=True)


@pytest.mark.parametrize("case", ["pin", "payload", "extra", "symlink", "limit", "sql"])
def test_invalid_packages_and_queries_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    monkeypatch.setattr(gold, "build_tables", lambda _: (fixture_tables(), {}))
    root = tmp_path / "gold"
    result = gold.export_fiscal_analytical_gold(
        fixture_inputs(tmp_path / "inputs"), root, write=True
    )
    pin, table, limit = result["manifest_sha256"], "shares", 200
    if case == "pin":
        pin = "0" * 64
    elif case == "payload":
        (root / "shares.parquet").write_bytes(b"tampered")
    elif case == "extra":
        (root / "extra").write_bytes(b"untracked")
    elif case == "symlink":
        target = tmp_path / "target"
        (root / "shares.parquet").rename(target)
        (root / "shares.parquet").symlink_to(target)
    elif case == "limit":
        limit = 201
    else:
        table = "SELECT * FROM read_csv('/etc/passwd')"
    with pytest.raises(ValueError, match="fiscal_gold"):
        gold.read_fiscal_analytical_gold(root, pin, table=table, limit=limit)


def test_input_overlap_is_rejected_before_verification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = fixture_inputs(tmp_path / "inputs")

    def unexpected(_: object) -> object:
        pytest.fail("verification must not start for an unsafe output")

    monkeypatch.setattr(gold, "build_tables", unexpected)
    for target in (
        tmp_path,
        inputs.package.root / "gold",
        inputs.cpi_input.cas_root / "gold",
    ):
        with pytest.raises(ValueError, match="overlaps_input"):
            gold.export_fiscal_analytical_gold(inputs, target, write=True)
    assert not (tmp_path / "inputs").exists()


def test_build_verifies_each_source_and_keeps_nominal_lineage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    inputs = fixture_inputs(tmp_path / "inputs")
    tables = fixture_tables()
    records = tables["shares"].to_pylist()
    records[0]["measure"] = "health_share_gdp"
    records[0]["numerator_id"] = "source-cell-1"
    records[1]["measure"] = "health_share_core_crown"
    tables["shares"] = pa.Table.from_pylist(records, schema=gold.fiscal.SHARE_SCHEMA)
    calls = []

    def shares(package: object, **kwargs: object) -> tuple[pa.Table, dict[str, str]]:
        calls.append((package, kwargs))
        return tables["shares"], {"verified": "fiscal"}

    def rates(package: object, **kwargs: object) -> tuple[pa.Table, dict[str, str]]:
        calls.append((package, kwargs))
        return tables["per_capita"], {"verified": "population"}

    def cpi(package: object, **kwargs: object) -> tuple[pa.Table, dict[str, str]]:
        calls.append((package, kwargs))
        return tables["cpi_benchmark"], {"verified": "cpi"}

    monkeypatch.setattr(gold.fiscal, "query_fiscal_health_shares", shares)
    monkeypatch.setattr(gold.population, "query_fiscal_per_capita", rates)
    monkeypatch.setattr(gold.cpi, "query_fiscal_cpi_benchmark", cpi)
    result, receipts = gold.build_tables(inputs)
    assert len(calls) == 3
    assert all(package is inputs.package for package, _ in calls)
    assert calls[0][1] == {"period_evidence": inputs.fiscal_period_evidence}
    assert calls[1][1]["population_input"] is inputs.population_input
    assert calls[2][1]["cpi_input"] is inputs.cpi_input
    assert result["nominal"]["numerator_id"].to_pylist() == ["source-cell-1"]
    assert "denominator_id" not in result["nominal"].column_names
    assert receipts == {
        "shares": {"verified": "fiscal"},
        "per_capita": {"verified": "population"},
        "cpi_benchmark": {"verified": "cpi"},
    }
