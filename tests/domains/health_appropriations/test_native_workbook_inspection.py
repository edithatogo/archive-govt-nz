"""Closed native inspection projects qualified profiles through CLI and MCP."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import subprocess
from pathlib import Path
from typing import Never

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from jsonschema import Draft202012Validator
from tests.cli.test_mcp_cli_contract import _ready_server
from tests.domains.health_appropriations.test_forecast_detail_source_adapter import (
    OBSERVED,
    setup_source,
)
from tests.domains.health_appropriations.test_literal_source_adapters import admission

from archive_govt_nz import cli, mcp_server
from archive_govt_nz.domains.health_appropriations import forecast
from archive_govt_nz.domains.health_appropriations import literal_packages as packages
from archive_govt_nz.domains.health_appropriations import (
    native_workbook_inspection as inspection,
)
from archive_govt_nz.domains.health_appropriations.schema_drift import (
    schema_fingerprint,
)


@pytest.mark.parametrize("index", [0, 1])
def test_known_source_returns_both_native_profiles_without_paths_or_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, index: int
) -> None:
    bronze, spec = setup_source(monkeypatch, index)
    source = tmp_path / spec.source_sha256[:2] / spec.source_sha256
    source.parent.mkdir()
    source.write_bytes(bronze)
    expected = tmp_path / "expected"
    forecast.normalize_forecast_workbook(
        source,
        expected / spec.summary_profile,
        expected_sha256=spec.source_sha256,
        profile=spec.summary_profile,
        source_locator=spec.source_locator,
        source_vintage=spec.source_vintage,
        observed_at=OBSERVED,
    )
    context = {
        "source_object_sha256": spec.source_sha256,
        "source_locator": spec.source_locator,
        "source_vintage": spec.source_vintage,
        "observed_at": OBSERVED,
    }
    packages.write_literal_package(
        expected / spec.detail_profile,
        admission(spec.detail_profile, context),
        profile=spec.detail_profile,
        context=context,
    )
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
    result = inspection.inspect_native_workbook(
        tmp_path, source_id=spec.adapter_id, observed_at=OBSERVED
    )
    Draft202012Validator(inspection.OUTPUT_SCHEMA).validate(result)
    assert result["status"] == "inspected"
    assert result["source_object_sha256"] == spec.source_sha256
    assert result["selection"]["adapter"] == {"id": spec.adapter_id, "version": "2"}
    assert result["native_kind"] == "health-native-compound/v1"
    assert [p["profile_id"] for p in result["profiles"]] == [
        spec.summary_profile,
        spec.detail_profile,
    ]
    assert [p["counts"]["facts"] for p in result["profiles"]] == [1, 1]
    assert [p["counts"]["excluded_sheets"] for p in result["profiles"]] == [2, 0]
    assert [r["rows"] for r in result["profiles"][0]["recordsets"]] == [1, 1, 2]
    assert [r["rows"] for r in result["profiles"][1]["recordsets"]] == [1, 2, 3]
    assert all(len(p["native_manifest_sha256"]) == 64 for p in result["profiles"])
    for profile, contract in zip(
        result["profiles"], inspection.adapters.profile_contracts(spec), strict=True
    ):
        folder = expected / profile["profile_id"]
        assert (
            profile["native_manifest_sha256"]
            == hashlib.sha256((folder / "MANIFEST.json").read_bytes()).hexdigest()
        )
        assert (
            profile["metadata_schema_version"]
            == json.loads((folder / "MANIFEST.json").read_text())["schema_version"]
        )
        for recordset, table_contract in zip(
            profile["recordsets"], contract.recordsets, strict=True
        ):
            assert (
                recordset["output_sha256"]
                == hashlib.sha256((folder / recordset["name"]).read_bytes()).hexdigest()
            )
            assert recordset["schema_id"] == table_contract.schema_id
            assert recordset["schema_version"] == table_contract.schema_version
            assert recordset["schema_sha256"] == schema_fingerprint(
                table_contract.schema
            )
    assert str(tmp_path) not in json.dumps(result)
    assert "summary-record" not in json.dumps(result)
    assert source.read_bytes() == bronze
    assert (
        sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*"))
        == before
    )
    assert (
        inspection.inspect_native_workbook(
            tmp_path, source_id=spec.adapter_id, observed_at=OBSERVED
        )
        == result
    )


@pytest.mark.parametrize(
    "defect", ["changed", "missing", "traversal", "unknown", "naive-time"]
)
def test_bad_source_or_context_fails_closed_without_disclosing_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    bronze, spec = setup_source(monkeypatch, 0)
    source = tmp_path / spec.source_sha256[:2] / spec.source_sha256
    source.parent.mkdir()
    source.write_bytes(bronze)
    root, source_id, observed = tmp_path, spec.adapter_id, OBSERVED
    if defect == "changed":
        source.write_bytes(bronze + b"changed")
    elif defect == "missing":
        source.unlink()
    elif defect == "traversal":
        root = tmp_path / "unused" / ".."
    elif defect == "unknown":
        source_id = "unknown-private-marker"
    else:
        observed = "2026-08-30T08:58:00"
    result = inspection.inspect_native_workbook(
        root, source_id=source_id, observed_at=observed
    )
    Draft202012Validator(inspection.OUTPUT_SCHEMA).validate(result)
    assert result["status"] == "failed"
    assert str(tmp_path) not in json.dumps(result)
    assert "unknown-private-marker" not in json.dumps(result)
    assert "profiles" not in result


@pytest.mark.parametrize("component", ["root", "prefix", "object"])
def test_symlink_components_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component: str
) -> None:
    bronze, spec = setup_source(monkeypatch, 0)
    root = tmp_path / "cas"
    source = root / spec.source_sha256[:2] / spec.source_sha256
    source.parent.mkdir(parents=True)
    source.write_bytes(bronze)
    target = (
        root
        if component == "root"
        else source.parent
        if component == "prefix"
        else source
    )
    retained = target.with_name(target.name + "-retained")
    target.rename(retained)
    try:
        target.symlink_to(retained, target_is_directory=component != "object")
    except OSError:
        if os.name == "nt":
            pytest.skip("Windows runner cannot create this symlink")
        raise
    result = inspection.inspect_native_workbook(
        root, source_id=spec.adapter_id, observed_at=OBSERVED
    )
    assert result["status"] == "failed"


@pytest.mark.parametrize("component", ["root", "prefix"])
def test_junction_metadata_is_refused_before_source_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component: str
) -> None:
    bronze, spec = setup_source(monkeypatch, 0)
    root = tmp_path / "cas"
    source = root / spec.source_sha256[:2] / spec.source_sha256
    source.parent.mkdir(parents=True)
    source.write_bytes(bronze)
    junction = root if component == "root" else source.parent
    # Model Windows metadata on other hosts; real NTFS coverage is below.
    monkeypatch.setattr(Path, "is_junction", lambda path: path == junction)
    reads: list[Path] = []
    original = inspection.verified_snapshot

    def read_snapshot(path: Path, pin: str, *, max_bytes: int) -> bytes:
        reads.append(path)
        return original(path, pin, max_bytes=max_bytes)

    monkeypatch.setattr(inspection, "verified_snapshot", read_snapshot)
    result = inspection.inspect_native_workbook(
        root, source_id=spec.adapter_id, observed_at=OBSERVED
    )
    assert result["status"] == "failed"
    assert "profiles" not in result
    assert reads == []
    assert source.read_bytes() == bronze


@pytest.mark.skipif(os.name != "nt", reason="Real NTFS junctions require Windows")
@pytest.mark.parametrize("component", ["root", "prefix"])
def test_windows_junction_cannot_redirect_inspection_outside_cas(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, component: str
) -> None:
    bronze, spec = setup_source(monkeypatch, 0)
    root = tmp_path / "cas"
    source = root / spec.source_sha256[:2] / spec.source_sha256
    source.parent.mkdir(parents=True)
    source.write_bytes(bronze)
    target = root if component == "root" else source.parent
    retained = target.with_name(target.name + "-outside")
    target.rename(retained)
    subprocess.run(
        ["cmd", "/d", "/c", "mklink", "/J", str(target), str(retained)],
        capture_output=True,
        text=True,
        check=True,
        timeout=10,
    )
    try:
        assert target.is_junction()
        assert not target.is_symlink()

        def refuse_read(*_args: object, **_kwargs: object) -> Never:
            message = "junction inspection attempted a source read"
            raise AssertionError(message)

        monkeypatch.setattr(inspection, "verified_snapshot", refuse_read)
        result = inspection.inspect_native_workbook(
            root, source_id=spec.adapter_id, observed_at=OBSERVED
        )
        assert result["status"] == "failed"
        assert "profiles" not in result
        assert source.read_bytes() == bronze
    finally:
        target.rmdir()


@pytest.mark.parametrize("outcome", ["inspected", "preserved_only", "failed"])
def test_actual_cli_and_jsonrpc_share_read_only_status_and_descriptors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    outcome: str,
) -> None:
    bronze, spec = setup_source(monkeypatch, 0)
    source = tmp_path / spec.source_sha256[:2] / spec.source_sha256
    source.parent.mkdir()
    source.write_bytes(bronze if outcome != "failed" else bronze + b"changed")
    if outcome == "preserved_only":

        def fail_admission(*_args: object, **_kwargs: object) -> Never:
            message = "fixture sibling failure"
            raise ValueError(message)

        monkeypatch.setattr(packages, "admit_literal_snapshot", fail_admission)
    expected = inspection.inspect_native_workbook(
        tmp_path, source_id=spec.adapter_id, observed_at=OBSERVED
    )
    assert expected["status"] == outcome
    before = {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    }

    def deny_write(*_args: object, **_kwargs: object) -> Never:
        message = "inspection attempted a Python filesystem write"
        raise AssertionError(message)

    original_open, original_parquet = os.open, pq.write_table

    def read_only_open(
        path: str | bytes | Path,
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        assert not flags & (
            os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        )
        return original_open(path, flags, mode, dir_fd=dir_fd)

    def memory_parquet(table: pa.Table, where: object) -> None:
        assert isinstance(where, pa.BufferOutputStream)
        original_parquet(table, where)

    monkeypatch.setattr(Path, "write_bytes", deny_write)
    monkeypatch.setattr(Path, "write_text", deny_write)
    monkeypatch.setattr(Path, "mkdir", deny_write)
    monkeypatch.setattr(os, "open", read_only_open)
    monkeypatch.setattr(pq, "write_table", memory_parquet)
    monkeypatch.setattr(socket.socket, "connect", deny_write)
    monkeypatch.setattr(socket, "create_connection", deny_write)
    monkeypatch.setattr(socket, "getaddrinfo", deny_write)
    code = cli.app(
        [
            "health-appropriations-inspect-native-workbook",
            "--cas-root",
            str(tmp_path),
            "--source-id",
            spec.adapter_id,
            "--observed-at",
            OBSERVED,
        ],
        exit_on_error=False,
        result_action="return_value",
    )
    actual = json.loads(capsys.readouterr().out)
    actual.pop("command")
    assert actual == expected
    assert code == (0 if outcome == "inspected" else 2)
    response = _ready_server().handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": inspection.TOOL_NAME,
                "arguments": {
                    "cas_root": str(tmp_path),
                    "source_id": spec.adapter_id,
                    "observed_at": OBSERVED,
                },
            },
        }
    )
    assert response is not None
    assert response["result"]["structuredContent"] == expected
    assert response["result"]["isError"] == (outcome != "inspected")
    assert {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in tmp_path.rglob("*")
        if p.is_file()
    } == before
    if outcome == "preserved_only":
        assert expected["profiles"] == []
        assert (
            expected["source_losses"][0]["reason"]
            == "reviewed_forecast_detail_admission_failed"
        )


@pytest.mark.parametrize("defect", ["write", "unknown"])
def test_mcp_invalid_arguments_are_redacted(defect: str) -> None:
    tool = next(t for t in mcp_server.list_tools() if t["name"] == inspection.TOOL_NAME)
    assert tool["annotations"] == {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    arguments: dict[str, object] = {
        "cas_root": "/private-path-marker",
        "source_id": inspection.adapters.SOURCES[0].adapter_id,
        "observed_at": OBSERVED,
    }
    if defect == "write":
        arguments["write"] = True
    else:
        arguments["source_id"] = "private-source-marker"
    response = _ready_server().handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": inspection.TOOL_NAME,
                "arguments": arguments,
            },
        }
    )
    assert response is not None
    assert response["error"]["code"] == mcp_server.JSONRPC_INVALID_PARAMS
    assert (
        response["error"]["message"] == "Invalid native workbook inspection arguments"
    )
    assert "private-path-marker" not in json.dumps(response)
    assert "private-source-marker" not in json.dumps(response)
