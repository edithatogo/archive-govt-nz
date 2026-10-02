"""Fixity verification and read-only operational surface for canonical Gold."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import canonical_gold_verification
from archive_govt_nz.domains.health_appropriations.canonical_gold_verification import (
    verify_canonical_gold_package,
)
from archive_govt_nz.mcp_server import PROTOCOL_VERSION, Server, call_tool, list_tools


def _package(root: Path) -> tuple[Path, str]:
    root.mkdir()
    payload = b"verified-output-payload"
    output = root / "observations.parquet"
    output.write_bytes(payload)
    revision_report = {
        "schema_version": "archive-govt-nz.health-revision-reconciliation/v1",
        "scope": "same_recordset_measure_source_label_and_exact_context_period_across_observed_vintages",
        "key_fields": [
            "recordset",
            "measure",
            "source_label",
            "unit",
            "currency",
            "price_basis",
            "base_period",
            "denominator_definition",
            "institutional_coverage",
            "accounting_basis",
            "period_token",
        ],
        "completeness": "historical_product_rows_only",
        "difference_interpretation": "not_assessed",
        "other_product_revisions": "not_assessed",
        "cross_source_comparison": "not_performed",
        "candidates": [],
    }
    revision_payload = (
        json.dumps(revision_report, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode()
    revision_output = root / "historical_revision_reconciliation.json"
    revision_output.write_bytes(revision_payload)
    manifest = {
        "schema_version": "archive-govt-nz.health-canonical-gold/v2",
        "outputs": {
            output.name: {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "bytes": len(payload),
                "rows": 1,
            },
            revision_output.name: {
                "sha256": hashlib.sha256(revision_payload).hexdigest(),
                "bytes": len(revision_payload),
                "kind": "report",
            },
        },
        "products": {"historical": {"input_records": 1}},
        "temporal_coverage_report": {
            "schema_version": "archive-govt-nz.health-temporal-coverage/v1",
            "groups": [{"observed_periods": []}],
        },
        "classification_drift_report": {
            "schema_version": "archive-govt-nz.health-classification-drift/v1",
            "mapping": "not_inferred",
            "candidates": [],
        },
        "revision_reconciliation_report": revision_report,
        "rights_state": "not_evaluated",
        "publication": "not_performed",
    }
    marker = root / "MANIFEST.json"
    marker.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return root, hashlib.sha256(marker.read_bytes()).hexdigest()


def _ready_server() -> Server:
    server = Server()
    response = server.handle_request(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "gold-verification-test", "version": "1"},
            },
        }
    )
    assert response is not None
    assert "result" in response
    assert (
        server.handle_request({"jsonrpc": "2.0", "method": "notifications/initialized"})
        is None
    )
    return server


def test_cli_mcp_parity_and_no_write(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, pin = _package(tmp_path / "gold")
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    receipt = verify_canonical_gold_package(root, pin)
    result = app(
        [
            "health-appropriations-verify-canonical-gold",
            str(root),
            pin,
        ],
        exit_on_error=False,
        result_action="return_value",
    )
    cli_receipt = json.loads(capsys.readouterr().out)
    assert result == 0
    assert cli_receipt.pop("command") == "health-appropriations-verify-canonical-gold"
    assert cli_receipt == receipt
    assert receipt["status"] == "verified"
    assert receipt["output_count"] == 2
    assert receipt["output_bytes"] == sum(
        (root / name).stat().st_size
        for name in ("observations.parquet", "historical_revision_reconciliation.json")
    )
    assert receipt["products"] == ["historical"]
    assert receipt["temporal_coverage_groups"] == 1
    assert receipt["verification_scope"] == "manifest_declared_output_fixity"
    assert receipt["rights_state"] == "not_evaluated"
    assert receipt["publication"] == "not_performed"

    arguments = {"package_dir": str(root), "manifest_sha256": pin}
    assert (
        call_tool("health_appropriations_verify_canonical_gold", arguments) == receipt
    )
    tool = _ready_server().handle_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "health_appropriations_verify_canonical_gold",
                "arguments": arguments,
            },
        }
    )
    assert tool is not None
    assert "error" not in tool
    assert json.loads(tool["result"]["content"][0]["text"]) == receipt
    assert tool["result"]["isError"] is False
    assert {path.name: path.read_bytes() for path in root.iterdir()} == before
    definition = next(
        item
        for item in list_tools()
        if item["name"] == "health_appropriations_verify_canonical_gold"
    )
    assert definition["annotations"] == {
        "title": "Verify canonical Health Gold package",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }


@pytest.mark.parametrize(
    "failure",
    [
        "wrong_pin",
        "tampered_output",
        "tampered_output_size",
        "missing_output",
        "extra_output",
        "unsafe_name",
        "invalid_manifest_schema",
        "invalid_reports",
        "invalid_classification_report",
    ],
)
def test_invalid_package_fails_closed_and_redacted(
    tmp_path: Path, failure: str
) -> None:
    root, pin = _package(tmp_path / "gold")
    if failure == "wrong_pin":
        pin = "0" * 64
    elif failure == "tampered_output":
        (root / "observations.parquet").write_bytes(
            b"x" * len(b"verified-output-payload")
        )
    elif failure == "tampered_output_size":
        (root / "observations.parquet").write_bytes(b"short")
    elif failure == "missing_output":
        (root / "observations.parquet").unlink()
    elif failure == "extra_output":
        (root / "unlisted.txt").write_text("unlisted", encoding="utf-8")
    elif failure == "unsafe_name":
        manifest_path = root / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["outputs"]["../escape"] = manifest["outputs"].pop(
            "observations.parquet"
        )
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        pin = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    elif failure in {
        "invalid_manifest_schema",
        "invalid_reports",
        "invalid_classification_report",
    }:
        manifest_path = root / "MANIFEST.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if failure == "invalid_manifest_schema":
            manifest["schema_version"] = "unsupported/v1"
        elif failure == "invalid_reports":
            manifest["temporal_coverage_report"] = []
        else:
            manifest["classification_drift_report"] = []
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        pin = hashlib.sha256(manifest_path.read_bytes()).hexdigest()

    receipt = verify_canonical_gold_package(root, pin)

    assert receipt["status"] == "failed"
    assert receipt["error"] == "invalid_canonical_gold_package"
    assert str(root) not in json.dumps(receipt)
    assert "verified-output-payload" not in json.dumps(receipt)

    response = _ready_server().handle_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "health_appropriations_verify_canonical_gold",
                "arguments": {"package_dir": str(root), "manifest_sha256": pin},
            },
        }
    )
    assert response is not None
    assert response["result"]["isError"] is True
    assert json.loads(response["result"]["content"][0]["text"]) == receipt


def test_invalid_revision_report_fails_closed(tmp_path: Path) -> None:
    root, _pin = _package(tmp_path / "gold")
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    manifest["revision_reconciliation_report"] = []
    marker.write_text(json.dumps(manifest), encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()

    receipt = verify_canonical_gold_package(root, pin)

    assert receipt["status"] == "failed"
    assert receipt["error"] == "invalid_canonical_gold_package"


def test_duplicate_manifest_keys_fail_closed(tmp_path: Path) -> None:
    root, _pin = _package(tmp_path / "gold")
    marker = root / "MANIFEST.json"
    marker.write_text('{"schema_version":"x","schema_version":"y"}', encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()

    assert verify_canonical_gold_package(root, pin)["status"] == "failed"


@pytest.mark.parametrize(
    "manifest_change",
    ["invalid_json_shape", "invalid_outputs", "invalid_output_metadata", "bad_digest"],
)
def test_malformed_manifest_contracts_fail_closed(
    tmp_path: Path, manifest_change: str
) -> None:
    root, _pin = _package(tmp_path / "gold")
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    if manifest_change == "invalid_json_shape":
        marker.write_text("[]", encoding="utf-8")
    else:
        if manifest_change == "invalid_outputs":
            manifest["outputs"] = []
        elif manifest_change == "invalid_output_metadata":
            manifest["outputs"]["observations.parquet"] = []
        elif manifest_change == "bad_digest":
            manifest["outputs"]["observations.parquet"]["sha256"] = "invalid"
        marker.write_text(json.dumps(manifest), encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()

    assert verify_canonical_gold_package(root, pin)["status"] == "failed"


def test_output_byte_limit_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _pin = _package(tmp_path / "gold")
    extra_payload = b"x"
    extra = root / "extra.bin"
    extra.write_bytes(extra_payload)
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text(encoding="utf-8"))
    manifest["outputs"][extra.name] = {
        "sha256": hashlib.sha256(extra_payload).hexdigest(),
        "bytes": len(extra_payload),
    }
    marker.write_text(json.dumps(manifest), encoding="utf-8")
    pin = hashlib.sha256(marker.read_bytes()).hexdigest()
    monkeypatch.setattr(
        canonical_gold_verification,
        "MAX_PACKAGE_BYTES",
        len(b"verified-output-payload"),
    )

    assert verify_canonical_gold_package(root, pin)["status"] == "failed"


def test_manifest_size_limit_and_invalid_root_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, pin = _package(tmp_path / "gold")
    monkeypatch.setattr(canonical_gold_verification, "MAX_MANIFEST_BYTES", 1)

    assert verify_canonical_gold_package(root, pin)["status"] == "failed"
    assert (
        verify_canonical_gold_package(tmp_path / "missing", pin)["status"] == "failed"
    )


def test_missing_manifest_fails_closed(tmp_path: Path) -> None:
    root, pin = _package(tmp_path / "gold")
    (root / "MANIFEST.json").unlink()

    assert verify_canonical_gold_package(root, pin)["status"] == "failed"
