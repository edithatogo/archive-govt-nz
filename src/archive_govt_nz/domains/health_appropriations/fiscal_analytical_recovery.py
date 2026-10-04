"""Two independent Bronze-to-Fiscal-Gold/report rebuilds and interface readbacks."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from archive_govt_nz import mcp_server
from archive_govt_nz.domains.health_appropriations import (
    cpi,
    historical,
    population_annual_silver,
)
from archive_govt_nz.domains.health_appropriations import (
    cpi_canonical_projection as cpi_source,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_gold as gold,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_operations as operations,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_reports as reports,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_cpi_benchmark as benchmark,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_crown_literals as fiscal_source,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_per_capita as rates,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_share_analysis as shares,
)
from archive_govt_nz.domains.health_appropriations import (
    population_annual_canonical_projection as population_source,
)
from archive_govt_nz.domains.health_appropriations.historical_canonical_export import (
    export_historical_canonical,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
)

VERSION = "archive-govt-nz.fiscal-analytical-recovery/v1"
_MAX_BYTES = 16 * 1024 * 1024
_MAX_CONSOLE_BYTES = 8 * 1024 * 1024
_SOURCE_BINDINGS = {
    family: (f"{pin[:2]}/{pin}", pin)
    for family, pin in (
        ("fiscal", fiscal_source.SOURCE_SHA256),
        ("population", population_source.SOURCE_SHA256),
        ("cpi", cpi_source.SOURCE_SHA256),
    )
}
_METADATA_BINDINGS = {
    "fiscal-series-notes-web-observation-20261004.json": shares.PERIOD_EVIDENCE_SHA256,
    "population-mean-period-web-observation-20261004.json": (
        rates.POPULATION_PERIOD_EVIDENCE_SHA256
    ),
    "cpi-definition-web-observation-20261004.json": benchmark.CPI_DEFINITION_SHA256,
}


def _require(condition: object, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _digest(path: Path) -> str:
    _require(
        path.is_file() and not path.is_symlink() and path.stat().st_size <= _MAX_BYTES,
        "fiscal_recovery_source_bounds_invalid",
    )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _source_snapshot(archive: Path) -> dict[str, str]:
    result = {}
    for family, (relative, expected) in _SOURCE_BINDINGS.items():
        actual = _digest(archive / "bronze-cas/sha256" / relative)
        _require(actual == expected, "fiscal_recovery_source_pin_mismatch")
        result[family] = actual
    for name, expected in _METADATA_BINDINGS.items():
        actual = _digest(archive / "source-evidence" / name)
        _require(actual == expected, "fiscal_recovery_metadata_pin_mismatch")
        result[name] = actual
    return result


def _inventory(root: Path) -> dict[str, dict[str, Any]]:
    return {
        path.relative_to(root).as_posix(): {
            "bytes": path.stat().st_size,
            "sha256": _digest(path),
        }
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _console(*args: str) -> dict[str, Any]:
    cli_name = "archive-govt-nz.exe" if sys.platform == "win32" else "archive-govt-nz"
    command = Path(sys.executable).parent / cli_name
    _require(command.is_file(), "fiscal_recovery_console_unavailable")
    result = subprocess.run(  # noqa: S603 - fixed installed CLI, shell-free bounded arguments.
        [str(command), *args], capture_output=True, timeout=120, check=False
    )
    _require(
        result.returncode == 0 and len(result.stdout) <= _MAX_CONSOLE_BYTES,
        "fiscal_recovery_console_failed",
    )
    return json.loads(result.stdout)


def _interface_readback(root: Path, pin: str) -> dict[str, Any]:
    before = _inventory(root)
    server = mcp_server.Server()
    server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": mcp_server.PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "fiscal-recovery", "version": "1"},
            },
        }
    )
    server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
    results = {}
    for ordinal, name in enumerate(gold.TABLE_SCHEMAS):
        cli = _console(
            "health-appropriations-query-fiscal-gold",
            str(root),
            pin,
            "--table",
            name,
            "--limit",
            "200",
        )
        cli.pop("command")
        response = server.handle_request(
            {
                "jsonrpc": "2.0",
                "id": ordinal + 2,
                "method": "tools/call",
                "params": {
                    "name": operations.TOOL_NAME,
                    "arguments": {
                        "package_dir": str(root),
                        "manifest_sha256": pin,
                        "table": name,
                        "limit": 200,
                    },
                },
            }
        )
        if not isinstance(response, dict):
            reason = "fiscal_recovery_mcp_failed"
            raise TypeError(reason)
        _require(
            response["result"]["isError"] is False,
            "fiscal_recovery_mcp_failed",
        )
        _require(
            cli == response["result"]["structuredContent"],
            "fiscal_recovery_interface_mismatch",
        )
        rows = pq.read_table(root / f"{name}.parquet").to_pylist()
        rows.sort(key=lambda row: (row["period_end"], row.get("measure", "")))
        expected = json.loads(json.dumps(rows, default=str))
        _require(
            cli["rows"] == expected
            and not cli["truncated"]
            and cli["row_count"] == len(rows),
            "fiscal_recovery_arrow_mismatch",
        )
        results[name] = {
            "rows": len(rows),
            "cli_mcp_arrow_equal": True,
            "result_sha256": hashlib.sha256(
                json.dumps(cli, sort_keys=True).encode()
            ).hexdigest(),
        }
    _require(_inventory(root) == before, "fiscal_recovery_query_mutation")
    return results


def _build_run(archive: Path, root: Path) -> dict[str, Any]:
    """Consume only original objects and separately pinned definition evidence."""
    root.mkdir()
    cas = archive / "bronze-cas/sha256"
    source = cas / _SOURCE_BINDINGS["fiscal"][0]
    raw, canonical = root / "historical-raw", root / "historical-canonical"
    historical.normalize_historical_workbook(
        source,
        raw,
        expected_sha256=fiscal_source.SOURCE_SHA256,
        source_locator=fiscal_source.SOURCE_URL,
        source_vintage=fiscal_source.VINTAGE,
        observed_at="2026-08-31T12:26:32Z",
    )
    raw_pin = _digest(raw / "MANIFEST.json")
    export_historical_canonical(raw, source, raw_pin, canonical, write=True)
    package = CanonicalPackageInput(
        "historical",
        canonical,
        _digest(canonical / "LOCAL_CANONICAL.json"),
        source,
        raw,
        raw_pin,
    )
    population, prices = root / "population", root / "cpi"
    population_annual_silver.normalize_population_annual(
        cas / _SOURCE_BINDINGS["population"][0],
        population,
        expected_sha256=population_source.SOURCE_SHA256,
        source_locator=population_source.SOURCE_LOCATOR,
        source_vintage=population_source.SOURCE_VINTAGE,
        observed_at=population_source.OBSERVED_AT,
        dry_run=False,
    )
    cpi.normalize_cpi(
        cas / _SOURCE_BINDINGS["cpi"][0],
        prices,
        expected_sha256=cpi_source.SOURCE_SHA256,
        source_locator=cpi_source.SOURCE_LOCATOR,
        source_vintage=cpi_source.SOURCE_VINTAGE,
        observed_at=cpi_source.OBSERVED_AT,
        dry_run=False,
    )
    evidence = archive / "source-evidence"
    inputs = gold.FiscalAnalyticalInputs(
        package,
        evidence / "fiscal-series-notes-web-observation-20261004.json",
        rates.PopulationInput(population, _digest(population / "MANIFEST.json"), cas),
        evidence / "population-mean-period-web-observation-20261004.json",
        benchmark.CpiInput(prices, _digest(prices / "MANIFEST.json"), cas),
        evidence / "cpi-definition-web-observation-20261004.json",
    )
    product = gold.export_fiscal_analytical_gold(inputs, root / "gold", write=True)
    report = reports.export_fiscal_analytical_reports(
        root / "gold", product["manifest_sha256"], root / "reports", write=True
    )
    verification = _console(
        "health-appropriations-verify-fiscal-reports",
        str(root / "reports"),
        report["manifest_sha256"],
    )
    verification.pop("command")
    _require(
        verification["status"] == "verified", "fiscal_recovery_report_readback_failed"
    )
    return {
        "gold": product,
        "reports": report,
        "report_cli_readback": verification,
        "query_interfaces": _interface_readback(
            root / "gold", product["manifest_sha256"]
        ),
    }


def recover_fiscal_analytical_products(archive: Path, output: Path) -> dict[str, Any]:
    """Keep both independent runs for the caller to inventory and dispose of."""
    _require(
        not output.resolve().is_relative_to(archive.resolve())
        and not archive.resolve().is_relative_to(output.resolve()),
        "fiscal_recovery_output_overlap",
    )
    before = _source_snapshot(archive)
    output.mkdir(parents=True, exist_ok=False)
    first, second = output / "first", output / "second"
    first_receipt = _build_run(archive, first)
    second_receipt = _build_run(archive, second)
    inventory = _inventory(first)
    _require(
        inventory == _inventory(second) and first_receipt == second_receipt,
        "fiscal_recovery_repeat_mismatch",
    )
    _require(_source_snapshot(archive) == before, "fiscal_recovery_original_mutation")
    return {
        "schema_version": VERSION,
        "status": "verified",
        "source_inputs": before,
        "originals_and_metadata_unchanged": True,
        "fresh_bronze_builds": 2,
        "retained_silver_consumed": False,
        "repeat_identical": True,
        "output_inventory": inventory,
        "products": first_receipt,
        "rights": "not_evaluated",
        "publication": "not_performed",
        "full_track_completion": "not_asserted",
    }
