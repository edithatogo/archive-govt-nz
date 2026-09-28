"""Read-only verification for the exact Context Gold output package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import context_gold_verification
from archive_govt_nz.domains.health_appropriations.context_gold_verification import (
    verify_context_gold_package,
)
from archive_govt_nz.mcp_server import call_tool


def _package(root: Path) -> tuple[Path, str]:
    root.mkdir()
    products = {}
    for name in (
        "context_observations.parquet",
        "context_coverage.parquet",
        "context_quality.parquet",
        "context-quality-report.md",
    ):
        payload = ("fixture:" + name).encode()
        (root / name).write_bytes(payload)
        products[name] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
            "rows": 1,
        }
    manifest = {
        "schema_version": "archive-govt-nz.health-context-gold/v1",
        "products": products,
        "plot_report": {
            "schema_version": "archive-govt-nz.health-context-gold-plots/v1",
            "status": "complete",
            "period_axis": "discrete_source_tokens_no_continuity_inference",
            "numeric_conversion": "float_for_display_only",
            "excluded_observations_plotted": False,
            "series": [],
        },
        "source_marker_sha256": ["a" * 64] * 4,
        "rights_state": "not_evaluated",
        "denominator_selection": "not_performed",
        "publication": "not_performed",
    }
    marker = root / "MANIFEST.json"
    marker.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    )
    return root, hashlib.sha256(marker.read_bytes()).hexdigest()


def _rewrite_manifest(root: Path, manifest: dict[str, object]) -> str:
    marker = root / "MANIFEST.json"
    marker.write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
    )
    return hashlib.sha256(marker.read_bytes()).hexdigest()


def test_context_gold_cli_mcp_parity_and_read_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    root, pin = _package(tmp_path / "context")
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    receipt = verify_context_gold_package(root, pin)
    result = app(
        ["health-appropriations-verify-context-gold", str(root), pin],
        exit_on_error=False,
        result_action="return_value",
    )
    cli_receipt = json.loads(capsys.readouterr().out)
    assert result == 0
    assert cli_receipt.pop("command") == "health-appropriations-verify-context-gold"
    assert cli_receipt == receipt
    assert (
        call_tool(
            "health_appropriations_verify_context_gold",
            {"package_dir": str(root), "manifest_sha256": pin},
        )
        == receipt
    )
    assert {path.name: path.read_bytes() for path in root.iterdir()} == before
    assert receipt["status"] == "verified"
    assert receipt["quality_report"] == "verified_as_declared_output"
    assert receipt["plot_report"] == "verified_as_declared_output"
    assert receipt["plot_count"] == 0
    assert receipt["rights_state"] == "not_evaluated"


@pytest.mark.parametrize("fault", ["payload", "extra", "manifest"])
def test_context_gold_verifier_fails_closed_without_writes(
    tmp_path: Path, fault: str
) -> None:
    root, pin = _package(tmp_path / "context")
    if fault == "payload":
        (root / "context_quality.parquet").write_bytes(b"tampered")
    elif fault == "extra":
        (root / "unexpected.txt").write_text("extra")
    else:
        (root / "MANIFEST.json").write_text("{}")
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    receipt = verify_context_gold_package(root, pin)
    assert receipt["status"] == "failed"
    assert not (root / "FAILURE.json").exists()
    assert {path.name: path.read_bytes() for path in root.iterdir()} == before


@pytest.mark.parametrize(
    "fault",
    ["schema", "boundary", "products", "marker-count", "marker-digest", "plots"],
)
def test_context_gold_verifier_rejects_manifest_contract_drift(
    tmp_path: Path, fault: str
) -> None:
    root, _pin = _package(tmp_path / "context")
    marker = root / "MANIFEST.json"
    manifest = json.loads(marker.read_text())
    if fault == "schema":
        manifest["schema_version"] = "wrong"
    elif fault == "boundary":
        manifest["rights_state"] = "approved"
    elif fault == "products":
        del manifest["products"]["context_quality.parquet"]
    elif fault == "marker-count":
        manifest["source_marker_sha256"] = ["a" * 64]
    elif fault == "plots":
        manifest["plot_report"]["period_axis"] = "continuous_time"
    else:
        manifest["source_marker_sha256"][0] = "invalid"
    pin = _rewrite_manifest(root, manifest)
    assert verify_context_gold_package(root, pin)["status"] == "failed"


@pytest.mark.parametrize(
    "fault",
    [
        "entry-type",
        "digest-shape",
        "bool-size",
        "negative-rows",
        "size-mismatch",
        "payload-digest",
        "missing-output",
        "package-limit",
    ],
)
def test_context_gold_verifier_rejects_output_metadata_and_fixity(
    tmp_path: Path, fault: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _pin = _package(tmp_path / "context")
    manifest = json.loads((root / "MANIFEST.json").read_text())
    name = "context_quality.parquet"
    entry = manifest["products"][name]
    if fault == "entry-type":
        manifest["products"][name] = []
    elif fault == "digest-shape":
        entry["sha256"] = "bad"
    elif fault == "bool-size":
        entry["bytes"] = True
    elif fault == "negative-rows":
        entry["rows"] = -1
    elif fault == "size-mismatch":
        entry["bytes"] += 1
    elif fault == "payload-digest":
        path = root / name
        path.write_bytes(b"x" * len(path.read_bytes()))
    elif fault == "missing-output":
        (root / name).unlink()
    else:
        monkeypatch.setattr(context_gold_verification, "MAX_PACKAGE_BYTES", 50)
    pin = _rewrite_manifest(root, manifest)
    assert verify_context_gold_package(root, pin)["status"] == "failed"


def test_context_gold_verifier_rejects_bad_root_and_duplicate_manifest_key(
    tmp_path: Path,
) -> None:
    root, pin = _package(tmp_path / "context")
    assert verify_context_gold_package(root, "bad")["status"] == "failed"
    assert verify_context_gold_package(tmp_path / "missing", pin)["status"] == "failed"
    missing_manifest, missing_pin = _package(tmp_path / "without-manifest")
    (missing_manifest / "MANIFEST.json").unlink()
    assert (
        verify_context_gold_package(missing_manifest, missing_pin)["status"] == "failed"
    )
    marker = root / "MANIFEST.json"
    payload = marker.read_text()
    duplicate = payload.replace(
        '"schema_version":"archive-govt-nz.health-context-gold/v1",',
        '"schema_version":"archive-govt-nz.health-context-gold/v1",'
        '"schema_version":"archive-govt-nz.health-context-gold/v1",',
    )
    marker.write_text(duplicate)
    duplicate_pin = hashlib.sha256(marker.read_bytes()).hexdigest()
    assert verify_context_gold_package(root, duplicate_pin)["status"] == "failed"
