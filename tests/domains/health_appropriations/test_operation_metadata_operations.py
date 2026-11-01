"""Typed v5 metadata operations reuse source regeneration and immutable outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from tests.domains.health_appropriations.test_operation_context_gold import _inputs

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import operation_context_gold as gold
from archive_govt_nz.mcp_server import call_tool, list_tools

BUILD = "health-appropriations-build-operation-context-metadata"
VERIFY = "health-appropriations-verify-operation-context-metadata"
MCP = "health_appropriations_verify_operation_context_metadata"


def _case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], list[Path]]:
    inputs, sources = _inputs(tmp_path, monkeypatch)
    package = tmp_path / "gold"
    receipt = gold.export_operation_context_gold(inputs, sources, package, write=True)
    spec = tmp_path / "inputs.json"
    spec.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.health-operation-context-inputs/v1",
                "inputs": [
                    {
                        "profile": i.profile,
                        "package_dir": str(i.package_dir),
                        "manifest_sha256": i.manifest_sha256,
                    }
                    for i in inputs
                ],
            }
        )
    )
    return (
        {
            "input_spec": str(spec),
            "source_root": str(sources),
            "gold_package": str(package),
            "gold_manifest_sha256": receipt["manifest_sha256"],
            "output_dir": str(tmp_path / "metadata"),
        },
        [sources, package, *(i.package_dir for i in inputs), spec],
    )


def _snapshot(roots: list[Path]) -> dict[str, str | None]:
    return {
        str(path): hashlib.sha256(path.read_bytes()).hexdigest()
        if path.is_file()
        else None
        for root in roots
        for path in ([root] if root.is_file() else [root, *root.rglob("*")])
    }


def _cli(
    command: str, args: dict[str, Any], capsys: pytest.CaptureFixture[str]
) -> tuple[int, dict[str, Any]]:
    argv = [command]
    for key, value in args.items():
        argv.append("--" + key.replace("_", "-"))
        if value is not True:
            argv.append(str(value))
    result = app(argv, exit_on_error=False, result_action="return_value")
    return (result, json.loads(capsys.readouterr().out))


def test_v5_dry_run_build_and_read_only_cli_mcp_verify_reuse_real_products(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    args, roots = _case(tmp_path, monkeypatch)
    before = _snapshot(roots)
    code, planned = _cli(BUILD, args, capsys)
    assert code == 0
    assert planned["status"] == "dry_run"
    assert planned["schema_version"] == "archive-govt-nz.health-gold-metadata/v5"
    assert planned["packages"] == 1
    assert not Path(args["output_dir"]).exists()
    assert _snapshot(roots) == before
    code, written = _cli(BUILD, {**args, "write": True}, capsys)
    assert code == 0
    assert written["status"] == "written"
    assert written["verification"]["status"] == "verified"
    assert written["manifest_sha256"] == planned["manifest_sha256"]
    verify_args = {**args, "manifest_sha256": written["manifest_sha256"]}
    output = Path(args["output_dir"])
    preserved = _snapshot([*roots, output])
    code, verified = _cli(VERIFY, verify_args, capsys)
    assert code == 0
    assert verified.pop("command") == VERIFY
    assert call_tool(MCP, verify_args) == verified == written["verification"]
    assert (
        verified["verification_scope"]
        == "source_regenerated_gold_metadata_reconstructed"
    )
    assert verified["rights"] == "not_evaluated"
    assert verified["publication"] == "not_performed"
    assert _snapshot([*roots, output]) == preserved
    code, refused = _cli(BUILD, {**args, "write": True}, capsys)
    assert code == 2
    assert refused["status"] == "failed"
    assert _snapshot([*roots, output]) == preserved
    repeat = tmp_path / "repeat"
    code, repeated = _cli(
        BUILD, {**args, "output_dir": str(repeat), "write": True}, capsys
    )
    assert code == 0
    assert repeated["manifest_sha256"] == written["manifest_sha256"]
    assert {p.name: p.read_bytes() for p in output.iterdir()} == {
        p.name: p.read_bytes() for p in repeat.iterdir()
    }


def test_dry_run_rejects_wrong_gold_pin_and_output_overlap_without_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    args, roots = _case(tmp_path, monkeypatch)
    before = _snapshot(roots)
    spec = Path(args["input_spec"])
    original_spec = spec.read_bytes()
    malformed = json.loads(original_spec)
    del malformed["inputs"][0]["manifest_sha256"]
    spec.write_text(json.dumps(malformed))
    malformed_snapshot = _snapshot(roots)
    code, refused = _cli(BUILD, args, capsys)
    assert code == 2
    assert refused["status"] == "failed"
    assert _snapshot(roots) == malformed_snapshot
    spec.write_bytes(original_spec)
    for changes in [
        {"gold_manifest_sha256": "0" * 64},
        {"output_dir": str(Path(args["source_root"]) / "new")},
        {"output_dir": str(Path(args["gold_package"]) / "new")},
        {"output_dir": str(roots[2] / "new")},
    ]:
        code, receipt = _cli(BUILD, {**args, **changes}, capsys)
        assert code == 2
        assert receipt["status"] == "failed"
        assert _snapshot(roots) == before
    assert not Path(args["output_dir"]).exists()


def test_metadata_independent_pin_and_self_consistent_tampering_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    args, roots = _case(tmp_path, monkeypatch)
    _, built = _cli(BUILD, {**args, "write": True}, capsys)
    output = Path(args["output_dir"])
    before = _snapshot([*roots, output])
    for field in ("manifest_sha256", "gold_manifest_sha256"):
        invalid = {**args, "manifest_sha256": built["manifest_sha256"], field: "0" * 64}
        code, receipt = _cli(VERIFY, invalid, capsys)
        assert code == 2
        assert receipt["status"] == "failed"
        with pytest.raises(ValueError, match="gold_metadata_contract"):
            call_tool(MCP, invalid)
        assert _snapshot([*roots, output]) == before
    citation = output / "citations.json"
    content = json.loads(citation.read_bytes())
    content["records"][0]["rights"] = "eligible"
    citation.write_text(json.dumps(content))
    marker = output / "MANIFEST.json"
    manifest = json.loads(marker.read_bytes())
    manifest["payloads"]["citations.json"] = {
        "sha256": hashlib.sha256(citation.read_bytes()).hexdigest(),
        "bytes": citation.stat().st_size,
    }
    marker.write_text(json.dumps(manifest))
    forged = {
        **args,
        "manifest_sha256": hashlib.sha256(marker.read_bytes()).hexdigest(),
    }
    tampered = _snapshot([*roots, output])
    code, receipt = _cli(VERIFY, forged, capsys)
    assert code == 2
    assert receipt["status"] == "failed"
    with pytest.raises(ValueError, match="gold_metadata_contract"):
        call_tool(MCP, forged)
    assert _snapshot([*roots, output]) == tampered
    assert built["manifest_sha256"] != forged["manifest_sha256"]


def test_mcp_contract_is_closed_read_only_and_keeps_legacy_profiles() -> None:
    definition = next(tool for tool in list_tools() if tool["name"] == MCP)
    assert definition["annotations"]["readOnlyHint"] is True
    assert definition["annotations"]["destructiveHint"] is False
    assert definition["outputSchema"]["properties"]["packages"] == {"const": 1}
    for invalid in ({}, {"input_spec": "a", "extra": True}):
        with pytest.raises(ValueError, match="operation_metadata_arguments_invalid"):
            call_tool(MCP, invalid)
    legacy = next(
        tool
        for tool in list_tools()
        if tool["name"] == "health_appropriations_verify_gold_metadata"
    )
    assert legacy["outputSchema"]["properties"]["schema_version"]["enum"] == [
        "archive-govt-nz.health-gold-metadata/v3",
        "archive-govt-nz.health-gold-metadata/v4",
    ]
