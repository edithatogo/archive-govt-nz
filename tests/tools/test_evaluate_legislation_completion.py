"""Anti-simulation and completion evaluator negative-control test suite."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import pytest

sys.path.insert(0, str(Path(__file__).parents[2]))
from tools.evaluate_legislation_completion import (
    evaluate_completion,
    fetch_live_donor_state,
    scan_codebase_ast_defects,
    verify_hosted_publication_readback,
)
from tools.validate_contracts import (
    execute_acceptance_check,
    validate_contract_dict,
)


def _setup_minimal_passing_repo(tmp_path: Path) -> Path:
    """Create a minimal passing repository environment where prerequisites are met."""
    root = Path(__file__).parents[2]

    # 1. Schemas
    schema_dir = tmp_path / "schemas" / "contracts" / "v1"
    schema_dir.mkdir(parents=True)
    shutil.copy(
        root / "schemas/contracts/v1/contract.schema.json",
        schema_dir / "contract.schema.json",
    )

    # 2. Source modules with clean implementations
    src_dir = tmp_path / "src" / "archive_govt_nz"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text("", encoding="utf-8")
    (src_dir / "cli.py").write_text(
        "def run(): return {'status': 'dynamic'}\n", encoding="utf-8"
    )
    (src_dir / "mcp_server.py").write_text(
        "class StdioServerTransport: pass\nclass Server: pass\n",
        encoding="utf-8",
    )
    adapters_dir = src_dir / "adapters"
    adapters_dir.mkdir(parents=True)
    (adapters_dir / "nz_legislation.py").write_text(
        "from archive_govt_nz.domains.legislation.api import NZLegislationApiClient\n",
        encoding="utf-8",
    )

    # 3. Evidence
    ev_dir = tmp_path / "evidence" / "migrations" / "corpus-legislation-nz"
    ev_dir.mkdir(parents=True)
    parity_dir = ev_dir / "parity"
    parity_dir.mkdir(parents=True)

    # Valid observation receipt
    (ev_dir / "observation-receipt.json").write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.observation/v1",
                "status": "verified",
                "observed_cycles": 2,
            }
        ),
        encoding="utf-8",
    )

    # Valid cached donor snapshot with 0 open issues for the positive base
    (ev_dir / "live-donor-snapshot.json").write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.donor-snapshot/v1",
                "source_url": "https://api.github.com/repos/edithatogo/corpus-legislation-nz",
                "retrieved_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "open_issues_count": 0,
                "response_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                "is_cached": True,
            }
        ),
        encoding="utf-8",
    )

    # Valid hosted publication readback
    (ev_dir / "hosted-publication-readback.json").write_text(
        json.dumps(
            {
                "platform": "huggingface",
                "canonical_dataset_id": "edithatogo/corpus-legislation-nz",
                "revision_or_record_id": "main@12345678",
                "source_url": "https://huggingface.co/datasets/edithatogo/corpus-legislation-nz",
                "retrieved_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "remote_file_inventory": ["data/corpus.parquet"],
                "remote_metadata_hash": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
                "status": "verified",
            }
        ),
        encoding="utf-8",
    )

    # 4. Conductor completed tracks
    tracks_dir = tmp_path / "conductor" / "tracks"
    for i in range(1, 13):
        tpath = tracks_dir / f"legislation_corrective_track_{i:02d}_20260818"
        tpath.mkdir(parents=True)
        (tpath / "metadata.json").write_text(
            json.dumps({"id": f"track_{i}", "status": "completed"}),
            encoding="utf-8",
        )

    # 5. Contracts (15 valid contracts)
    contracts_base = tmp_path / "contracts"
    contracts_base.mkdir(parents=True)
    for cfile in (root / "contracts").rglob("*.yaml"):
        target_cfile = contracts_base / cfile.relative_to(root / "contracts")
        target_cfile.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(cfile, target_cfile)

    return tmp_path


def test_evaluator_passes_on_current_completed_repo() -> None:
    """The evaluator must report PASSED on the current, evidence-backed repo."""
    root = Path(__file__).parents[2]
    attestation = (
        root
        / "evidence/migrations/corpus-legislation-nz/shadow-operation-cutover-attestation.json"
    )
    assert attestation.is_file(), (
        "attestation must exist for the completed-state assertion"
    )
    result = subprocess.run(
        [
            "uv",
            "run",
            "--locked",
            "python",
            "tools/evaluate_legislation_completion.py",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "PASSED (COMPLETE)" in result.stdout
    assert "[BLOCKER]" not in result.stdout


def test_negative_control_1_fixed_cli_count_detected(tmp_path: Path) -> None:
    """Test 1: Fixed 100% coverage or constant returns in CLI must be detected."""
    base = _setup_minimal_passing_repo(tmp_path)
    (base / "src/archive_govt_nz/cli.py").write_text(
        'def status(): return {"coverage_percent": 100.0}\n', encoding="utf-8"
    )

    blockers = scan_codebase_ast_defects(base)
    assert any("Fixed 100% coverage constant" in b for b in blockers)


def test_negative_control_2_fixed_mcp_count_detected(tmp_path: Path) -> None:
    """Test 2: Fixed constants in MCP server must be detected."""
    base = _setup_minimal_passing_repo(tmp_path)
    (base / "src/archive_govt_nz/mcp_server.py").write_text(
        'def get_health(): return {"coverage_percent": 100.0, "status": "healthy"}\n',
        encoding="utf-8",
    )

    blockers = scan_codebase_ast_defects(base)
    assert any("Fixed production constants" in b for b in blockers)


def test_negative_control_3_adapter_not_using_client(tmp_path: Path) -> None:
    """Test 3: NZLegislationAdapter not utilizing NZLegislationApiClient must be detected."""
    base = _setup_minimal_passing_repo(tmp_path)
    (base / "src/archive_govt_nz/adapters/nz_legislation.py").write_text(
        "import httpx\nclass NZLegislationAdapter:\n    async def fetch(): pass\n",
        encoding="utf-8",
    )

    blockers = scan_codebase_ast_defects(base)
    assert any("does not utilize NZLegislationApiClient" in b for b in blockers)


def test_negative_control_4_unresolved_donor_issues_detected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test 4: Open donor issues in snapshot must be reported as active blocker."""
    base = _setup_minimal_passing_repo(tmp_path)
    snap_file = (
        base / "evidence/migrations/corpus-legislation-nz/live-donor-snapshot.json"
    )
    snap = json.loads(snap_file.read_text(encoding="utf-8"))
    snap["open_issues_count"] = 30
    snap_file.write_text(json.dumps(snap), encoding="utf-8")

    def mock_urlopen(*_args: object, **_kwargs: object) -> object:
        msg = "Offline"
        raise urllib.error.URLError(msg)

    monkeypatch.setattr(urllib.request, "urlopen", mock_urlopen)

    is_complete, res = evaluate_completion(base)
    assert is_complete is False
    assert any("30 active donor issues/PRs remain open" in b for b in res["blockers"])


def test_negative_control_5_live_state_unavailable_does_not_become_zero(
    tmp_path: Path,
) -> None:
    """Test 5: Live state unavailability does not default to 0."""
    base = _setup_minimal_passing_repo(tmp_path)
    # Remove snapshot so both live (dummy domain) and cached fail
    snap_file = (
        base / "evidence/migrations/corpus-legislation-nz/live-donor-snapshot.json"
    )
    snap_file.unlink()

    state = fetch_live_donor_state(
        repo="nonexistent-org/nonexistent-repo-12345", root=base
    )
    assert state.get("live_state_unavailable") is True
    assert state.get("open_issues_count") is None


def test_negative_control_6_fake_hosted_readback_boolean_rejected(
    tmp_path: Path,
) -> None:
    """Test 6: Plain boolean flag without structured receipt is rejected."""
    base = _setup_minimal_passing_repo(tmp_path)
    rb_file = (
        base
        / "evidence/migrations/corpus-legislation-nz/hosted-publication-readback.json"
    )
    rb_file.unlink()

    ok, msg = verify_hosted_publication_readback(base)
    assert ok is False
    assert "missing" in msg.lower()


def test_negative_control_7_missing_remote_revision_rejected(
    tmp_path: Path,
) -> None:
    """Test 7: Hosted readback receipt missing revision ID is rejected."""
    base = _setup_minimal_passing_repo(tmp_path)
    rb_file = (
        base
        / "evidence/migrations/corpus-legislation-nz/hosted-publication-readback.json"
    )
    rb_data = json.loads(rb_file.read_text(encoding="utf-8"))
    del rb_data["revision_or_record_id"]
    rb_file.write_text(json.dumps(rb_data), encoding="utf-8")

    ok, msg = verify_hosted_publication_readback(base)
    assert ok is False
    assert "missing field 'revision_or_record_id'" in msg


def test_negative_control_8_acceptance_check_not_executed_rejected(
    tmp_path: Path,
) -> None:
    """Test 8: Acceptance check failing with non-matching exit code is rejected."""
    check = {
        "check_id": "CHK-FAIL-01",
        "executor_id": "pytest_runner",
        "execution_class": "local_test",
        "side_effect_class": "read_only",
        "command": "uv run pytest tests/nonexistent_test_path.py",
        "expected_exit_code": 0,
        "timeout_seconds": 10,
    }
    passed, receipt = execute_acceptance_check(check, tmp_path)
    assert passed is False
    assert receipt["exit_code"] != 0


def test_negative_control_9_executor_outside_typed_registry_rejected(
    tmp_path: Path,
) -> None:
    """Test 9: Acceptance checks with unregistered executor IDs are rejected."""
    data: dict[str, Any] = {
        "contract_id": "test-contract",
        "version": "1.0.0",
        "status": "active",
        "scope": "test",
        "owning_track": "test_track",
        "baseline": {
            "audited_target_commit": "c154578f4e7de3585e6b5885c157fc6ef2c7564b",
            "audited_donor_commit": "749918c251da59dc890c19dfda2ab9a021fd8ca6",
        },
        "invariants": ["test"],
        "preconditions": ["test"],
        "postconditions": ["test"],
        "forbidden_actions": ["test"],
        "acceptance_checks": [
            {
                "check_id": "CHK-BAD-01",
                "executor_id": "arbitrary_shell_executor",
                "execution_class": "local_read_only",
                "side_effect_class": "read_only",
                "timeout_seconds": 30,
                "expected_exit_code": 0,
                "evidence_destination": "evidence/test.json",
                "command": "sh -c 'echo evil'",
            }
        ],
        "evidence_paths": ["evidence/test.json"],
        "created_at": "2026-08-18T12:00:00Z",
        "updated_at": "2026-08-18T12:00:00Z",
    }
    errors = validate_contract_dict(data, Path("test.yaml"), repo_root=tmp_path)
    assert any("unknown or missing executor_id" in e for e in errors)


def test_negative_control_10_missing_weekly_observation_receipt_rejected(
    tmp_path: Path,
) -> None:
    """Test 10: Missing observation receipt fails evidence integrity."""
    base = _setup_minimal_passing_repo(tmp_path)
    obs = base / "evidence/migrations/corpus-legislation-nz/observation-receipt.json"
    obs.unlink()

    is_complete, res = evaluate_completion(base)
    assert is_complete is False
    assert any("observation-receipt.json" in b for b in res["blockers"])


def test_negative_control_11_in_progress_must_track_rejected(
    tmp_path: Path,
) -> None:
    """Test 11: In-progress Conductor child tracks block completion."""
    base = _setup_minimal_passing_repo(tmp_path)
    meta = (
        base / "conductor/tracks/legislation_corrective_track_01_20260818/metadata.json"
    )
    meta.write_text(
        json.dumps(
            {
                "id": "legislation_corrective_track_01",
                "status": "in_progress",
            }
        ),
        encoding="utf-8",
    )

    is_complete, res = evaluate_completion(base)
    assert is_complete is False
    assert any("child tracks remain in progress" in b for b in res["blockers"])


def test_negative_control_12_future_dated_contract_rejected(
    tmp_path: Path,
) -> None:
    """Test 12: Future dated contract timestamp is rejected."""
    base = _setup_minimal_passing_repo(tmp_path)
    future_time = (datetime.now(UTC) + timedelta(days=10)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    data: dict[str, Any] = {
        "contract_id": "test-future",
        "version": "1.0.0",
        "status": "active",
        "scope": "test",
        "owning_track": "legislation_corrective_track_01_20260818",
        "baseline": {
            "audited_target_commit": "c154578f4e7de3585e6b5885c157fc6ef2c7564b",
            "audited_donor_commit": "749918c251da59dc890c19dfda2ab9a021fd8ca6",
        },
        "invariants": ["test"],
        "preconditions": ["test"],
        "postconditions": ["test"],
        "forbidden_actions": ["test"],
        "acceptance_checks": [],
        "evidence_paths": [],
        "created_at": future_time,
        "updated_at": future_time,
    }
    errors = validate_contract_dict(data, Path("test.yaml"), repo_root=base)
    assert any("Future timestamp" in e for e in errors)


def test_negative_control_13_stale_external_state_snapshot_rejected(
    tmp_path: Path,
) -> None:
    """Test 13: Stale cached snapshot older than max age is rejected."""
    base = _setup_minimal_passing_repo(tmp_path)
    stale_time = (datetime.now(UTC) - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    snap_file = (
        base / "evidence/migrations/corpus-legislation-nz/live-donor-snapshot.json"
    )
    snap = json.loads(snap_file.read_text(encoding="utf-8"))
    snap["retrieved_at"] = stale_time
    snap_file.write_text(json.dumps(snap), encoding="utf-8")

    state = fetch_live_donor_state(
        repo="nonexistent-org/nonexistent-repo-12345", root=base
    )
    assert state.get("live_state_unavailable") is True
