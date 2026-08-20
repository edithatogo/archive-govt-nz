"""Adversarial contract tests for the service-backed legislation CLI."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING, Any

import pytest

from archive_govt_nz.cli import legislation
from archive_govt_nz.cli_compat import compat_nzlc_main
from archive_govt_nz.domains.legislation.cli_state import (
    coverage_counts,
    load_authenticated_manifest,
    verify_linked_state,
)
from archive_govt_nz.domains.legislation.corpus import (
    LegislationSyncResult,
)
from archive_govt_nz.domains.legislation.coverage import LegislationCoverageReport
from archive_govt_nz.domains.legislation.manifest import (
    compute_legislation_inventory_sha256,
    compute_legislation_manifest_sha256,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


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


def _write_authenticated_state(tmp_path: Path) -> dict[str, Path]:
    """Write one mutually linked manifest, checkpoint, and sharded CAS."""
    cas_path = tmp_path / "cas"
    stored = ContentAddressedStore(cas_path).put_bytes(b"one")
    record = _record()
    record.update(
        {
            "raw_cas_hash_sha256": stored.sha256,
            "raw_cas_hash_blake3": stored.blake3,
            "byte_size": stored.byte_count,
        }
    )
    records = [record]
    work_ids = ["work-1"]
    manifest_sha256 = compute_legislation_manifest_sha256(records)
    inventory_sha256 = compute_legislation_inventory_sha256(work_ids)
    manifest = {
        "schema_version": "archive-govt-nz.legislation-manifest/v1",
        "generated_at": "2026-08-20T00:00:00Z",
        "run_id": "batch-1",
        "records": records,
        "total_records": 1,
        "manifest_sha256": manifest_sha256,
        "discovered_work_ids": work_ids,
        "discovered_works_count": 1,
        "discovered_inventory_sha256": inventory_sha256,
    }
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    checkpoint = {
        "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
        "last_updated": "2026-08-20T00:00:00Z",
        "completed_batches": ["batch-1"],
        "processed_work_ids": work_ids,
        "last_processed_index": 1,
        "total_records_preserved": 1,
        "metadata": {
            "manifest_sha256": manifest_sha256,
            "discovered_inventory_sha256": inventory_sha256,
            "conditional_requests": {},
        },
    }
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint_path.write_text(json.dumps(checkpoint), encoding="utf-8")
    return {
        "cas_path": cas_path,
        "manifest_path": manifest_path,
        "checkpoint_path": checkpoint_path,
    }


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


def test_sync_delegates_explicit_selection_to_archive_service(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The CLI serializes the service result without duplicating acquisition."""
    observed: dict[str, Any] = {}

    async def fake_sync(_self: object, **kwargs: object) -> LegislationSyncResult:
        observed.update(kwargs)
        return LegislationSyncResult(
            status="no_change",
            works_attempted=1,
            works_synced=0,
            records_preserved=0,
            records=[],
            manifest={},
            coverage=LegislationCoverageReport(total_seed_works=1),
            checkpoint={},
        )

    monkeypatch.setattr(
        "archive_govt_nz.cli.LegislationArchiveService.sync_works", fake_sync
    )
    code = legislation(
        action="sync",
        work_ids=["work-1"],
        batch_id="batch-1",
        cas_path=str(tmp_path / "cas"),
        checkpoint_path=str(tmp_path / "checkpoint.json"),
        manifest_path=str(tmp_path / "manifest.json"),
        format="json",
    )
    result = json.loads(capsys.readouterr().out)
    assert code == 0
    assert result["status"] == "no_change"
    assert observed["work_ids"] == ["work-1"]
    assert observed["search_terms"] is None
    assert observed["batch_id"] == "batch-1"


def test_discovery_empty_and_failure_are_non_success(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """An empty or failed search cannot become discovered evidence."""
    monkeypatch.setattr(
        "archive_govt_nz.domains.legislation.api.NZLegislationApiClient.iter_search_works",
        lambda *_args, **_kwargs: [],
    )
    empty_code = legislation(action="discover", search_term="none", format="json")
    empty = json.loads(capsys.readouterr().out)
    assert empty_code == 1
    assert empty["status"] == "no_state"

    def fail(*_args: object, **_kwargs: object) -> list[dict[str, str]]:
        msg = "transport failed"
        raise ValueError(msg)

    monkeypatch.setattr(
        "archive_govt_nz.domains.legislation.api.NZLegislationApiClient.iter_search_works",
        fail,
    )
    failure_code = legislation(action="discover", search_term="fail", format="json")
    failure = json.loads(capsys.readouterr().out)
    assert failure_code == 2
    assert failure["status"] == "failed"


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


def test_authenticated_state_supports_validate_manifest_coverage_status_and_replay(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Affirmative CLI states require one fully linked durable target state."""
    state = _write_authenticated_state(tmp_path)
    assert (
        verify_linked_state(
            state["cas_path"], state["checkpoint_path"], state["manifest_path"]
        )
        == 1
    )
    common = {
        "manifest_path": str(state["manifest_path"]),
        "checkpoint_path": str(state["checkpoint_path"]),
        "cas_path": str(state["cas_path"]),
        "format": "json",
    }
    expected = {
        "validate": "valid",
        "manifest": "ready",
        "coverage": "complete",
        "status": "operational",
        "replay": "verified",
    }
    for action, status in expected.items():
        code = legislation(action=action, **common)  # type: ignore[arg-type]
        result = json.loads(capsys.readouterr().out)
        assert code == 0
        assert result["status"] == status


@pytest.mark.parametrize(
    "case",
    [
        "checkpoint_not_object",
        "checkpoint_root",
        "checkpoint_count",
        "cas_bytes",
        "blake3",
        "byte_size",
    ],
)
def test_status_and_replay_reject_divergent_durable_state(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    case: str,
) -> None:
    """Root, byte, and dual-hash divergence cannot become operational."""
    state = _write_authenticated_state(tmp_path)
    if case == "checkpoint_not_object":
        state["checkpoint_path"].write_text("[]", encoding="utf-8")
    elif case == "checkpoint_root":
        checkpoint = json.loads(state["checkpoint_path"].read_text(encoding="utf-8"))
        checkpoint["metadata"]["manifest_sha256"] = "0" * 64
        state["checkpoint_path"].write_text(json.dumps(checkpoint), encoding="utf-8")
    elif case == "checkpoint_count":
        checkpoint = json.loads(state["checkpoint_path"].read_text(encoding="utf-8"))
        checkpoint["total_records_preserved"] = 2
        state["checkpoint_path"].write_text(json.dumps(checkpoint), encoding="utf-8")
    elif case == "cas_bytes":
        manifest = json.loads(state["manifest_path"].read_text(encoding="utf-8"))
        digest = manifest["records"][0]["raw_cas_hash_sha256"]
        (state["cas_path"] / "sha256" / digest[:2] / digest).write_bytes(b"bad")
    elif case == "blake3":
        manifest = json.loads(state["manifest_path"].read_text(encoding="utf-8"))
        manifest["records"][0]["raw_cas_hash_blake3"] = "0" * 64
        manifest["manifest_sha256"] = compute_legislation_manifest_sha256(
            manifest["records"]
        )
        state["manifest_path"].write_text(json.dumps(manifest), encoding="utf-8")
        checkpoint = json.loads(state["checkpoint_path"].read_text(encoding="utf-8"))
        checkpoint["metadata"]["manifest_sha256"] = manifest["manifest_sha256"]
        state["checkpoint_path"].write_text(json.dumps(checkpoint), encoding="utf-8")
    else:
        manifest = json.loads(state["manifest_path"].read_text(encoding="utf-8"))
        manifest["records"][0]["byte_size"] = 4
        manifest["manifest_sha256"] = compute_legislation_manifest_sha256(
            manifest["records"]
        )
        state["manifest_path"].write_text(json.dumps(manifest), encoding="utf-8")
        checkpoint = json.loads(state["checkpoint_path"].read_text(encoding="utf-8"))
        checkpoint["metadata"]["manifest_sha256"] = manifest["manifest_sha256"]
        state["checkpoint_path"].write_text(json.dumps(checkpoint), encoding="utf-8")

    for action in ("status", "replay"):
        code = legislation(
            action=action,  # type: ignore[arg-type]
            manifest_path=str(state["manifest_path"]),
            checkpoint_path=str(state["checkpoint_path"]),
            cas_path=str(state["cas_path"]),
            format="json",
        )
        result = json.loads(capsys.readouterr().out)
        assert code == 1
        assert result["status"] == "invalid"


def test_cli_state_helpers_reject_missing_inventory_and_invalid_records(
    tmp_path: Path,
) -> None:
    """The critical state module fails every unauthenticated manifest class."""
    missing = tmp_path / "missing.json"
    assert coverage_counts(missing) == (0, 0, 0, 0)
    with pytest.raises(ValueError, match="manifest is missing"):
        load_authenticated_manifest(missing)

    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    for field in (
        "discovered_work_ids",
        "discovered_works_count",
        "discovered_inventory_sha256",
    ):
        payload.pop(field)
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="authenticated discovered inventory"):
        load_authenticated_manifest(manifest)

    _write_manifest(manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["records"][0]["canonical_uri"] = 1
    payload["manifest_sha256"] = compute_legislation_manifest_sha256(payload["records"])
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="manifest record is invalid"):
        load_authenticated_manifest(manifest)


def test_coverage_counts_classifies_html_manifestations(tmp_path: Path) -> None:
    """Coverage projects XML and HTML manifestations from canonical IDs."""
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["records"][0]["manifestation_id"] = "work-1:html:latest"
    payload["manifest_sha256"] = compute_legislation_manifest_sha256(payload["records"])
    manifest.write_text(json.dumps(payload), encoding="utf-8")
    assert coverage_counts(manifest) == (1, 1, 0, 1)


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


def test_text_failures_preserve_fail_closed_exit_semantics(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Human-readable output must not bypass discovery or sync failures."""

    def fail_discovery(*_args: object, **_kwargs: object) -> list[dict[str, str]]:
        message = "discovery unavailable"
        raise ValueError(message)

    monkeypatch.setattr(
        "archive_govt_nz.domains.legislation.api.NZLegislationApiClient.iter_search_works",
        fail_discovery,
    )
    assert legislation(action="discover", search_term="act", format="text") == 2
    assert "status=failed" in capsys.readouterr().out

    assert legislation(action="sync", batch_id="", format="text") == 5
    assert "status=invalid_request" in capsys.readouterr().out


@pytest.mark.parametrize("output_format", ["json", "text"])
def test_sync_transport_failure_is_non_success(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
    output_format: str,
) -> None:
    """A service exception cannot be represented as a completed sync."""

    async def fail_sync(_self: object, **_kwargs: object) -> LegislationSyncResult:
        message = "source unavailable"
        raise OSError(message)

    monkeypatch.setattr(
        "archive_govt_nz.cli.LegislationArchiveService.sync_works", fail_sync
    )
    code = legislation(
        action="sync",
        work_ids=["work-1"],
        batch_id="batch-1",
        cas_path=str(tmp_path / "cas"),
        checkpoint_path=str(tmp_path / "checkpoint.json"),
        manifest_path=str(tmp_path / "manifest.json"),
        format=output_format,  # type: ignore[arg-type]
    )
    output = capsys.readouterr()
    assert code == 2
    assert "source unavailable" in output.err
    if output_format == "json":
        assert json.loads(output.out)["status"] == "failed"
    else:
        assert "status=failed" in output.out


def test_text_success_projections_require_authenticated_state(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Text projections use the same authenticated manifest and CAS state."""
    state = _write_authenticated_state(tmp_path)
    common = {
        "manifest_path": str(state["manifest_path"]),
        "checkpoint_path": str(state["checkpoint_path"]),
        "cas_path": str(state["cas_path"]),
        "format": "text",
    }
    for action, marker in (
        ("validate", "status=valid"),
        ("coverage", "status=complete"),
        ("status", "status=operational"),
    ):
        assert legislation(action=action, **common) == 0  # type: ignore[arg-type]
        assert marker in capsys.readouterr().out


def test_text_incomplete_and_unverified_projections_are_non_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Text mode retains nonzero exits for incomplete or unauthenticated state."""
    manifest = tmp_path / "manifest.json"
    _write_manifest(manifest, discovered=["work-1", "work-2"])
    assert (
        legislation(action="coverage", manifest_path=str(manifest), format="text") == 1
    )
    assert "status=incomplete" in capsys.readouterr().out

    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text("{}", encoding="utf-8")
    assert (
        legislation(action="changes", checkpoint_path=str(checkpoint), format="json")
        == 1
    )
    assert json.loads(capsys.readouterr().out)["status"] == "unverified"
    assert (
        legislation(action="changes", checkpoint_path=str(checkpoint), format="text")
        == 1
    )
    assert "status=unverified" in capsys.readouterr().out

    assert (
        legislation(
            action="replay",
            cas_path=str(tmp_path / "missing-cas"),
            checkpoint_path=str(checkpoint),
            manifest_path=str(manifest),
            format="text",
        )
        == 1
    )
    assert "status=no_state" in capsys.readouterr().out

    assert (
        legislation(
            action="publication-plan", manifest_path=str(manifest), format="text"
        )
        == 3
    )
    assert "status=blocked" in capsys.readouterr().out


def test_text_invalid_status_and_replay_are_non_success(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Corrupt linked state stays invalid in human-readable mode."""
    state = _write_authenticated_state(tmp_path)
    checkpoint = json.loads(state["checkpoint_path"].read_text(encoding="utf-8"))
    checkpoint["metadata"]["manifest_sha256"] = "0" * 64
    state["checkpoint_path"].write_text(json.dumps(checkpoint), encoding="utf-8")
    common = {
        "manifest_path": str(state["manifest_path"]),
        "checkpoint_path": str(state["checkpoint_path"]),
        "cas_path": str(state["cas_path"]),
        "format": "text",
    }
    for action in ("status", "replay"):
        assert legislation(action=action, **common) == 1  # type: ignore[arg-type]
        assert "status=invalid" in capsys.readouterr().out
