"""Tests for weekly gazette harvest orchestration and state management."""

from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.adapters.nz_gazette import NZGazetteAdapter
from archive_govt_nz.domains.gazette.service import GazetteArchiveService
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from types import ModuleType

_TOOL_PATH = Path(__file__).parents[2] / "tools" / "run_gazette_harvest.py"
_SPEC = importlib.util.spec_from_file_location("run_gazette_harvest", _TOOL_PATH)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

validate_source_set_config = _MODULE.validate_source_set_config
check_credentials_presence = _MODULE.check_credentials_presence
load_discovery_seed = _MODULE.load_discovery_seed
sync_gazette_notices = _MODULE.sync_gazette_notices
run_harvest = _MODULE.run_harvest
main = _MODULE.main


def test_validate_source_set_config(tmp_path: Path) -> None:
    """Verify source-set configuration validation for valid and invalid inputs."""
    valid_cfg = tmp_path / "valid.yml"
    valid_cfg.write_text(
        "name: nz-gazette\nenabled: true\nschedule: '0 4 * * 4'\n",
        encoding="utf-8",
    )
    res = validate_source_set_config(valid_cfg)
    assert res["name"] == "nz-gazette"
    assert res["enabled"] is True

    with pytest.raises(FileNotFoundError, match="not found"):
        validate_source_set_config(tmp_path / "missing.yml")

    invalid_name = tmp_path / "invalid_name.yml"
    invalid_name.write_text("name: other\nenabled: true\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Expected source-set name 'nz-gazette'"):
        validate_source_set_config(invalid_name)

    disabled = tmp_path / "disabled.yml"
    disabled.write_text("name: nz-gazette\nenabled: false\n", encoding="utf-8")
    with pytest.raises(ValueError, match="disabled"):
        validate_source_set_config(disabled)


def test_check_credentials_presence(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify safe credential audit without leaking values."""
    monkeypatch.setenv("HF_TOKEN", "secret-token")
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)
    creds = check_credentials_presence()
    assert creds["HF_TOKEN"] is True
    assert creds["ZENODO_TOKEN"] is False


def test_load_discovery_seed(tmp_path: Path) -> None:
    """Verify discovery seed loading and fail-closed validation."""
    assert load_discovery_seed(None) == []

    bad = tmp_path / "bad.json"
    bad.write_text('{"not": "a list"}', encoding="utf-8")
    with pytest.raises(TypeError, match="JSON array"):
        load_discovery_seed(bad)

    good = tmp_path / "good.json"
    good.write_text('[{"notice_id": "2026-001"}]', encoding="utf-8")
    assert load_discovery_seed(good) == [{"notice_id": "2026-001"}]


def test_run_harvest_no_change(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify harvest returns no_change when 0 notices are synced."""
    config_file = tmp_path / "nz-gazette.yml"
    config_file.write_text("name: nz-gazette\nenabled: true\n", encoding="utf-8")

    checkpoint_file = tmp_path / "checkpoint.json"
    checkpoint_file.write_text(
        json.dumps({"processed_notice_ids": ["2026-000"]}), encoding="utf-8"
    )

    monkeypatch.setattr(
        _MODULE,
        "sync_gazette_notices",
        lambda *_, **__: {
            "notices_synced": 0,
            "records": [],
            "errors": [],
            "processed_ids": [],
            "discovery": {},
        },
    )

    code = run_harvest(
        config_path=config_file,
        checkpoint_path=checkpoint_file,
        candidate_checkpoint_path=tmp_path / "cand.json",
        manifest_path=tmp_path / "man.json",
        receipt_path=tmp_path / "rec.json",
        cas_path=tmp_path / "cas",
    )
    assert code == 0
    receipt = json.loads((tmp_path / "rec.json").read_text(encoding="utf-8"))
    assert receipt["outcome"] == "no_change"
    assert receipt["promoted"] is True


def test_run_harvest_changed_promotes_checkpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify changed outcome syncs, validates and promotes checkpoint."""
    config_file = tmp_path / "nz-gazette.yml"
    config_file.write_text("name: nz-gazette\nenabled: true\n", encoding="utf-8")
    checkpoint_file = tmp_path / "checkpoint.json"

    record = {
        "schema_version": "archive-govt-nz.gazette/v1",
        "notice_id": "2026-001",
        "issue_number": "42",
        "year": 2026,
        "title": "T",
        "publication_date": "2026-08-22T00:00:00Z",
        "category": "General",
        "canonical_uri": "https://gazette.govt.nz/notice/id/2026-001",
        "raw_cas_hash_sha256": "a" * 64,
        "retrieval_timestamp": "2026-08-22T01:00:00Z",
        "content_text": "",
    }
    monkeypatch.setattr(
        _MODULE,
        "sync_gazette_notices",
        lambda *_, **__: {
            "notices_synced": 1,
            "records": [record],
            "errors": [],
            "processed_ids": ["2026-001"],
            "discovery": {},
        },
    )

    code = run_harvest(
        config_path=config_file,
        checkpoint_path=checkpoint_file,
        candidate_checkpoint_path=tmp_path / "cand.json",
        manifest_path=tmp_path / "man.json",
        receipt_path=tmp_path / "rec.json",
        cas_path=tmp_path / "cas",
    )
    assert code == 0
    receipt = json.loads((tmp_path / "rec.json").read_text(encoding="utf-8"))
    assert receipt["outcome"] == "changed"
    chk = json.loads(checkpoint_file.read_text(encoding="utf-8"))
    assert chk["schema_version"] == "archive-govt-nz.gazette-checkpoint/v1"
    assert chk["processed_notice_ids"] == ["2026-001"]


def test_run_harvest_sync_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify harvest fails when sync raises."""
    config_file = tmp_path / "nz-gazette.yml"
    config_file.write_text("name: nz-gazette\nenabled: true\n", encoding="utf-8")

    def boom(*_: object, **__: object) -> dict[str, object]:
        msg = "network down"
        raise RuntimeError(msg)

    monkeypatch.setattr(_MODULE, "sync_gazette_notices", boom)

    code = run_harvest(
        config_path=config_file,
        checkpoint_path=tmp_path / "chk.json",
        candidate_checkpoint_path=tmp_path / "cand.json",
        manifest_path=tmp_path / "man.json",
        receipt_path=tmp_path / "rec.json",
        cas_path=tmp_path / "cas",
    )
    assert code == 1
    receipt = json.loads((tmp_path / "rec.json").read_text(encoding="utf-8"))
    assert receipt["outcome"] == "failed"


def test_run_harvest_validation_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify harvest fails when manifest contains invalid records."""
    config_file = tmp_path / "nz-gazette.yml"
    config_file.write_text("name: nz-gazette\nenabled: true\n", encoding="utf-8")

    monkeypatch.setattr(
        _MODULE,
        "sync_gazette_notices",
        lambda *_, **__: {
            "notices_synced": 1,
            "records": [{"notice_id": "", "title": ""}],
            "errors": [],
            "processed_ids": ["x"],
            "discovery": {},
        },
    )

    code = run_harvest(
        config_path=config_file,
        checkpoint_path=tmp_path / "chk.json",
        candidate_checkpoint_path=tmp_path / "cand.json",
        manifest_path=tmp_path / "man.json",
        receipt_path=tmp_path / "rec.json",
        cas_path=tmp_path / "cas",
    )
    assert code == 1
    receipt = json.loads((tmp_path / "rec.json").read_text(encoding="utf-8"))
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
    config_file = tmp_path / "nz-gazette.yml"
    config_file.write_text("name: nz-gazette\nenabled: true\n", encoding="utf-8")

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_gazette_harvest.py",
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
        ],
    )
    monkeypatch.setattr(
        _MODULE,
        "sync_gazette_notices",
        lambda *_, **__: {
            "notices_synced": 0,
            "records": [],
            "errors": [],
            "processed_ids": [],
            "discovery": {},
        },
    )

    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0


def test_sync_gazette_notices_empty_seed(tmp_path: Path) -> None:
    """Verify empty discovery seed short-circuits to a no-targets report."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = NZGazetteAdapter(store)
    service = GazetteArchiveService(store=store, adapter=adapter)

    report = sync_gazette_notices(service, backfill_limit=0)
    assert report["notices_synced"] == 0
    assert report["records"] == []
    assert report["discovery"]["targets_count"] == 0


def test_sync_gazette_notices_with_real_service(tmp_path: Path) -> None:
    """Verify end-to-end sync through the real service with mocked transport."""
    store = ContentAddressedStore(tmp_path / "cas")

    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html><body><p>Seed notice body</p></body></html>",
        )

    transport = httpx.MockTransport(handler)
    seed = tmp_path / "seed.json"
    seed.write_text(
        '[{"notice_id": "2026-010", "issue_number": "7", "title": "Seeded"}]',
        encoding="utf-8",
    )

    client = httpx.AsyncClient(transport=transport)
    adapter = NZGazetteAdapter(store, client=client)
    service = GazetteArchiveService(store=store, adapter=adapter)
    try:
        report = sync_gazette_notices(service, seed_path=seed, backfill_limit=5)
    finally:
        asyncio.run(client.aclose())

    assert report["notices_synced"] == 1
    assert report["processed_ids"] == ["2026-010"]
    assert report["errors"] == []


def test_run_harvest_partial_retryable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify partial_retryable outcome when errors coexist with synced records."""
    config_file = tmp_path / "nz-gazette.yml"
    config_file.write_text("name: nz-gazette\nenabled: true\n", encoding="utf-8")

    record = {
        "schema_version": "archive-govt-nz.gazette/v1",
        "notice_id": "2026-003",
        "issue_number": "9",
        "year": 2026,
        "title": "Partial",
        "publication_date": "2026-08-22T00:00:00Z",
        "category": "General",
        "canonical_uri": "https://gazette.govt.nz/notice/id/2026-003",
        "raw_cas_hash_sha256": "b" * 64,
        "retrieval_timestamp": "2026-08-22T01:00:00Z",
        "content_text": "",
    }
    monkeypatch.setattr(
        _MODULE,
        "sync_gazette_notices",
        lambda *_, **__: {
            "notices_synced": 1,
            "records": [record],
            "errors": ["2026-004: failed: HTTP 500"],
            "processed_ids": ["2026-003"],
            "discovery": {},
        },
    )

    code = run_harvest(
        config_path=config_file,
        checkpoint_path=tmp_path / "chk.json",
        candidate_checkpoint_path=tmp_path / "cand.json",
        manifest_path=tmp_path / "man.json",
        receipt_path=tmp_path / "rec.json",
        cas_path=tmp_path / "cas",
    )
    assert code == 0
    receipt = json.loads((tmp_path / "rec.json").read_text(encoding="utf-8"))
    assert receipt["outcome"] == "partial_retryable"
