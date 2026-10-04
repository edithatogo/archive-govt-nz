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
            if "measure" in row:
                row["measure"] = f"fixture_{name}"
            if "status" in row:
                row["status"] = "calculated" if year == 2025 else "missing_population"
            if "percent" in row:
                row["percent"] = Decimal("9.123456789012")
            if "numerator_id" in row:
                row["numerator_id"] = f"source-cell-{year}"
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
        assert result["rows"][0]["percent"] == "9.123456789012"
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
