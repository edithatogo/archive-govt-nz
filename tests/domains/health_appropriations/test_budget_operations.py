"""Read-only compact Budget package receipts and matching CLI/MCP boundaries."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError
from openpyxl import Workbook

from archive_govt_nz.cli import app, health_appropriations_verify_budget
from archive_govt_nz.domains.health_appropriations import budget_operations
from archive_govt_nz.domains.health_appropriations.budget import (
    normalize_budget_workbook,
)
from archive_govt_nz.mcp_server import Server, call_tool, list_tools


@pytest.fixture
def package(tmp_path: Path) -> tuple[Path, str]:
    book = Workbook()
    sheet = book.active
    assert sheet is not None
    sheet.title = "Raw Data"
    sheet.append(
        [
            "Vote",
            "Year",
            "Department",
            "Appropriation Name",
            "Functional Classification",
            "Amount $000",
            "Amount Type",
            "Portfolio Name",
        ]
    )
    sheet.append(["Health", 2026, "Health", "Care", "Health", -1, "Actuals", "Health"])
    sheet.append(
        ["Education", 2026, "Education", "Care", "Education", 0, "Actuals", "Education"]
    )
    source = tmp_path / "synthetic.xlsx"
    book.save(source)
    book.close()
    root = tmp_path / "package"
    normalize_budget_workbook(
        source,
        root,
        expected_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
        observed_at="2026-08-31T00:00:00Z",
        source_vintage="Budget-2026",
        source_locator="synthetic.xlsx",
    )
    return root, hashlib.sha256((root / "MANIFEST.json").read_bytes()).hexdigest()


def test_receipt_and_cli_mcp_parity(
    package: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, pin = package
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    receipt = budget_operations.verify_budget_package(root, pin)
    assert receipt["status"] == "passed"
    assert receipt["manifest_sha256"] == pin
    assert receipt["counts"] == {"facts": 1, "field_lineage": 8, "dispositions": 2}
    assert receipt["disposition_counts"] == {
        "input": 2,
        "normalized": 1,
        "out_of_scope": 1,
        "blank": 0,
        "rejected": 0,
    }
    assert receipt["source_vintage"] == "Budget-2026"
    assert receipt["rights_state"] == "not_evaluated"
    assert receipt["verification_scope"] == "reviewed_package_only"
    assert receipt["publication_state"] == "local_validation_only"
    assert "raw_values_json" not in json.dumps(receipt)
    assert health_appropriations_verify_budget(root, pin) == 0
    envelope = json.loads(capsys.readouterr().out)
    assert envelope.pop("command") == "health-appropriations-verify-budget"
    assert (
        envelope
        == receipt
        == call_tool(
            "health_appropriations_verify_budget",
            {"package_dir": str(root), "manifest_sha256": pin},
        )
    )
    assert {path.name: path.read_bytes() for path in root.iterdir()} == before
    definition = next(
        t for t in list_tools() if t["name"] == "health_appropriations_verify_budget"
    )
    assert definition["annotations"] == {
        "title": "Verify standalone Budget package",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
    Draft202012Validator(definition["outputSchema"]).validate(receipt)


@pytest.mark.parametrize("change", ["missing", "wrong_pin", "tampered", "partial"])
def test_failure_parity_and_no_creation(
    package: tuple[Path, str], change: str, capsys: pytest.CaptureFixture[str]
) -> None:
    root, pin = package
    if change == "missing":
        root = root.parent / "missing-private-name"
    elif change == "wrong_pin":
        pin = "0" * 64
    elif change == "tampered":
        (root / "budget_facts.parquet").write_bytes(b"private-source-payload")
    else:
        (root / "MANIFEST.json").unlink()
    before = {str(p): p.read_bytes() for p in root.parent.rglob("*") if p.is_file()}
    expected = budget_operations.verify_budget_package(root, pin)
    assert expected == {
        "schema_version": "archive-govt-nz.health-budget-verification/v1",
        "status": "failed",
        "error": "invalid_budget_package",
        "verification_scope": "reviewed_package_only",
        "rights_state": "not_evaluated",
        "publication_state": "local_validation_only",
    }
    assert health_appropriations_verify_budget(root, pin) == 2
    envelope = json.loads(capsys.readouterr().out)
    envelope.pop("command")
    assert (
        envelope
        == expected
        == call_tool(
            "health_appropriations_verify_budget",
            {"package_dir": str(root), "manifest_sha256": pin},
        )
    )
    assert {
        str(p): p.read_bytes() for p in root.parent.rglob("*") if p.is_file()
    } == before


def test_malformed_pin_is_redacted(tmp_path: Path) -> None:
    receipt = budget_operations.verify_budget_package(
        tmp_path / "absent", "private-pin"
    )
    assert receipt["status"] == "failed"
    assert "private-pin" not in json.dumps(receipt)
    assert not (tmp_path / "absent").exists()


@pytest.mark.parametrize("length", [0, 1, 2048, 2049])
def test_receipt_context_bound(
    package: tuple[Path, str], monkeypatch: pytest.MonkeyPatch, length: int
) -> None:
    root, pin = package
    tables = budget_operations.read_verified_budget(root, pin)
    tables[3]["source_vintage"] = "v" * length
    monkeypatch.setattr(budget_operations, "read_verified_budget", lambda *_: tables)
    result = budget_operations.verify_budget_package(root, pin)
    assert result["status"] == ("passed" if 1 <= length <= 2048 else "failed")


def test_unexpected_failure_never_discloses_diagnostics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*_: object) -> None:
        message = "private-source signed-url token"
        raise RuntimeError(message)

    monkeypatch.setattr(budget_operations, "read_verified_budget", fail)
    result = budget_operations.verify_budget_package(tmp_path, "a" * 64)
    assert result["error"] == "invalid_budget_package"
    assert "private" not in json.dumps(result)


def test_cli_argument_dispatch(
    package: tuple[Path, str], capsys: pytest.CaptureFixture[str]
) -> None:
    root, pin = package
    with pytest.raises(SystemExit) as exit_info:
        app(
            [
                "health-appropriations-verify-budget",
                "--package-dir",
                str(root),
                "--manifest-sha256",
                pin,
            ]
        )
    assert exit_info.value.code == 0
    assert json.loads(capsys.readouterr().out)["manifest_sha256"] == pin


@pytest.mark.parametrize("passed", [True, False])
def test_protocol_failure_flag_preserves_receipt(
    package: tuple[Path, str], passed: bool  # noqa: FBT001
) -> None:
    root, pin = package
    if not passed:
        pin = "0" * 64
    response = Server()._call_tool(  # noqa: SLF001
        1,
        {
            "name": "health_appropriations_verify_budget",
            "arguments": {"package_dir": str(root), "manifest_sha256": pin},
        },
    )
    result = response["result"]
    assert result["isError"] is not passed
    assert result["structuredContent"] == budget_operations.verify_budget_package(
        root, pin
    )
    assert json.loads(result["content"][0]["text"]) == result["structuredContent"]


def test_published_schema_matches_mcp_and_rejects_overclaims(
    package: tuple[Path, str],
) -> None:
    root, pin = package
    schema = json.loads(
        (
            Path(__file__).parents[3]
            / "schemas/health-budget-verification-v1.schema.json"
        ).read_text()
    )
    assert schema == budget_operations.BUDGET_VERIFICATION_SCHEMA
    validator = Draft202012Validator(schema)
    receipt = budget_operations.verify_budget_package(root, pin)
    validator.validate(receipt)
    for key, value in [
        ("rights_state", "eligible"),
        ("status", "ready"),
        ("error", "private"),
    ]:
        with pytest.raises(ValidationError):
            validator.validate({**receipt, key: value})
    with pytest.raises(ValidationError):
        validator.validate({**receipt, "counts": {**receipt["counts"], "facts": True}})
    failed = budget_operations.verify_budget_package(root, "0" * 64)
    validator.validate(failed)
    with pytest.raises(ValidationError):
        validator.validate({**failed, "source_locator": "unverified-private"})
