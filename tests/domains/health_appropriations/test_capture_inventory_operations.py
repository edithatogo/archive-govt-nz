# SPDX-License-Identifier: Apache-2.0
"""Contracts for pinned read-only capture inventory reconciliation."""

import hashlib
import json
from pathlib import Path

import pytest

from archive_govt_nz.cli import app
from archive_govt_nz.mcp_server import call_tool

TOOL = "health_appropriations_reconcile_capture_inventory"


def test_reconcile_cli_mcp_pins_and_redaction(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    url = "https://example.govt.nz/private-source"
    row = {"source_id": "a", "url": url, "family": "vote", "disposition": "discovered"}
    census = {
        "schema_version": "archive-govt-nz.health-source-census/v1",
        "record_count": 1,
        "records": [row],
    }
    payload = json.dumps(census).encode()
    census_path = tmp_path / "private-census.json"
    census_path.write_bytes(payload)
    request_path = tmp_path / "private-request.json"
    request_path.write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    manifest = {
        "schema_version": "archive-govt-nz.health-capture-manifest/v1",
        "capture_context": {
            "contract": "health-capture-resume/v1",
            "census_sha256": digest,
        },
        "results": [
            {
                "source_id": "a",
                "url": url,
                "state": "captured",
                "request_url_sha256": hashlib.sha256(url.encode()).hexdigest(),
                "sha256": "a" * 64,
                "bytes": 7,
            }
        ],
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_bytes = json.dumps(manifest).encode()
    manifest_path.write_bytes(manifest_bytes)

    def pin(name: str, path: Path, sha: str) -> dict[str, str]:
        return {"name": name, "path": str(path), "sha256": sha}

    args = {
        "censuses": [pin("census", census_path, digest)],
        "captures": [
            {
                "manifest": pin(
                    "manifest",
                    manifest_path,
                    hashlib.sha256(manifest_bytes).hexdigest(),
                ),
                "request": pin("request", request_path, digest),
            }
        ],
    }
    before = {path.name: path.read_bytes() for path in tmp_path.iterdir()}
    result = call_tool(TOOL, args)
    assert result == call_tool(TOOL, args)
    assert result["summary"]["recorded_captured_resource_count"] == 1
    assert (
        app(
            [
                "health-appropriations-reconcile-capture-inventory",
                "--censuses-json",
                json.dumps(args["censuses"]),
                "--captures-json",
                json.dumps(args["captures"]),
            ],
            exit_on_error=False,
            result_action="return_value",
        )
        == 0
    )
    output = capsys.readouterr().out
    assert json.loads(output) == result
    assert url not in output
    assert str(tmp_path) not in output
    assert {path.name: path.read_bytes() for path in tmp_path.iterdir()} == before
    census_path.write_bytes(b"tampered")
    with pytest.raises(ValueError, match="input_digest_mismatch"):
        call_tool(TOOL, args)


def test_reconcile_rejects_unbound_request(tmp_path: Path) -> None:
    census = {
        "schema_version": "archive-govt-nz.health-source-census/v1",
        "record_count": 0,
        "records": [],
    }
    path = tmp_path / "input.json"
    payload = json.dumps(census).encode()
    path.write_bytes(payload)
    pin = {
        "name": "census",
        "path": str(path),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    manifest = {
        "schema_version": "archive-govt-nz.health-capture-manifest/v1",
        "capture_context": {
            "contract": "health-capture-resume/v1",
            "census_sha256": "0" * 64,
        },
        "results": [],
    }
    mp = tmp_path / "manifest.json"
    data = json.dumps(manifest).encode()
    mp.write_bytes(data)
    args = {
        "censuses": [pin],
        "captures": [
            {
                "manifest": {
                    "name": "manifest",
                    "path": str(mp),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            }
        ],
    }
    with pytest.raises(ValueError, match="capture_request_missing"):
        call_tool(TOOL, args)


def test_reconcile_rejects_excessive_row_work_before_projection(tmp_path: Path) -> None:
    path = tmp_path / "large.json"
    payload = json.dumps({"records": [{}] * 10001}).encode()
    path.write_bytes(payload)
    args = {
        "censuses": [
            {
                "name": "census",
                "path": str(path),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        ],
        "captures": [],
    }
    with pytest.raises(ValueError, match="inventory_row_limit_exceeded"):
        call_tool(TOOL, args)


def test_reconcile_rejects_excessive_request_matching_work(tmp_path: Path) -> None:
    def pin(name: str, document: dict[str, object]) -> dict[str, str]:
        path = tmp_path / name
        payload = json.dumps(document).encode()
        path.write_bytes(payload)
        return {
            "name": name,
            "path": str(path),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }

    args = {
        "censuses": [pin("census", {"records": []})],
        "captures": [
            {
                "manifest": pin("manifest", {"results": [{}] * 2000}),
                "request": pin("request", {"records": [{}] * 3000}),
            }
        ],
    }
    with pytest.raises(ValueError, match="inventory_request_work_limit_exceeded"):
        call_tool(TOOL, args)
