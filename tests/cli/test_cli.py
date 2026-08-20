"""Comprehensive test suite for truthful archive-govt-nz CLI subcommands."""

from __future__ import annotations

import hashlib
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
    assert "doctor: status=healthy" in captured.out
    assert code_text == 0

    code_json = doctor(format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "doctor"
    assert payload["status"] == "healthy"
    assert payload["python_min_satisfied"] is True
    assert code_json == 0

    # Simulate Python version < 3.11
    monkeypatch.setattr(sys, "version_info", (3, 10, 0))
    code_degraded = doctor(format="text")
    captured_degraded = capsys.readouterr()
    assert "doctor: status=unhealthy" in captured_degraded.out
    assert "Python >= 3.11 requirement not satisfied" in captured_degraded.err
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
    # 1. Configured seeds directory (JSON and text)
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

    # 2. Empty directory (JSON and text)
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

    # 3. Missing directory (JSON and text)
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


def test_cli_capture_not_configured(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate capture rejects standalone execution without active daemon."""
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


def test_cli_archive_inspection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate archive command with missing, empty, and populated directories."""
    # 1. Missing output_dir (JSON and text)
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

    # 2. Empty output_dir (JSON and text)
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

    # 3. Populated output_dir (JSON and text)
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
    assert "status=verified" in captured_verify.out
    assert code_verify == 0


def test_cli_replay_absent_and_populated_cas(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate replay with absent CAS objects and valid/corrupted objects."""
    cas_dir = tmp_path / "cas"

    # 1. Absent CAS objects (JSON and text)
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

    # 2. Valid CAS objects (JSON and text)
    sha_dir = cas_dir / "sha256"
    sha_dir.mkdir(parents=True)
    content = b"hello legislation payload"
    expected_hex = hashlib.sha256(content).hexdigest()
    (sha_dir / expected_hex).write_bytes(content)

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

    # 3. Corrupted CAS object (JSON and text)
    corrupt_hex = "0000000000000000000000000000000000000000000000000000000000000000"
    (sha_dir / corrupt_hex).write_bytes(b"mismatched content")
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
    assert payload["status"] in ("passed", "degraded")
    assert code_json in (0, 1)

    # Degraded check
    monkeypatch.setattr(sys, "version_info", (3, 10, 0))
    code_deg = verify(format="text")
    captured_deg = capsys.readouterr()
    assert "status=degraded" in captured_deg.out
    assert "Verification failures: python_version" in captured_deg.err
    assert code_deg == 1


def test_cli_provenance_ledger(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate provenance ledger query against real, missing, and corrupt ledger."""
    # 1. Real ledger file (JSON and text)
    code_ok = provenance(
        ledger_path="evidence/archive-evidence-ledger.json", format="json"
    )
    captured_ok = capsys.readouterr()
    payload_ok = json.loads(captured_ok.out)
    assert payload_ok["command"] == "provenance"
    assert payload_ok["status"] == "synced"
    assert payload_ok["entities_tracked"] > 0
    assert code_ok == 0

    code_ok_text = provenance(
        ledger_path="evidence/archive-evidence-ledger.json", format="text"
    )
    captured_ok_text = capsys.readouterr()
    assert "Provenance ledger synced:" in captured_ok_text.out
    assert code_ok_text == 0

    # 2. Missing ledger file (JSON and text)
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

    # 3. Corrupt ledger file (JSON and text)
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

    # 4. List ledger file
    list_path = tmp_path / "list_ledger.json"
    list_path.write_text('[{"id": 1}, {"id": 2}]', encoding="utf-8")
    code_list = provenance(ledger_path=str(list_path), format="json")
    payload_list = json.loads(capsys.readouterr().out)
    assert payload_list["entities_tracked"] == 2
    assert code_list == 0

    # 5. Scalar JSON value in ledger file
    scalar_path = tmp_path / "scalar_ledger.json"
    scalar_path.write_text("12345", encoding="utf-8")
    code_scalar = provenance(ledger_path=str(scalar_path), format="json")
    payload_scalar = json.loads(capsys.readouterr().out)
    assert payload_scalar["entities_tracked"] == 0
    assert code_scalar == 0


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
    assert code_text == 0

    code_json = search("health policy", format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "search"
    assert payload["query"] == "health policy"
    assert payload["status"] == "no_index"
    assert code_json == 0

    # Populated index directory
    idx_dir = tmp_path / "idx"
    idx_dir.mkdir()
    code_idx = search("health", index_dir=str(idx_dir), format="json")
    payload_idx = json.loads(capsys.readouterr().out)
    assert payload_idx["status"] == "observed"
    assert code_idx == 0


def test_cli_publish_dry_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate publish dry-run controls with missing and ready staging."""
    missing_staging = tmp_path / "missing_staging"
    code_dry_missing = publish(
        target="dry-run", staging_dir=str(missing_staging), format="json"
    )
    payload_dry_missing = json.loads(capsys.readouterr().out)
    assert payload_dry_missing["status"] == "not_configured"
    assert code_dry_missing == 2

    code_dry_missing_text = publish(
        target="dry-run", staging_dir=str(missing_staging), format="text"
    )
    captured_dry_missing_text = capsys.readouterr()
    assert "not_configured" in captured_dry_missing_text.out
    assert code_dry_missing_text == 2

    missing_staging.mkdir()
    code_dry_ok = publish(
        target="dry-run", staging_dir=str(missing_staging), format="json"
    )
    payload_dry_ok = json.loads(capsys.readouterr().out)
    assert payload_dry_ok["status"] == "ready"
    assert code_dry_ok == 0

    code_dry_ok_text = publish(
        target="dry-run", staging_dir=str(missing_staging), format="text"
    )
    captured_dry_ok_text = capsys.readouterr()
    assert "ready" in captured_dry_ok_text.out
    assert code_dry_ok_text == 0


def test_cli_publish_remote_tokens(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Validate publish remote token negative and positive controls."""
    # 1. HuggingFace
    monkeypatch.delenv("HF_TOKEN", raising=False)
    code_hf_missing = publish(target="huggingface", format="json")
    payload_hf_missing = json.loads(capsys.readouterr().out)
    assert payload_hf_missing["status"] == "not_configured"
    assert "HF_TOKEN not configured" in payload_hf_missing["error"]
    assert code_hf_missing == 2

    code_hf_missing_text = publish(target="huggingface", format="text")
    captured_hf_text = capsys.readouterr()
    assert "not_configured" in captured_hf_text.out
    assert code_hf_missing_text == 2

    monkeypatch.setenv("HF_TOKEN", "mock_hf_token")
    code_hf_ok = publish(target="huggingface", format="json")
    payload_hf_ok = json.loads(capsys.readouterr().out)
    assert payload_hf_ok["status"] == "ready"
    assert code_hf_ok == 0

    # 2. Zenodo
    monkeypatch.delenv("ZENODO_TOKEN", raising=False)
    code_zenodo_missing = publish(target="zenodo", format="json")
    payload_zenodo_missing = json.loads(capsys.readouterr().out)
    assert payload_zenodo_missing["status"] == "not_configured"
    assert code_zenodo_missing == 2

    monkeypatch.setenv("ZENODO_TOKEN", "mock_zenodo_token")
    code_zenodo_ok = publish(target="zenodo", format="json")
    payload_zenodo_ok = json.loads(capsys.readouterr().out)
    assert payload_zenodo_ok["status"] == "ready"
    assert code_zenodo_ok == 0

    # 3. Unsupported target
    code_unsupp = publish(target="unknown_target", format="json")
    payload_unsupp = json.loads(capsys.readouterr().out)
    assert payload_unsupp["status"] == "unsupported"
    assert code_unsupp == 5


def test_cli_legislation(capsys: pytest.CaptureFixture[str]) -> None:
    """Validate legislation interface."""
    legislation(action="coverage", format="text")
    captured = capsys.readouterr()
    assert "Legislation action 'coverage':" in captured.out

    legislation(action="coverage", format="json")
    captured_json = capsys.readouterr()
    payload = json.loads(captured_json.out)
    assert payload["command"] == "legislation"
    assert payload["coverage_percent"] >= 0.0
    assert payload["candidate_works_count"] == 33693

    legislation(action="doctor", format="json")
    doc_json = json.loads(capsys.readouterr().out)
    assert doc_json["status"] == "healthy"

    legislation(action="manifest", format="json")
    man_json = json.loads(capsys.readouterr().out)
    assert man_json["manifest_status"] in ("ready", "pending")

    legislation(action="publication-plan", format="json")
    pub_json = json.loads(capsys.readouterr().out)
    assert pub_json["status"] == "staged"


def test_compat_wrappers(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Validate legacy compatibility entrypoint deprecation notices."""
    monkeypatch.setattr("archive_govt_nz.cli.app", lambda: None)

    compat_sm_govt_nz_main()
    captured = capsys.readouterr()
    assert "DEPRECATION NOTICE: `sm-govt-nz`" in captured.err

    compat_nz_govt_social_main()
    captured = capsys.readouterr()
    assert "DEPRECATION NOTICE: `nz-govt-social`" in captured.err

    compat_nzlc_main()
    captured = capsys.readouterr()
    assert "DEPRECATION NOTICE: `nzlc`" in captured.err


def test_main_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Validate main entrypoint invokes cyclopts app."""
    called = []
    monkeypatch.setattr("archive_govt_nz.cli.app", lambda: called.append(True))
    main()
    assert called == [True]
