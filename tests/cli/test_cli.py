"""Comprehensive test suite for truthful archive-govt-nz CLI subcommands."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from archive_govt_nz.cli import (
    archive,
    capabilities,
    capture,
    derivatives,
    doctor,
    legislation,
    main,
    provenance,
    publish,
    replay,
    search,
    sources,
    verify,
    version,
)
from archive_govt_nz.cli_compat import (
    compat_nz_govt_social_main,
    compat_nzlc_main,
    compat_sm_govt_nz_main,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate version text and JSON outputs."""
    code_text = version(format="text")
    captured = capsys.readouterr()
    assert "0.1.0" in captured.out
    assert code_text == 0

    code_json = version(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "version"
    assert payload["status"] == "success"
    assert code_json == 0


def test_cli_doctor(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate doctor runtime health check in healthy and degraded states."""
    code_text = doctor(format="text")
    captured = capsys.readouterr()
    assert "doctor: status=runtime_compatible" in captured.out
    assert code_text == 0

    code_json = doctor(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "doctor"
    assert payload["status"] == "runtime_compatible"
    assert payload["python_min_satisfied"] is True
    assert payload["integrity_status"] == "not_checked"
    assert code_json == 0

    # Simulate Python version < 3.14
    monkeypatch.setattr(sys, "version_info", (3, 13, 0))
    code_degraded = doctor(format="text")
    captured_degraded = capsys.readouterr()
    assert "doctor: status=runtime_incompatible" in captured_degraded.out
    assert "Python >= 3.14 requirement not satisfied" in captured_degraded.err
    assert code_degraded == 1


def test_cli_capabilities(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate static capabilities catalogue."""
    code_text = capabilities(format="text")
    captured = capsys.readouterr()
    assert "cas_dual_hash" in captured.out
    assert code_text == 0

    code_json = capabilities(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "capabilities"
    assert payload["status"] == "compiled"
    assert payload["count"] > 0
    assert code_json == 0


def test_cli_sources_configured_and_missing(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate sources with configured seeds, empty, and missing directory."""
    code_ok = sources(format="json", registry_path="registry/seeds")
    captured_ok = capsys.readouterr()
    payload_ok = json.loads(captured_ok.out)
    assert payload_ok["command"] == "sources"
    assert payload_ok["status"] == "configured"
    assert payload_ok["registered_sources_count"] > 0
    assert code_ok == 0

    code_ok_text = sources(format="text", registry_path="registry/seeds")
    captured_ok_text = capsys.readouterr()
    assert "Registered sources:" in captured_ok_text.out
    assert code_ok_text == 0

    empty_dir = tmp_path / "empty_seeds"
    empty_dir.mkdir()
    code_empty = sources(format="json", registry_path=str(empty_dir))
    captured_empty = capsys.readouterr()
    payload_empty = json.loads(captured_empty.out)
    assert payload_empty["status"] == "empty"
    assert payload_empty["registered_sources_count"] == 0
    assert "No seed sources" in captured_empty.err
    assert code_empty == 1

    code_empty_text = sources(format="text", registry_path=str(empty_dir))
    captured_empty_text = capsys.readouterr()
    assert "Registered sources: 0 seeds" in captured_empty_text.out
    assert code_empty_text == 1

    missing_dir = tmp_path / "non_existent_seeds"
    code_missing = sources(format="json", registry_path=str(missing_dir))
    captured_missing = capsys.readouterr()
    payload_missing = json.loads(captured_missing.out)
    assert payload_missing["status"] == "not_configured"
    assert "Registry path not found" in captured_missing.err
    assert code_missing == 2

    code_missing_text = sources(format="text", registry_path=str(missing_dir))
    captured_missing_text = capsys.readouterr()
    assert "Error: Registry path not found" in captured_missing_text.out
    assert code_missing_text == 2


def test_cli_capture_not_configured_and_redirect(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Validate capture rejects standalone execution and redirects legislation."""
    code_text = capture("https://health.govt.nz", format="text")
    captured_text = capsys.readouterr()
    assert "not_configured" in captured_text.out
    assert "No standalone capture daemon" in captured_text.err
    assert code_text == 2

    code_json = capture("https://health.govt.nz", format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "capture"
    assert payload["status"] == "not_configured"
    assert "No standalone capture daemon" in payload["error"]
    assert code_json == 2

    code_leg = capture(
        "https://legislation.govt.nz",
        source_type="legislation",
        format="json",
    )
    captured_leg = capsys.readouterr()
    payload_leg = json.loads(captured_leg.out)
    assert payload_leg["status"] == "redirect"
    assert payload_leg["suggested_command"] == "archive-govt-nz legislation sync"
    assert "Legislation capture must be executed" in captured_leg.err
    assert code_leg == 2

    code_leg_text = capture(
        "https://legislation.govt.nz",
        source_type="legislation",
        format="text",
    )
    captured_leg_text = capsys.readouterr()
    assert "Error: Legislation capture must be executed" in captured_leg_text.out
    assert code_leg_text == 2


def test_cli_archive_inspection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate archive command with missing, empty, and populated directories."""
    missing_dir = tmp_path / "missing_warc"
    code_missing = archive(action="count", output_dir=str(missing_dir), format="json")
    captured_missing = capsys.readouterr()
    payload_missing = json.loads(captured_missing.out)
    assert payload_missing["status"] == "no_state"
    assert code_missing == 1

    code_missing_text = archive(
        action="count", output_dir=str(missing_dir), format="text"
    )
    captured_missing_text = capsys.readouterr()
    assert "status=no_state (not found)" in captured_missing_text.out
    assert code_missing_text == 1

    empty_dir = tmp_path / "empty_warc"
    empty_dir.mkdir()
    code_empty = archive(action="verify", output_dir=str(empty_dir), format="json")
    captured_empty = capsys.readouterr()
    payload_empty = json.loads(captured_empty.out)
    assert payload_empty["status"] == "no_state"
    assert code_empty == 1

    code_empty_text = archive(action="verify", output_dir=str(empty_dir), format="text")
    captured_empty_text = capsys.readouterr()
    assert "status=no_state (0 files)" in captured_empty_text.out
    assert code_empty_text == 1

    warc_file = empty_dir / "test.warc.gz"
    warc_file.write_bytes(b"WARC/1.0 header content")
    code_count = archive(action="count", output_dir=str(empty_dir), format="json")
    payload_count = json.loads(capsys.readouterr().out)
    assert payload_count["status"] == "observed"
    assert payload_count["warc_count"] == 1
    assert payload_count["total_bytes"] > 0
    assert code_count == 0

    code_verify = archive(action="verify", output_dir=str(empty_dir), format="text")
    captured_verify = capsys.readouterr()
    assert "status=failed" in captured_verify.out
    assert code_verify == 1


def test_cli_replay_absent_and_populated_cas(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate replay with absent CAS objects and valid/corrupted objects."""
    cas_dir = tmp_path / "cas"

    code_absent = replay(cas_dir=str(cas_dir), format="json")
    captured_absent = capsys.readouterr()
    payload_absent = json.loads(captured_absent.out)
    assert payload_absent["status"] == "no_state"
    assert payload_absent["records_replayed"] == 0
    assert code_absent == 1

    code_absent_text = replay(cas_dir=str(cas_dir), format="text")
    captured_absent_text = capsys.readouterr()
    assert "status=no_state (0 records)" in captured_absent_text.out
    assert code_absent_text == 1

    content = b"hello legislation payload"
    store = ContentAddressedStore(cas_dir)
    store.put_bytes(content)

    code_valid = replay(cas_dir=str(cas_dir), format="json")
    captured_valid = capsys.readouterr()
    payload_valid = json.loads(captured_valid.out)
    assert payload_valid["status"] == "verified"
    assert payload_valid["records_replayed"] == 1
    assert payload_valid["corrupted_records"] == 0
    assert code_valid == 0

    code_valid_text = replay(cas_dir=str(cas_dir), format="text")
    captured_valid_text = capsys.readouterr()
    assert "status=verified replayed=1 corrupted=0" in captured_valid_text.out
    assert code_valid_text == 0

    corrupt_receipt = store.put_bytes(b"content to corrupt")
    corrupt_receipt.path.write_bytes(b"mismatched content")
    code_corrupt = replay(cas_dir=str(cas_dir), format="json")
    captured_corrupt = capsys.readouterr()
    payload_corrupt = json.loads(captured_corrupt.out)
    assert payload_corrupt["status"] == "failed"
    assert payload_corrupt["corrupted_records"] == 1
    assert code_corrupt == 1

    code_corrupt_text = replay(cas_dir=str(cas_dir), format="text")
    captured_corrupt_text = capsys.readouterr()
    assert "status=failed" in captured_corrupt_text.out
    assert code_corrupt_text == 1


def test_cli_verify(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate multi-point verify checks in passed and degraded states."""
    code_text = verify(format="text")
    captured = capsys.readouterr()
    assert "Verification: status=" in captured.out
    assert code_text in (0, 1)

    code_json = verify(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "verify"
    assert payload["checks_executed"] > 0
    assert payload["checks_passed"] > 0
    assert payload["status"] in ("passed", "failed")
    assert code_json in (0, 1)

    monkeypatch.setattr(sys, "version_info", (3, 10, 0))
    code_deg = verify(format="text")
    captured_deg = capsys.readouterr()
    assert "status=failed" in captured_deg.out
    assert "python_runtime" in captured_deg.err
    assert code_deg == 1


def test_cli_provenance_ledger(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate provenance ledger query against real, missing, and corrupt ledger."""
    code_ok = provenance(
        ledger_path="evidence/archive-evidence-ledger.json", format="json"
    )
    captured_ok = capsys.readouterr()
    payload_ok = json.loads(captured_ok.out)
    assert payload_ok["command"] == "provenance"
    assert payload_ok["status"] == "validated"
    assert payload_ok["entities_tracked"] > 0
    assert code_ok == 0

    code_ok_text = provenance(
        ledger_path="evidence/archive-evidence-ledger.json", format="text"
    )
    captured_ok_text = capsys.readouterr()
    assert "Provenance ledger validated:" in captured_ok_text.out
    assert code_ok_text == 0

    missing_path = tmp_path / "missing_ledger.json"
    code_missing = provenance(ledger_path=str(missing_path), format="json")
    captured_missing = capsys.readouterr()
    payload_missing = json.loads(captured_missing.out)
    assert payload_missing["status"] == "no_state"
    assert payload_missing["entities_tracked"] == 0
    assert "Provenance ledger not found" in captured_missing.err
    assert code_missing == 1

    code_missing_text = provenance(ledger_path=str(missing_path), format="text")
    captured_missing_text = capsys.readouterr()
    assert "Provenance ledger not found:" in captured_missing_text.out
    assert code_missing_text == 1

    corrupt_path = tmp_path / "corrupt_ledger.json"
    corrupt_path.write_text("{ unclosed", encoding="utf-8")
    code_corrupt = provenance(ledger_path=str(corrupt_path), format="json")
    captured_corrupt = capsys.readouterr()
    payload_corrupt = json.loads(captured_corrupt.out)
    assert payload_corrupt["status"] == "corrupt"
    assert code_corrupt == 1

    code_corrupt_text = provenance(ledger_path=str(corrupt_path), format="text")
    captured_corrupt_text = capsys.readouterr()
    assert "Provenance ledger corrupt:" in captured_corrupt_text.out
    assert code_corrupt_text == 1

    list_path = tmp_path / "list_ledger.json"
    list_path.write_text('[{"id": 1}, {"id": 2}]', encoding="utf-8")
    code_list = provenance(ledger_path=str(list_path), format="json")
    payload_list = json.loads(capsys.readouterr().out)
    assert payload_list["status"] == "corrupt"
    assert code_list == 1

    scalar_path = tmp_path / "scalar_ledger.json"
    scalar_path.write_text("12345", encoding="utf-8")
    code_scalar = provenance(ledger_path=str(scalar_path), format="json")
    payload_scalar = json.loads(capsys.readouterr().out)
    assert payload_scalar["entities_tracked"] == 0
    assert payload_scalar["status"] == "corrupt"
    assert code_scalar == 1


def test_cli_derivatives(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate derivatives catalog."""
    code_text = derivatives(format="text")
    captured = capsys.readouterr()
    assert "parquet_curated_records" in captured.out
    assert code_text == 0

    code_json = derivatives(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "derivatives"
    assert len(payload["derivatives"]) > 0
    assert payload["status"] == "compiled"
    assert code_json == 0


def test_cli_search(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Validate search interface with missing and existing index directory."""
    code_text = search("health policy", format="text")
    captured = capsys.readouterr()
    assert "Search for 'health policy'" in captured.out
    assert code_text == 1

    code_json = search("health policy", format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "search"
    assert payload["query"] == "health policy"
    assert payload["status"] == "no_index"
    assert code_json == 1

    idx_dir = tmp_path / "idx"
    idx_dir.mkdir()
    code_idx = search("health", index_dir=str(idx_dir), format="json")
    payload_idx = json.loads(capsys.readouterr().out)
    assert payload_idx["status"] == "no_index"
    assert code_idx == 1


def test_cli_publish_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate publish dry-run controls with missing and ready staging."""
    missing_staging = tmp_path / "missing_staging"
    code_dry_missing = publish(
        target="dry-run", staging_dir=str(missing_staging), format="json"
    )
    payload_dry_missing = json.loads(capsys.readouterr().out)
    assert payload_dry_missing["status"] == "no_state"
    assert code_dry_missing == 1

    code_dry_missing_text = publish(
        target="dry-run", staging_dir=str(missing_staging), format="text"
    )
    captured_dry_missing_text = capsys.readouterr()
    assert "no_state" in captured_dry_missing_text.out
    assert code_dry_missing_text == 1

    missing_staging.mkdir()
    code_dry_ok = publish(
        target="dry-run", staging_dir=str(missing_staging), format="json"
    )
    payload_dry_ok = json.loads(capsys.readouterr().out)
    assert payload_dry_ok["status"] == "no_state"
    assert code_dry_ok == 1

    code_dry_ok_text = publish(
        target="dry-run", staging_dir=str(missing_staging), format="text"
    )
    captured_dry_ok_text = capsys.readouterr()
    assert "no_state" in captured_dry_ok_text.out
    assert code_dry_ok_text == 1


def test_cli_publish_remote_tokens_are_not_readiness_evidence(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Token presence cannot replace a fixed package and rights evidence."""
    monkeypatch.delenv("HF_TOKEN", raising=False)
    code_hf_missing = publish(target="huggingface", format="json")
    payload_hf_missing = json.loads(capsys.readouterr().out)
    assert payload_hf_missing["status"] == "no_state"
    assert code_hf_missing == 1

    code_hf_missing_text = publish(target="huggingface", format="text")
    captured_hf_text = capsys.readouterr()
    assert "no_state" in captured_hf_text.out
    assert code_hf_missing_text == 1

    monkeypatch.setenv("HF_TOKEN", "mock_hf_token")
    code_hf_ok = publish(target="huggingface", format="json")
    payload_hf_ok = json.loads(capsys.readouterr().out)
    assert payload_hf_ok["status"] == "no_state"
    assert code_hf_ok == 1

    monkeypatch.delenv("ZENODO_TOKEN", raising=False)
    code_zenodo_missing = publish(target="zenodo", format="json")
    payload_zenodo_missing = json.loads(capsys.readouterr().out)
    assert payload_zenodo_missing["status"] == "no_state"
    assert code_zenodo_missing == 1

    monkeypatch.setenv("ZENODO_TOKEN", "mock_zenodo_token")
    code_zenodo_ok = publish(target="zenodo", format="json")
    payload_zenodo_ok = json.loads(capsys.readouterr().out)
    assert payload_zenodo_ok["status"] == "no_state"
    assert code_zenodo_ok == 1

    code_unsupp = publish(target="unknown_target", format="json")
    payload_unsupp = json.loads(capsys.readouterr().out)
    assert payload_unsupp["status"] == "unsupported"
    assert code_unsupp == 5


def test_cli_legislation_doctor_and_discover(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate legislation doctor and discover actions."""
    code_doc = legislation(action="doctor", format="json")
    captured_doc = capsys.readouterr()
    payload_doc = json.loads(captured_doc.out)
    assert payload_doc["status"] == "runtime_compatible"
    assert code_doc == 0

    code_doc_text = legislation(action="doctor", format="text")
    captured_doc_text = capsys.readouterr()
    assert "status=runtime_compatible" in captured_doc_text.out
    assert code_doc_text == 0

    monkeypatch.setattr(sys, "version_info", (3, 10, 0))
    code_doc_deg = legislation(action="doctor", format="json")
    captured_doc_deg = capsys.readouterr()
    assert "Legislation doctor failures:" in captured_doc_deg.err
    assert code_doc_deg == 1

    def mock_iter_search(*_args: object, **_kwargs: object) -> list[dict[str, str]]:
        return [{"work_id": "act-101", "title": "Test Act", "legislation_type": "act"}]

    monkeypatch.setattr(
        "archive_govt_nz.domains.legislation.api.NZLegislationApiClient.iter_search_works",
        mock_iter_search,
    )
    code_disc = legislation(action="discover", search_term="test", format="json")
    payload_disc = json.loads(capsys.readouterr().out)
    assert payload_disc["status"] == "discovered"
    assert payload_disc["candidate_works_count"] == 1
    assert payload_disc["work_ids"] == ["act-101"]
    assert code_disc == 0

    code_disc_text = legislation(action="discover", search_term="test", format="text")
    assert "candidates=1" in capsys.readouterr().out
    assert code_disc_text == 0


def test_cli_legislation_sync_and_no_change(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validate real legislation sync pipeline and idempotent no_change rerun."""
    cas_path = str(tmp_path / "cas")
    chk_path = str(tmp_path / "checkpoints" / "weekly.json")
    man_path = str(tmp_path / "manifests" / "weekly.json")

    xml_content = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b'<act id="DLM1" status="in-force"><title>Ombudsmen Act 1975</title></act>'
    )

    async def mock_get_doc(
        _self: object, _url: str, **_kwargs: object
    ) -> tuple[int, bytes, dict[str, str]]:
        return 200, xml_content, {"content-type": "application/xml"}

    monkeypatch.setattr(
        "archive_govt_nz.domains.legislation.api.NZLegislationApiClient.get_document_raw_async",
        mock_get_doc,
    )

    code_sync1 = legislation(
        action="sync",
        cas_path=cas_path,
        checkpoint_path=chk_path,
        manifest_path=man_path,
        work_ids=["act-1975-9"],
        batch_id="batch-1",
        max_works=5,
        format="json",
    )
    payload_sync1 = json.loads(capsys.readouterr().out)
    assert payload_sync1["status"] == "success"
    assert payload_sync1["records_preserved"] == 1
    assert code_sync1 == 0

    code_sync2 = legislation(
        action="sync",
        cas_path=cas_path,
        checkpoint_path=chk_path,
        manifest_path=man_path,
        work_ids=["act-1975-9"],
        batch_id="batch-1",
        format="text",
    )
    captured_sync2 = capsys.readouterr()
    assert "status=no_change" in captured_sync2.out
    assert code_sync2 == 0

    async def mock_fail_doc(
        _self: object, _url: str, **_kwargs: object
    ) -> tuple[int, bytes, dict[str, str]]:
        return 500, b"", {}

    monkeypatch.setattr(
        "archive_govt_nz.domains.legislation.api.NZLegislationApiClient.get_document_raw_async",
        mock_fail_doc,
    )
    code_fail = legislation(
        action="sync",
        cas_path=cas_path,
        checkpoint_path=chk_path,
        manifest_path=man_path,
        work_ids=["act-failing"],
        batch_id="batch-failure",
        fail_fast=True,
        force_resync=True,
        format="json",
    )
    payload_fail = json.loads(capsys.readouterr().out)
    assert payload_fail["status"] == "failed"
    assert code_fail == 2


def test_cli_legislation_validate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate legislation validate against missing, corrupt, and valid files."""
    man_path = tmp_path / "manifest.json"

    code_val_missing = legislation(
        action="validate", manifest_path=str(man_path), format="json"
    )
    payload_val_missing = json.loads(capsys.readouterr().out)
    assert payload_val_missing["status"] == "no_state"
    assert code_val_missing == 1

    code_val_missing_text = legislation(
        action="validate", manifest_path=str(man_path), format="text"
    )
    assert "status=no_state" in capsys.readouterr().out
    assert code_val_missing_text == 1

    man_path.write_text("{ unclosed", encoding="utf-8")
    code_val_corrupt = legislation(
        action="validate", manifest_path=str(man_path), format="json"
    )
    assert json.loads(capsys.readouterr().out)["status"] == "invalid"
    assert code_val_corrupt == 1

    code_val_corrupt_text = legislation(
        action="validate", manifest_path=str(man_path), format="text"
    )
    assert "status=invalid" in capsys.readouterr().out
    assert code_val_corrupt_text == 1

    invalid_man = {
        "schema_version": "archive-govt-nz.legislation-manifest/v1",
        "records": [{"document_id": "", "work_id": ""}],
    }
    man_path.write_text(json.dumps(invalid_man), encoding="utf-8")
    code_val_invalid = legislation(
        action="validate", manifest_path=str(man_path), format="json"
    )
    payload_val_inv = json.loads(capsys.readouterr().out)
    assert payload_val_inv["status"] == "invalid"
    assert code_val_invalid == 1

    valid_man = {
        "schema_version": "archive-govt-nz.legislation-manifest/v1",
        "manifest_sha256": "abcdef123456",
        "total_records": 1,
        "records": [
            {
                "document_id": "act:1975:9:v1:xml",
                "work_id": "act-1975-9",
                "title": "Ombudsmen Act 1975",
                "canonical_uri": "https://example.com/act.xml",
            }
        ],
    }
    man_path.write_text(json.dumps(valid_man), encoding="utf-8")

    code_val_ok = legislation(
        action="validate", manifest_path=str(man_path), format="json"
    )
    payload_val_ok = json.loads(capsys.readouterr().out)
    assert payload_val_ok["status"] == "invalid"
    assert payload_val_ok["records_validated"] == 0
    assert code_val_ok == 1

    code_val_ok_text = legislation(
        action="validate", manifest_path=str(man_path), format="text"
    )
    assert "status=invalid" in capsys.readouterr().out
    assert code_val_ok_text == 1


def test_cli_legislation_manifest(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate legislation manifest against missing, corrupt, and valid files."""
    man_path = tmp_path / "manifest.json"

    code_man_missing = legislation(
        action="manifest", manifest_path=str(man_path), format="json"
    )
    payload_man_missing = json.loads(capsys.readouterr().out)
    assert payload_man_missing["status"] == "no_state"
    assert code_man_missing == 1

    code_man_missing_text = legislation(
        action="manifest", manifest_path=str(man_path), format="text"
    )
    assert "status=no_state" in capsys.readouterr().out
    assert code_man_missing_text == 1

    man_path.write_text("{ unclosed", encoding="utf-8")
    code_man_corrupt = legislation(
        action="manifest", manifest_path=str(man_path), format="json"
    )
    assert json.loads(capsys.readouterr().out)["status"] == "corrupt"
    assert code_man_corrupt == 1

    code_man_corrupt_text = legislation(
        action="manifest", manifest_path=str(man_path), format="text"
    )
    assert "status=corrupt" in capsys.readouterr().out
    assert code_man_corrupt_text == 1

    valid_man = {
        "schema_version": "archive-govt-nz.legislation-manifest/v1",
        "manifest_sha256": "abcdef123456",
        "total_records": 1,
        "records": [],
    }
    man_path.write_text(json.dumps(valid_man), encoding="utf-8")

    code_man_ok = legislation(
        action="manifest", manifest_path=str(man_path), format="json"
    )
    payload_man_ok = json.loads(capsys.readouterr().out)
    assert payload_man_ok["status"] == "corrupt"
    assert payload_man_ok["total_records"] == 0
    assert code_man_ok == 1

    code_man_ok_text = legislation(
        action="manifest", manifest_path=str(man_path), format="text"
    )
    assert "status=corrupt" in capsys.readouterr().out
    assert code_man_ok_text == 1


def test_cli_legislation_coverage_dynamic_sensitivity(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate coverage changes dynamically and rejects missing state."""
    man_path = tmp_path / "cov_manifest.json"
    chk_path = tmp_path / "cov_checkpoint.json"
    cas_path = str(tmp_path / "cas")

    code_cov_none = legislation(
        action="coverage",
        manifest_path=str(man_path),
        checkpoint_path=str(chk_path),
        cas_path=cas_path,
        format="json",
    )
    payload_cov_none = json.loads(capsys.readouterr().out)
    assert payload_cov_none["status"] == "no_state"
    assert payload_cov_none["candidate_works_count"] == 0
    assert code_cov_none == 1

    code_cov_none_text = legislation(
        action="coverage",
        manifest_path=str(man_path),
        checkpoint_path=str(chk_path),
        cas_path=cas_path,
        format="text",
    )
    assert "status=no_state" in capsys.readouterr().out
    assert code_cov_none_text == 1

    manifest_3_records = {
        "records": [
            {
                "document_id": "act:1:v1:xml",
                "canonical_uri": "https://example.com/1.xml",
            },
            {
                "document_id": "act:2:v1:xml",
                "canonical_uri": "https://example.com/2.xml",
            },
            {
                "document_id": "act:3:v1:html",
                "canonical_uri": "https://example.com/3.html",
            },
        ]
    }
    man_path.write_text(json.dumps(manifest_3_records), encoding="utf-8")

    code_cov3 = legislation(
        action="coverage",
        manifest_path=str(man_path),
        checkpoint_path=str(chk_path),
        cas_path=cas_path,
        format="json",
    )
    payload_cov3 = json.loads(capsys.readouterr().out)
    assert payload_cov3["status"] == "invalid"
    assert code_cov3 == 1

    code_cov3_text = legislation(
        action="coverage",
        manifest_path=str(man_path),
        checkpoint_path=str(chk_path),
        cas_path=cas_path,
        format="text",
    )
    assert "status=invalid" in capsys.readouterr().out
    assert code_cov3_text == 1

    manifest_5_records = {
        "records": [
            {
                "document_id": f"act:{i}:v1:xml",
                "canonical_uri": f"https://example.com/{i}.xml",
            }
            for i in range(5)
        ]
    }
    man_path.write_text(json.dumps(manifest_5_records), encoding="utf-8")

    code_cov5 = legislation(
        action="coverage",
        manifest_path=str(man_path),
        checkpoint_path=str(chk_path),
        cas_path=cas_path,
        format="json",
    )
    payload_cov5 = json.loads(capsys.readouterr().out)
    assert payload_cov5["status"] == "invalid"
    assert code_cov5 == 1


def test_cli_legislation_changes_and_status(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate changes and status actions in text and JSON formats."""
    man_path = tmp_path / "manifest.json"
    chk_path = tmp_path / "checkpoint.json"
    cas_path = str(tmp_path / "cas")

    code_chg = legislation(
        action="changes", checkpoint_path=str(chk_path), format="json"
    )
    payload_chg = json.loads(capsys.readouterr().out)
    assert payload_chg["status"] == "no_state"
    assert payload_chg["total_changes"] == 0
    assert code_chg == 1

    code_chg_text = legislation(
        action="changes", checkpoint_path=str(chk_path), format="text"
    )
    assert "status=no_state" in capsys.readouterr().out
    assert code_chg_text == 1

    code_stat_no = legislation(
        action="status",
        cas_path=cas_path,
        checkpoint_path=str(chk_path),
        manifest_path=str(man_path),
        format="json",
    )
    assert json.loads(capsys.readouterr().out)["status"] == "no_state"
    assert code_stat_no == 1

    code_stat_no_text = legislation(
        action="status",
        cas_path=cas_path,
        checkpoint_path=str(chk_path),
        manifest_path=str(man_path),
        format="text",
    )
    assert "status=no_state" in capsys.readouterr().out
    assert code_stat_no_text == 1

    chk_path.write_text('{"processed_work_ids": ["act-1"]}', encoding="utf-8")
    code_stat_ok = legislation(
        action="status",
        cas_path=cas_path,
        checkpoint_path=str(chk_path),
        manifest_path=str(man_path),
        format="json",
    )
    assert json.loads(capsys.readouterr().out)["status"] == "no_state"
    assert code_stat_ok == 1

    code_stat_ok_text = legislation(
        action="status",
        cas_path=cas_path,
        checkpoint_path=str(chk_path),
        manifest_path=str(man_path),
        format="text",
    )
    assert "status=no_state" in capsys.readouterr().out
    assert code_stat_ok_text == 1


def test_cli_legislation_replay_and_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Validate replay, publication-plan, and publication-verify actions."""
    man_path = tmp_path / "manifest.json"
    cas_path = str(tmp_path / "cas")

    code_rep = legislation(action="replay", cas_path=cas_path, format="json")
    assert json.loads(capsys.readouterr().out)["status"] == "no_state"
    assert code_rep == 1

    code_plan_no = legislation(
        action="publication-plan", manifest_path=str(man_path), format="json"
    )
    assert json.loads(capsys.readouterr().out)["status"] == "no_state"
    assert code_plan_no == 1

    code_plan_no_text = legislation(
        action="publication-plan", manifest_path=str(man_path), format="text"
    )
    assert "status=no_state" in capsys.readouterr().out
    assert code_plan_no_text == 1

    man_path.write_text("{ unclosed", encoding="utf-8")
    code_plan_corrupt = legislation(
        action="publication-plan", manifest_path=str(man_path), format="json"
    )
    assert json.loads(capsys.readouterr().out)["status"] == "corrupt"
    assert code_plan_corrupt == 1

    code_plan_corrupt_text = legislation(
        action="publication-plan", manifest_path=str(man_path), format="text"
    )
    assert "status=corrupt" in capsys.readouterr().out
    assert code_plan_corrupt_text == 1

    man_path.write_text('{"total_records": 10}', encoding="utf-8")
    code_plan_ok = legislation(
        action="publication-plan", manifest_path=str(man_path), format="json"
    )
    payload_plan_ok = json.loads(capsys.readouterr().out)
    assert payload_plan_ok["status"] == "corrupt"
    assert payload_plan_ok["total_records"] == 0
    assert code_plan_ok == 1

    code_plan_ok_text = legislation(
        action="publication-plan", manifest_path=str(man_path), format="text"
    )
    assert "status=corrupt" in capsys.readouterr().out
    assert code_plan_ok_text == 1

    monkeypatch.delenv("HF_TOKEN", raising=False)
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)
    code_pub_v_no = legislation(action="publication-verify", format="json")
    assert json.loads(capsys.readouterr().out)["status"] == "unverified"
    assert code_pub_v_no == 3

    code_pub_v_no_text = legislation(action="publication-verify", format="text")
    assert "status=unverified" in capsys.readouterr().out
    assert code_pub_v_no_text == 3

    monkeypatch.setenv("HF_TOKEN", "mock_hf")
    code_pub_v_ok = legislation(action="publication-verify", format="json")
    assert json.loads(capsys.readouterr().out)["status"] == "unverified"
    assert code_pub_v_ok == 3

    code_pub_v_ok_text = legislation(action="publication-verify", format="text")
    assert "status=unverified" in capsys.readouterr().out
    assert code_pub_v_ok_text == 3


def test_compat_wrappers_and_nzlc_legacy_args(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate legacy wrappers including nzlc argument mapping."""
    monkeypatch.setattr("archive_govt_nz.cli.app", lambda: None)

    compat_sm_govt_nz_main()
    captured = capsys.readouterr()
    assert "DEPRECATION NOTICE: `sm-govt-nz`" in captured.err

    compat_nz_govt_social_main()
    captured = capsys.readouterr()
    assert "DEPRECATION NOTICE: `nz-govt-social`" in captured.err

    monkeypatch.setattr(sys, "argv", ["nzlc", "doctor", "--json"])
    code_nzlc_doc = compat_nzlc_main()
    captured_nzlc_doc = capsys.readouterr()
    assert "DEPRECATION NOTICE: `nzlc`" in captured_nzlc_doc.err
    payload_nzlc_doc = json.loads(captured_nzlc_doc.out)
    assert payload_nzlc_doc["action"] == "doctor"
    assert code_nzlc_doc == 0

    monkeypatch.setattr(sys, "argv", ["nzlc", "coverage-report", "--json"])
    code_nzlc_cov = compat_nzlc_main()
    assert "DEPRECATION NOTICE: `nzlc`" in capsys.readouterr().err
    assert code_nzlc_cov in (0, 1)

    monkeypatch.setattr(sys, "argv", ["nzlc"])
    code_nzlc_empty = compat_nzlc_main()
    assert code_nzlc_empty in (0, 1)

    monkeypatch.setattr(sys, "argv", ["nzlc", "unknown-command"])
    code_nzlc_unk = compat_nzlc_main()
    assert code_nzlc_unk == 5


def test_cli_legislation_unknown_action() -> None:
    """Validate invalid legislation action returns exit code 5."""
    code_unk = legislation(action="unknown_action")  # type: ignore[arg-type]
    assert code_unk == 5


def test_cli_legislation_coverage_fallbacks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate coverage fallback to checkpoint and CAS when manifest is missing."""
    man_path = tmp_path / "non_existent_manifest.json"
    chk_path = tmp_path / "fallback_checkpoint.json"
    cas_path = str(tmp_path / "cas")

    chk_path.write_text(
        json.dumps({"processed_work_ids": ["act-1", "act-2"]}),
        encoding="utf-8",
    )
    code_chk = legislation(
        action="coverage",
        manifest_path=str(man_path),
        checkpoint_path=str(chk_path),
        cas_path=cas_path,
        format="json",
    )
    payload_chk = json.loads(capsys.readouterr().out)
    assert payload_chk["candidate_works_count"] == 0
    assert payload_chk["status"] == "no_state"
    assert code_chk == 1

    chk_path.unlink()
    cas_sha = tmp_path / "cas" / "sha256"
    cas_sha.mkdir(parents=True)
    (cas_sha / "abc123").write_bytes(b"content")
    code_cas = legislation(
        action="coverage",
        manifest_path=str(man_path),
        checkpoint_path=str(chk_path),
        cas_path=cas_path,
        format="json",
    )
    payload_cas = json.loads(capsys.readouterr().out)
    assert payload_cas["candidate_works_count"] == 0
    assert payload_cas["status"] == "no_state"
    assert code_cas == 1


def test_cli_legislation_sync_partial_and_total_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Validate sync handling of partial failure and total failure without fail_fast."""
    cas_path = str(tmp_path / "cas")
    chk_path = str(tmp_path / "checkpoints" / "sync_fail.json")
    man_path = str(tmp_path / "manifests" / "sync_fail.json")

    async def mock_mixed_doc(
        _self: object, url: str, **_kwargs: object
    ) -> tuple[int, bytes, dict[str, str]]:
        if "act-ok" in url:
            xml = b"<act><title>OK Act</title></act>"
            return 200, xml, {"content-type": "application/xml"}
        return 500, b"", {}

    monkeypatch.setattr(
        "archive_govt_nz.domains.legislation.api.NZLegislationApiClient.get_document_raw_async",
        mock_mixed_doc,
    )

    code_partial = legislation(
        action="sync",
        cas_path=cas_path,
        checkpoint_path=chk_path,
        manifest_path=man_path,
        work_ids=["act-ok", "act-bad"],
        batch_id="batch-partial",
        fail_fast=False,
        force_resync=True,
        format="json",
    )
    payload_partial = json.loads(capsys.readouterr().out)
    assert payload_partial["status"] == "partial"
    assert payload_partial["records_preserved"] == 1
    assert code_partial == 1

    code_total_fail = legislation(
        action="sync",
        cas_path=cas_path,
        checkpoint_path=chk_path,
        manifest_path=man_path,
        work_ids=["act-bad"],
        batch_id="batch-total-failure",
        fail_fast=False,
        force_resync=True,
        format="json",
    )
    payload_total_fail = json.loads(capsys.readouterr().out)
    assert payload_total_fail["status"] == "failed"
    assert payload_total_fail["records_preserved"] == 0
    assert code_total_fail == 2


def test_main_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate main entrypoint invokes cyclopts app."""
    called = []
    monkeypatch.setattr("archive_govt_nz.cli.app", lambda: called.append(True))
    main()
    assert called == [True]
