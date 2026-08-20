"""Adversarial contract tests for the service-backed legislation CLI."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any

from archive_govt_nz.cli import legislation
from archive_govt_nz.cli_compat import compat_nzlc_main
from archive_govt_nz.domains.legislation.manifest import (
    compute_legislation_inventory_sha256,
    compute_legislation_manifest_sha256,
)

if TYPE_CHECKING:
    from pathlib import Path

    import pytest


def _record(work_id: str = "work-1") -> dict[str, Any]:
    return {
        "schema_version": "archive-govt-nz.legislation/v2",
        "document_id": f"document-{work_id}",
        "work_id": work_id,
        "expression_id": f"expression-{work_id}",
        "manifestation_id": f"manifestation-{work_id}",
        "title": f"Title {work_id}",
        "legislation_type": "act",
        "status": "historical",
        "canonical_uri": f"https://www.legislation.govt.nz/{work_id}",
        "raw_cas_hash_sha256": "a" * 64,
        "raw_cas_hash_blake3": "b" * 64,
        "byte_size": 3,
        "retrieval_timestamp": "2026-08-20T00:00:00Z",
        "rights_statement": None,
        "redistribution_policy": "rights_review_required",
    }


def _write_manifest(path: Path, *, discovered: list[str] | None = None) -> None:
    records = [_record()]
    work_ids = discovered or ["work-1"]
    payload = {
        "schema_version": "archive-govt-nz.legislation-manifest/v1",
        "generated_at": "2026-08-20T00:00:00Z",
        "run_id": "batch-1",
        "records": records,
        "total_records": len(records),
        "manifest_sha256": compute_legislation_manifest_sha256(records),
        "discovered_work_ids": work_ids,
        "discovered_works_count": len(work_ids),
        "discovered_inventory_sha256": compute_legislation_inventory_sha256(work_ids),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_sync_rejects_fabricated_default_selection(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Sync requires explicit bounded selection and a batch identity."""
    code = legislation(
        action="sync",
        cas_path=str(tmp_path / "cas"),
        checkpoint_path=str(tmp_path / "checkpoint.json"),
        manifest_path=str(tmp_path / "manifest.json"),
        max_works=0,
        format="json",
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 5
    assert payload["status"] == "invalid_request"
    assert not (tmp_path / "cas").exists()


def test_validate_rejects_manifest_root_drift(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Document/work field presence cannot authenticate a manifest."""
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["manifest_sha256"] = "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    code = legislation(action="validate", manifest_path=str(manifest), format="json")
    result = json.loads(capsys.readouterr().out)
    assert code == 1
    assert result["status"] == "invalid"


def test_coverage_uses_authenticated_discovered_inventory_denominator(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """One manifested work out of two discovered works is 50%, not 100%."""
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, discovered=["work-1", "work-2"])
    code = legislation(action="coverage", manifest_path=str(manifest), format="json")
    result = json.loads(capsys.readouterr().out)
    assert code == 1
    assert result["candidate_works_count"] == 2
    assert result["retrieved_works_count"] == 1
    assert result["coverage_percent"] == 50.0
    assert result["unresolved_gaps_count"] == 1


def test_flat_cas_and_absent_state_are_not_operational(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A flat arbitrary CAS file cannot satisfy status or doctor."""
    flat = tmp_path / "cas" / "sha256"
    flat.mkdir(parents=True)
    (flat / ("a" * 64)).write_bytes(b"garbage")
    code_status = legislation(
        action="status", cas_path=str(tmp_path / "cas"), format="json"
    )
    status = json.loads(capsys.readouterr().out)
    assert code_status == 1
    assert status["status"] == "no_state"

    code_doctor = legislation(
        action="doctor",
        cas_path=str(tmp_path / "missing-cas"),
        checkpoint_path=str(tmp_path / "missing-checkpoint.json"),
        format="json",
    )
    doctor = json.loads(capsys.readouterr().out)
    assert code_doctor == 0
    assert doctor["status"] == "runtime_compatible"


def test_changes_without_evidence_are_no_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An absent change-event ledger cannot become observed zero changes."""
    code = legislation(
        action="changes",
        checkpoint_path=str(tmp_path / "missing.json"),
        format="json",
    )
    result = json.loads(capsys.readouterr().out)
    assert code == 1
    assert result["status"] == "no_state"


def test_publication_actions_do_not_close_authority_or_rights(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A manifest and token are not publication or rights evidence."""
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest)
    code_plan = legislation(
        action="publication-plan", manifest_path=str(manifest), format="json"
    )
    plan = json.loads(capsys.readouterr().out)
    assert code_plan == 3
    assert plan["status"] == "blocked"

    monkeypatch.setenv("HF_TOKEN", "capability-only")
    code_verify = legislation(action="publication-verify", format="json")
    verification = json.loads(capsys.readouterr().out)
    assert code_verify == 3
    assert verification["status"] == "unverified"


def test_unknown_legacy_action_is_usage_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The compatibility shim cannot silently reinterpret unknown commands."""
    monkeypatch.setattr(sys, "argv", ["nzlc", "definitely-unknown"])
    assert compat_nzlc_main() == 5
    assert "Unknown nzlc action" in capsys.readouterr().err
