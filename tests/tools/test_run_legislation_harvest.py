"""Tests for weekly legislation harvest orchestration and workflow state management."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = Path(__file__).parents[2] / "tools" / "run_legislation_harvest.py"
_SPEC = importlib.util.spec_from_file_location("run_legislation_harvest", _TOOL_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

validate_source_set_config = _MODULE.validate_source_set_config
check_credentials_presence = _MODULE.check_credentials_presence
sync_legislation_records = _MODULE.sync_legislation_records
run_harvest = _MODULE.run_harvest
main = _MODULE.main


def test_validate_source_set_config(tmp_path: Path) -> None:
    """Verify source-set configuration validation for valid and invalid inputs."""
    valid_cfg = tmp_path / "valid.yml"
    valid_cfg.write_text(
        "name: legislation\nenabled: true\nschedule: '23 18 * * 0'\n",
        encoding="utf-8",
    )
    res = validate_source_set_config(valid_cfg)
    assert res["name"] == "legislation"
    assert res["enabled"] is True

    # Missing file
    with pytest.raises(FileNotFoundError, match="not found"):
        validate_source_set_config(tmp_path / "missing.yml")

    # Invalid name
    invalid_name = tmp_path / "invalid_name.yml"
    invalid_name.write_text("name: other\nenabled: true\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Expected source-set name 'legislation'"):
        validate_source_set_config(invalid_name)

    # Disabled config
    disabled = tmp_path / "disabled.yml"
    disabled.write_text("name: legislation\nenabled: false\n", encoding="utf-8")
    with pytest.raises(ValueError, match="disabled"):
        validate_source_set_config(disabled)


def test_check_credentials_presence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify safe credential audit without leaking values."""
    monkeypatch.setenv("HF_TOKEN", "secret-token")
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)
    monkeypatch.delenv("LEGISLATION_API_KEY", raising=False)

    creds = check_credentials_presence()
    assert creds["HF_TOKEN"] is True
    assert creds["ZENODO_TOKEN"] is False
    assert creds["LEGISLATION_API_KEY"] is False


def test_run_harvest_no_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify harvest returns no_change when 0 works are synced."""
    config_file = tmp_path / "legislation.yml"
    config_file.write_text("name: legislation\nenabled: true\n", encoding="utf-8")

    checkpoint_file = tmp_path / "checkpoint.json"
    checkpoint_file.write_text(
        json.dumps({"processed_work_ids": ["w1"]}), encoding="utf-8"
    )
    candidate_chk = tmp_path / "candidate_chk.json"
    manifest_file = tmp_path / "manifest.json"
    receipt_file = tmp_path / "receipt.json"
    cas_path = tmp_path / "cas"

    monkeypatch.setattr(
        _MODULE,
        "sync_legislation_records",
        lambda *_, **__: {
            "works_synced": 0,
            "errors": [],
            "processed_ids": [],
        },
    )

    code = run_harvest(
        config_path=config_file,
        checkpoint_path=checkpoint_file,
        candidate_checkpoint_path=candidate_chk,
        manifest_path=manifest_file,
        receipt_path=receipt_file,
        cas_path=cas_path,
    )
    assert code == 0
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt["outcome"] == "no_change"
    assert receipt["new_works_synced"] == 0


def test_run_harvest_changed_and_promoted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify harvest promotes checkpoint on successful new works sync."""
    config_file = tmp_path / "legislation.yml"
    config_file.write_text("name: legislation\nenabled: true\n", encoding="utf-8")

    checkpoint_file = tmp_path / "checkpoint.json"
    checkpoint_file.write_text(json.dumps({"processed_work_ids": []}), encoding="utf-8")
    candidate_chk = tmp_path / "candidate_chk.json"
    manifest_file = tmp_path / "manifest.json"
    receipt_file = tmp_path / "receipt.json"
    cas_path = tmp_path / "cas"

    monkeypatch.setattr(
        _MODULE,
        "sync_legislation_records",
        lambda *_, **__: {
            "works_synced": 3,
            "errors": [],
            "processed_ids": ["w1", "w2", "w3"],
        },
    )

    code = run_harvest(
        config_path=config_file,
        checkpoint_path=checkpoint_file,
        candidate_checkpoint_path=candidate_chk,
        manifest_path=manifest_file,
        receipt_path=receipt_file,
        cas_path=cas_path,
        backfill_limit=10,
        promote=True,
    )
    assert code == 0
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt["outcome"] == "changed"
    assert receipt["new_works_synced"] == 3
    assert receipt["promoted"] is True

    promoted_chk = json.loads(checkpoint_file.read_text(encoding="utf-8"))
    assert len(promoted_chk["processed_work_ids"]) == 3


def test_run_harvest_partial_retryable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify harvest classifies partial successes with errors as partial_retryable."""
    config_file = tmp_path / "legislation.yml"
    config_file.write_text("name: legislation\nenabled: true\n", encoding="utf-8")

    checkpoint_file = tmp_path / "checkpoint.json"
    candidate_chk = tmp_path / "candidate_chk.json"
    manifest_file = tmp_path / "manifest.json"
    receipt_file = tmp_path / "receipt.json"
    cas_path = tmp_path / "cas"

    monkeypatch.setattr(
        _MODULE,
        "sync_legislation_records",
        lambda *_, **__: {
            "works_synced": 1,
            "errors": ["Transient 503 from upstream API on w2"],
            "processed_ids": ["w1"],
        },
    )

    code = run_harvest(
        config_path=config_file,
        checkpoint_path=checkpoint_file,
        candidate_checkpoint_path=candidate_chk,
        manifest_path=manifest_file,
        receipt_path=receipt_file,
        cas_path=cas_path,
    )
    assert code == 0
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt["outcome"] == "partial_retryable"
    assert len(receipt["errors"]) == 1


def test_run_harvest_failed_sync(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify harvest returns exit code 1 on fatal sync exception."""
    config_file = tmp_path / "legislation.yml"
    config_file.write_text("name: legislation\nenabled: true\n", encoding="utf-8")

    checkpoint_file = tmp_path / "checkpoint.json"
    candidate_chk = tmp_path / "candidate_chk.json"
    manifest_file = tmp_path / "manifest.json"
    receipt_file = tmp_path / "receipt.json"
    cas_path = tmp_path / "cas"

    def _failing_sync(*_args: object, **_kwargs: object) -> dict[str, object]:
        msg = "Fatal disk write error"
        raise OSError(msg)

    monkeypatch.setattr(_MODULE, "sync_legislation_records", _failing_sync)

    code = run_harvest(
        config_path=config_file,
        checkpoint_path=checkpoint_file,
        candidate_checkpoint_path=candidate_chk,
        manifest_path=manifest_file,
        receipt_path=receipt_file,
        cas_path=cas_path,
    )
    assert code == 1
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt["outcome"] == "failed"


def test_run_harvest_validation_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify harvest fails when manifest contains invalid schema records."""
    config_file = tmp_path / "legislation.yml"
    config_file.write_text("name: legislation\nenabled: true\n", encoding="utf-8")

    checkpoint_file = tmp_path / "checkpoint.json"
    candidate_chk = tmp_path / "candidate_chk.json"
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "document_id": "",
                        "work_id": "",
                        "title": "",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    receipt_file = tmp_path / "receipt.json"
    cas_path = tmp_path / "cas"

    monkeypatch.setattr(
        _MODULE,
        "sync_legislation_records",
        lambda *_, **__: {
            "works_synced": 1,
            "errors": [],
            "processed_ids": ["w1"],
        },
    )

    code = run_harvest(
        config_path=config_file,
        checkpoint_path=checkpoint_file,
        candidate_checkpoint_path=candidate_chk,
        manifest_path=manifest_file,
        receipt_path=receipt_file,
        cas_path=cas_path,
    )
    assert code == 1
    receipt = json.loads(receipt_file.read_text(encoding="utf-8"))
    assert receipt["outcome"] == "failed"
    assert receipt["validation_findings_count"] > 0


def test_run_harvest_invalid_config(tmp_path: Path) -> None:
    """Verify harvest fails cleanly when configuration path is invalid."""
    code = run_harvest(
        config_path=tmp_path / "non_existent.yml",
        checkpoint_path=tmp_path / "chk.json",
        candidate_checkpoint_path=tmp_path / "cand.json",
        manifest_path=tmp_path / "man.json",
        receipt_path=tmp_path / "rec.json",
        cas_path=tmp_path / "cas",
    )
    assert code == 1


def test_main_cli_execution(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify main entrypoint handles CLI arguments and exits with code."""
    config_file = tmp_path / "legislation.yml"
    config_file.write_text("name: legislation\nenabled: true\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_legislation_harvest.py",
            "--source-set-config",
            str(config_file),
            "--checkpoint-path",
            str(tmp_path / "chk.json"),
            "--candidate-checkpoint-path",
            str(tmp_path / "cand_chk.json"),
            "--manifest-path",
            str(tmp_path / "man.json"),
            "--receipt-path",
            str(tmp_path / "rec.json"),
            "--cas-path",
            str(tmp_path / "cas"),
            "--backfill-limit",
            "5",
        ],
    )

    monkeypatch.setattr(
        _MODULE,
        "sync_legislation_records",
        lambda *_, **__: {
            "works_synced": 0,
            "errors": [],
            "processed_ids": [],
        },
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
