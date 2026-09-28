"""Read-only verification for the exact Context Gold output package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from archive_govt_nz.cli import app
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
