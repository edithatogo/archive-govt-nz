"""Named analytical queries preserve exact values and share a read-only interface."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz import cli, mcp_server
from archive_govt_nz.domains.health_appropriations import fiscal_analytical_gold as gold
from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_operations as ops,
)


def package(root: Path) -> str:
    root.mkdir()
    inventory = {}
    for name, schema in gold.TABLE_SCHEMAS.items():
        records: list[dict[str, Any]] = []
        for year in (2025, 2024):
            row = dict.fromkeys(schema.names)
            row["period_end"] = date(year, 6, 30)
            if "period_start" in row:
                row["period_start"] = date(year - 1, 7, 1)
            if "measure" in row:
                row["measure"] = {
                    "shares": "health_share_gdp",
                    "per_capita": "health_spending_per_mean_resident",
                    "cpi_benchmark": "household_cpi_fy2025_benchmark",
                }[name]
            if "status" in row:
                row["status"] = (
                    "missing_population"
                    if name == "per_capita" and year == 2024
                    else "calculated"
                )
            values = {
                "source_object_sha256": "a" * 64,
                "source_vintage": "golden-budget-vintage",
                "period_definition_evidence_sha256": "d" * 64,
                "numerator_source_time_status": "actual",
                "denominator_source_time_status": "actual",
                "population_source_time_status": "actual",
                "numerator_id": f"health-{year}",
                "denominator_id": f"gdp-{year}",
                "population_id": f"population-{year}",
                "numerator_amount": Decimal("30311.125"),
                "denominator_amount": Decimal("436103.5"),
                "input_scale": "NZD millions",
                "numerator_coverage": "Core Crown Health",
                "denominator_coverage": "GDP",
                "accounting_basis": "PBE Standards",
                "denominator_accounting_basis": "PBE Standards",
                "health_source_sha256": "a" * 64,
                "health_vintage": "golden-budget-vintage",
                "population_source_sha256": "b" * 64,
                "population_vintage": "golden-population-vintage",
                "health_amount_millions": Decimal("30311.125"),
                "mean_population": Decimal(5000000),
                "source_dollars_per_mean_resident": Decimal("6062.225"),
                "unit": "source dollars per mean resident",
                "fiscal_period_evidence_sha256": "d" * 64,
                "population_period_evidence_sha256": "e" * 64,
                "formula_policy": "golden-exact-ratio",
                "cpi_source_sha256": "c" * 64,
                "cpi_vintage": "golden-cpi-vintage",
                "nominal_amount_millions": Decimal("30311.125"),
                "period_cpi_ids": [f"cpi-{year}-q{q}" for q in range(1, 5)],
                "period_cpi_source_time_statuses": ["actual"] * 4,
                "period_cpi_mean": Decimal("100.125"),
                "benchmark_period_start": date(2024, 7, 1),
                "benchmark_period_end": date(2025, 6, 30),
                "benchmark_cpi_ids": [f"base-q{q}" for q in range(1, 5)],
                "benchmark_cpi_source_time_statuses": ["actual"] * 4,
                "benchmark_cpi_mean": Decimal("100.0"),
                "cpi_benchmark_millions": Decimal("30349.0"),
                "numerator_gst_basis": "exclusive",
                "cpi_definition_evidence_sha256": "f" * 64,
                "cpi_source_quality_flags": [],
                "fiscal_source_quality_flags": [],
                "population_source_quality_flags": [],
                "source_quality_flags": [],
            }
            for key, value in values.items():
                if key in row:
                    row[key] = value
            if "percent" in row:
                row["percent"] = Decimal("6.950422262631")
            records.append(row)
        path = root / f"{name}.parquet"
        pq.write_table(pa.Table.from_pylist(records, schema=schema), path)
        inventory[name] = {
            "filename": path.name,
            "bytes": path.stat().st_size,
            "rows": 2,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    content = json.dumps({"schema_version": gold.VERSION, "tables": inventory}).encode()
    (root / "manifest.json").write_bytes(content)
    return hashlib.sha256(content).hexdigest()


@pytest.mark.parametrize("table", list(gold.TABLE_SCHEMAS))
def test_named_duckdb_query_is_exact_ordered_and_readonly(
    tmp_path: Path, table: str
) -> None:
    root = tmp_path / "gold"
    pin = package(root)
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    result = ops.query_fiscal_analytical_gold(root, pin, table=table, limit=1)
    assert result["status"] == "verified"
    assert result["rows"][0]["period_end"] == "2024-06-30"
    assert result["row_count"] == 1
    assert result["total_rows"] == 2
    assert result["truncated"] is True
    assert result["source_reverification"] == "not_performed"
    assert result["decimal_encoding"] == "exact_string"
    if table == "shares":
        assert result["rows"][0]["percent"] == "6.950422262631"
    expected = {
        "nominal": {
            "source_vintage": "golden-budget-vintage",
            "numerator_id": "health-2024",
            "numerator_amount": "30311.125000000000000000",
        },
        "shares": {
            "measure": "health_share_gdp",
            "denominator_id": "gdp-2024",
            "percent": "6.950422262631",
        },
        "per_capita": {
            "measure": "health_spending_per_mean_resident",
            "population_id": "population-2024",
            "status": "missing_population",
        },
        "cpi_benchmark": {
            "measure": "household_cpi_fy2025_benchmark",
            "period_cpi_ids": [f"cpi-2024-q{q}" for q in range(1, 5)],
            "cpi_benchmark_millions": "30349.000000000000",
        },
    }[table]
    assert {key: result["rows"][0][key] for key in expected} == expected
    assert before == {path.name: path.read_bytes() for path in root.iterdir()}


def test_duckdb_cross_product_golden_matrix_and_unapproved_real_view(
    tmp_path: Path,
) -> None:
    root = tmp_path / "gold"
    pin = package(root)
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    queried = {
        name: ops.query_fiscal_analytical_gold(root, pin, table=name, limit=2)["rows"]
        for name in gold.TABLE_SCHEMAS
    }
    by_period = {
        name: {row["period_end"]: row for row in rows} for name, rows in queried.items()
    }

    for year in (2024, 2025):
        period = f"{year}-06-30"
        nominal = by_period["nominal"][period]
        shares = by_period["shares"][period]
        per_capita = by_period["per_capita"][period]
        cpi = by_period["cpi_benchmark"][period]
        assert nominal["numerator_id"] == shares["numerator_id"]
        assert Decimal(nominal["numerator_amount"]) == Decimal(
            shares["numerator_amount"]
        )
        assert nominal["source_object_sha256"] == shares["source_object_sha256"]
        assert shares["denominator_id"] == f"gdp-{year}"
        assert Decimal(shares["denominator_amount"]) == Decimal("436103.5")
        assert per_capita["health_source_sha256"] == nominal["source_object_sha256"]
        assert per_capita["health_vintage"] == nominal["source_vintage"]
        assert Decimal(per_capita["health_amount_millions"]) == Decimal(
            nominal["numerator_amount"]
        )
        assert per_capita["population_id"] == f"population-{year}"
        assert per_capita["status"] == (
            "missing_population" if year == 2024 else "calculated"
        )
        assert cpi["nominal_amount_millions"] == nominal["numerator_amount"]
        assert cpi["period_cpi_ids"] == [f"cpi-{year}-q{q}" for q in range(1, 5)]

    unsupported_real = ops.query_fiscal_analytical_gold(
        root, pin, table="real", limit=2
    )
    assert unsupported_real["status"] == "failed"
    assert unsupported_real["error"] == "fiscal_gold_query_invalid"
    assert before == {path.name: path.read_bytes() for path in root.iterdir()}


def test_cli_mcp_parity_and_annotations(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "gold"
    pin = package(root)
    args = {
        "package_dir": str(root),
        "manifest_sha256": pin,
        "table": "shares",
        "limit": 2,
    }
    expected = mcp_server.call_tool(ops.TOOL_NAME, args)
    assert (
        cli.health_appropriations_query_fiscal_gold(root, pin, table="shares", limit=2)
        == 0
    )
    actual = json.loads(capsys.readouterr().out)
    actual.pop("command")
    assert actual == expected
    definition = next(
        tool for tool in mcp_server.list_tools() if tool["name"] == ops.TOOL_NAME
    )
    assert definition["annotations"]["readOnlyHint"] is True
    assert definition["annotations"]["openWorldHint"] is False


@pytest.mark.parametrize(
    "change",
    [
        {"table": "SELECT * FROM read_csv('/etc/passwd')"},
        {"limit": 201},
        {"limit": True},
    ],
)
def test_mcp_rejects_invalid_arguments_before_io(
    tmp_path: Path, change: dict[str, Any]
) -> None:
    args = {
        "package_dir": str(tmp_path / "absent"),
        "manifest_sha256": "0" * 64,
        "table": "shares",
        **change,
    }
    with pytest.raises(ValueError, match="arguments_invalid"):
        mcp_server.call_tool(ops.TOOL_NAME, args)


def test_invalid_package_cli_returns_bounded_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert (
        cli.health_appropriations_query_fiscal_gold(tmp_path / "absent", "0" * 64) == 2
    )
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "failed"
    assert result["error"] == "fiscal_gold_inventory_invalid"


def test_failed_query_is_a_protocol_tool_error_with_structured_receipt(
    tmp_path: Path,
) -> None:
    root = tmp_path / "gold"
    package(root)
    server = mcp_server.Server()
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": mcp_server.PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "fixture", "version": "1"},
            },
        }
    )
    server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": ops.TOOL_NAME,
                "arguments": {
                    "package_dir": str(root),
                    "manifest_sha256": "0" * 64,
                    "table": "shares",
                },
            },
        }
    )
    assert response is not None
    assert response["result"]["isError"] is True
    receipt = response["result"]["structuredContent"]
    assert receipt["status"] == "failed"
    assert receipt["error"] == "fiscal_gold_manifest_pin_mismatch"
