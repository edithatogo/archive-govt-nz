"""Recovery fails on changed Bronze and disagreements between independent runs."""

import hashlib
import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz import mcp_server
from archive_govt_nz.domains.health_appropriations import fiscal_analytical_gold as gold
from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_recovery as recovery,
)


def source_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    archive = tmp_path / "archive"
    original = archive / "bronze-cas/sha256/aa/original"
    original.parent.mkdir(parents=True)
    original.write_bytes(b"immutable original")
    monkeypatch.setattr(
        recovery,
        "_SOURCE_BINDINGS",
        {"fixture": ("aa/original", hashlib.sha256(original.read_bytes()).hexdigest())},
    )
    definition = archive / "source-evidence/period.json"
    definition.parent.mkdir()
    definition.write_bytes(b"pinned period definition")
    monkeypatch.setattr(
        recovery,
        "_METADATA_BINDINGS",
        {
            "period.json": hashlib.sha256(definition.read_bytes()).hexdigest(),
        },
    )
    return archive, original


def test_changed_bronze_fails_before_derivative_creation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, original = source_fixture(tmp_path, monkeypatch)
    original.write_bytes(b"changed")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match="fiscal_recovery_source_pin_mismatch"):
        recovery.recover_fiscal_analytical_products(archive, output)
    assert not output.exists()
    original.write_bytes(b"immutable original")
    (archive / "source-evidence/period.json").write_bytes(b"changed definition")
    with pytest.raises(ValueError, match="fiscal_recovery_metadata_pin_mismatch"):
        recovery.recover_fiscal_analytical_products(archive, output)
    assert not output.exists()


def test_independent_product_disagreement_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, _ = source_fixture(tmp_path, monkeypatch)

    def build(_archive: Path, root: Path) -> dict[str, Any]:
        root.mkdir()
        (root / "product").write_text(root.name)
        return {"status": "verified"}

    monkeypatch.setattr(recovery, "_build_run", build)
    with pytest.raises(ValueError, match="fiscal_recovery_repeat_mismatch"):
        recovery.recover_fiscal_analytical_products(archive, tmp_path / "output")


def test_original_mutation_during_build_is_detected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive, original = source_fixture(tmp_path, monkeypatch)

    def build(_archive: Path, root: Path) -> dict[str, Any]:
        root.mkdir()
        (root / "product").write_bytes(b"same output")
        original.write_bytes(b"mutated during build")
        return {"status": "verified"}

    monkeypatch.setattr(recovery, "_build_run", build)
    with pytest.raises(ValueError, match="fiscal_recovery_source_pin_mismatch"):
        recovery.recover_fiscal_analytical_products(archive, tmp_path / "output")


def synthetic_gold(root: Path) -> str:
    """Transport fixture with no original-source or analytical approval claim."""
    root.mkdir()
    inventory = {}
    for name, schema in gold.TABLE_SCHEMAS.items():
        rows = []
        for year in (2025, 2024):
            row = dict.fromkeys(schema.names)
            row["period_end"] = date(year, 6, 30)
            if "measure" in row:
                row["measure"] = f"fixture_{name}"
            if "percent" in row:
                row["percent"] = Decimal("9.123456789012")
            rows.append(row)
        path = root / f"{name}.parquet"
        pq.write_table(pa.Table.from_pylist(rows, schema=schema), path)
        inventory[name] = {
            "filename": path.name,
            "bytes": path.stat().st_size,
            "rows": 2,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    marker = json.dumps({"schema_version": gold.VERSION, "tables": inventory}).encode()
    (root / "manifest.json").write_bytes(marker)
    return hashlib.sha256(marker).hexdigest()


def test_actual_console_mcp_arrow_readback_preserves_package(tmp_path: Path) -> None:
    root = tmp_path / "gold"
    pin = synthetic_gold(root)
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    result = recovery._interface_readback(root, pin)  # noqa: SLF001 - real transport boundary.
    assert set(result) == set(gold.TABLE_SCHEMAS)
    assert sum(table["rows"] for table in result.values()) == 8
    assert all(table["cli_mcp_arrow_equal"] for table in result.values())
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}


def test_corrupted_mcp_delivery_is_not_verified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "gold"
    pin = synthetic_gold(root)
    before = {p.name: p.read_bytes() for p in root.iterdir()}
    original = mcp_server.Server.handle_request

    def corrupt(
        server: mcp_server.Server, request: dict[str, Any]
    ) -> dict[str, Any] | None:
        response = original(server, request)
        if request["method"] == "tools/call":
            assert response is not None
            response["result"]["structuredContent"]["rows"][0]["period_end"] = (
                "1900-01-01"
            )
        return response

    monkeypatch.setattr(mcp_server.Server, "handle_request", corrupt)
    with pytest.raises(ValueError, match="fiscal_recovery_interface_mismatch"):
        recovery._interface_readback(root, pin)  # noqa: SLF001 - corrupt transport boundary.
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}

    def no_delivery(
        server: mcp_server.Server, request: dict[str, Any]
    ) -> dict[str, Any] | None:
        if request["method"] == "tools/call":
            return None
        return original(server, request)

    monkeypatch.setattr(mcp_server.Server, "handle_request", no_delivery)
    with pytest.raises(TypeError, match="fiscal_recovery_mcp_failed"):
        recovery._interface_readback(root, pin)  # noqa: SLF001 - absent transport response.
    assert before == {p.name: p.read_bytes() for p in root.iterdir()}
