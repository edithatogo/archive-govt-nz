"""Gold delivery retains exact comparison inputs and fails closed on corruption."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest
from tests.domains.health_appropriations.test_budget_vintage_comparison import (
    inputs,
    row,
)

from archive_govt_nz.domains.health_appropriations import budget_comparison_gold as gold
from archive_govt_nz.mcp_server import Server


def fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    data = inputs(
        tmp_path,
        monkeypatch,
        [row(2025, "Estimated Actual", 1), row(2026, "Main Estimates", 2, "Old")],
        [row(2025, "Actuals", 4), row(2026, "Estimated Actual", 9, "New")],
    )
    target = tmp_path / "gold"
    dry = gold.export_budget_comparison(data[0], data[1], target, write=False)
    assert dry["status"] == "dry_run"
    assert not target.exists()
    receipt = gold.export_budget_comparison(data[0], data[1], target, write=True)
    return target, receipt["manifest_sha256"]


def test_package_reports_exact_queries_and_exclusive_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, pin = fixture(tmp_path, monkeypatch)
    result = gold.query_budget_comparison(target, pin, limit=200)
    assert result["status"] == "verified"
    assert result["total_rows"] == 3
    assert [r["difference_later_minus_earlier"] for r in result["rows"]] == [
        "3.000",
        None,
        None,
    ]
    assert result["rows"][0]["earlier_amounts"] == ["1.000"]
    assert result["rows"][0]["earlier_source_rows"] == [2]
    assert result["source_reverification"] == "not_performed"
    assert "supplementary_estimates_excluded" in result["caveats"]
    assert result["source_bindings"]["earlier"]["source_vintage"] == "Budget-2025"
    console = Path(sys.executable).parent / (
        "archive-govt-nz.exe" if sys.platform == "win32" else "archive-govt-nz"
    )
    delivered = subprocess.run(
        [
            str(console),
            "health-appropriations-query-budget-comparison",
            str(target),
            pin,
            "--limit",
            "200",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    envelope = json.loads(delivered.stdout)
    envelope.pop("command")
    assert envelope == result
    assert not result["truncated"]
    assert gold.query_budget_comparison(target, pin, limit=1)["truncated"]
    assert gold.query_budget_comparison(target, pin, limit=True)["status"] == "failed"
    assert gold.query_budget_comparison(target, "0" * 64)["status"] == "failed"
    summary = json.loads((target / "summary.json").read_text())
    assert summary["plot_points"] == 1
    assert summary["plot_excluded_groups"] == 2
    assert (target / "differences.png").read_bytes().startswith(b"\x89PNG")
    data = [
        gold.comparison.BudgetComparisonInput(
            tmp_path / f"{year}.xlsx",
            tmp_path / str(year),
            hashlib.sha256(
                (tmp_path / str(year) / "MANIFEST.json").read_bytes()
            ).hexdigest(),
        )
        for year in (2025, 2026)
    ]
    with pytest.raises(FileExistsError):
        gold.export_budget_comparison(data[0], data[1], target, write=True)
    with pytest.raises(ValueError, match="budget_comparison_gold_contract"):
        gold.export_budget_comparison(data[0], data[1], data[0].package)


def test_corrupt_and_extra_payloads_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, pin = fixture(tmp_path, monkeypatch)
    (target / "summary.json").write_bytes(b"changed")
    assert gold.query_budget_comparison(target, pin)["status"] == "failed"
    (target / "extra.txt").write_text("extra")
    assert gold.query_budget_comparison(target, pin)["status"] == "failed"


def test_mcp_native_protocol_and_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target, pin = fixture(tmp_path, monkeypatch)
    server = Server()
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test", "version": "1"},
            },
        }
    )
    server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
    arguments = {"package_dir": str(target), "manifest_sha256": pin, "limit": 200}
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": gold.TOOL_NAME, "arguments": arguments},
        }
    )
    assert response is not None
    assert not response["result"]["isError"]
    assert response["result"]["structuredContent"] == gold.query_budget_comparison(
        target, pin, limit=200
    )
    arguments["manifest_sha256"] = "0" * 64
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": gold.TOOL_NAME, "arguments": arguments},
        }
    )
    assert response is not None
    assert response["result"]["isError"]
