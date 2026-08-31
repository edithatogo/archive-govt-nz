"""The publication command separates metadata authority from raw decisions."""

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

SPEC = importlib.util.spec_from_file_location(
    "publish_foi_tool", Path(__file__).parents[1] / "tools/publish_foi.py"
)
assert SPEC is not None
assert SPEC.loader is not None
TOOL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(TOOL)


def test_catalogue_creation_and_receipt_are_explicit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Creating the named public catalogue does not grant raw publication authority."""
    hub = MagicMock()
    hub.writer.whoami.return_value = {"name": "edithatogo"}
    monkeypatch.setattr(TOOL, "HuggingFaceHub", lambda: hub)
    monkeypatch.setattr(
        TOOL, "publish_catalogue", lambda *_args: {"status": "fixture_verified"}
    )
    receipt = tmp_path / "receipt.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_foi",
            "catalogue",
            "--create-catalogue-repository",
            "--receipt",
            str(receipt),
        ],
    )
    assert TOOL.main() == 0
    hub.writer.create_repo.assert_called_once_with(
        TOOL.CATALOGUE_REPO, repo_type="dataset", private=False, exist_ok=True
    )
    assert json.loads(receipt.read_text())["status"] == "fixture_verified"
    with pytest.raises(SystemExit):
        TOOL.main()


def test_raw_command_requires_explicit_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Do not contact the Hub when the package decision is absent."""
    monkeypatch.setattr(
        sys, "argv", ["publish_foi", "raw", "--receipt", str(tmp_path / "receipt")]
    )
    with pytest.raises(SystemExit):
        TOOL.main()


def test_account_mismatch_and_private_exceptions_are_sanitized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Neither another account nor exception text becomes a successful receipt."""
    hub = MagicMock()
    hub.writer.whoami.return_value = {"name": "wrong"}
    monkeypatch.setattr(TOOL, "HuggingFaceHub", lambda: hub)
    monkeypatch.setattr(
        sys,
        "argv",
        ["publish_foi", "catalogue", "--receipt", str(tmp_path / "receipt")],
    )
    assert TOOL.main() == 1
    failure = json.loads(capsys.readouterr().out)
    assert failure["publication_verified"] is False
    assert failure["reason"] == "approved_operator_account_required"
    (tmp_path / "receipt").unlink()
    hub.writer.whoami.return_value = {"name": "edithatogo"}

    def failed(*_args: object) -> dict:
        message = "private diagnostic must not be printed"
        raise ValueError(message)

    monkeypatch.setattr(TOOL, "publish_catalogue", failed)
    assert TOOL.main() == 1
    output = capsys.readouterr().out
    assert "private diagnostic" not in output
    assert json.loads(output)["reason"] == "unclassified"


def test_raw_command_passes_exact_decision_to_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No raw repository is created implicitly by the command."""
    hub = MagicMock()
    hub.writer.whoami.return_value = {"name": "edithatogo"}
    monkeypatch.setattr(TOOL, "HuggingFaceHub", lambda: hub)
    decision = tmp_path / "decision.json"
    decision.write_text('{"fixture":true}')
    publish = MagicMock(return_value={"status": "fixture_verified"})
    monkeypatch.setattr(TOOL, "publish_raw_package", publish)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "publish_foi",
            "raw",
            "--package",
            str(tmp_path),
            "--decision",
            str(decision),
            "--manifest-sha256",
            "a" * 64,
            "--receipt",
            str(tmp_path / "receipt"),
        ],
    )
    assert TOOL.main() == 0
    assert publish.call_args.kwargs["decision"] == {"fixture": True}
    hub.writer.create_repo.assert_not_called()


def test_receipt_race_preserves_existing_bytes_and_reports_verified_remote_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A local receipt failure must not conceal a completed remote verification."""
    hub = MagicMock()
    hub.writer.whoami.return_value = {"name": "edithatogo"}
    monkeypatch.setattr(TOOL, "HuggingFaceHub", lambda: hub)
    receipt = tmp_path / "receipt"

    def publish(*_args: object) -> dict:
        receipt.write_text("concurrent receipt")
        return {"status": "verified", "repo_id": TOOL.CATALOGUE_REPO}

    monkeypatch.setattr(TOOL, "publish_catalogue", publish)
    monkeypatch.setattr(
        sys, "argv", ["publish_foi", "catalogue", "--receipt", str(receipt)]
    )
    assert TOOL.main() == 1
    result = json.loads(capsys.readouterr().out)
    assert result["publication_verified"] is True
    assert result["receipt_saved"] is False
    assert receipt.read_text() == "concurrent receipt"
