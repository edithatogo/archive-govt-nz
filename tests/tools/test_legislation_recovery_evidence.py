"""Integrity checks for committed Prompt 10 recovery evidence."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "evidence/migrations/corpus-legislation-nz/durable-recovery"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_recovery_evidence_binds_authority_and_durable_stages() -> None:
    """Require usable stage artifacts and an explicit authority chain."""
    authority_path = BASE / "authority-decision-20260903.json"
    authority = _load(authority_path)
    assert authority["decision_id"] == "maintainer-legislation-selected-552-20260903"
    assert (
        authority["decisions"]["payload_redistribution"]
        == "approved_public_selected_552"
    )
    assert (
        authority["decisions"]["recovered_state_parent_use"]
        == "approved_bounded_no_write_preflight"
    )
    assert authority["expiry_policy"].startswith("no_expiry_for_the_exact_hash_bound")
    readback = authority["governed_external_readback"]
    readback_path = ROOT / readback["path"]
    assert readback["integration_status"] == "merged_verified"
    assert readback["authority_commit"] == "d60ed58420d1fe39dc420bbe047b9bf901b0d66d"
    assert _sha(readback_path) == readback["expected_sha256"]

    for number in (1, 2):
        attempt = _load(BASE / f"recovery-attempt-{number:02d}-20260903.json")
        stage_path = ROOT / attempt["durable_stage_receipt"]["path"]
        assert _sha(stage_path) == attempt["durable_stage_receipt"]["sha256"]
        assert attempt["rights_authority"]["receipt_sha256"] == _sha(authority_path)
        stage = _load(stage_path)
        for artifact in stage["durable_artifacts"].values():
            artifact_path = ROOT / artifact["path"]
            assert artifact_path.is_file()
            assert _sha(artifact_path) == artifact["sha256"]
        preflight = stage["parent_preflight"]
        assert preflight["decision_id"] == authority["decision_id"]
        assert preflight["authority_receipt_sha256"] == _sha(authority_path)
        assert (
            preflight["stage_input_tree_sha256"]
            == preflight["stage_output_tree_sha256"]
        )
        assert preflight["stage_unchanged"] is True
        assert stage["workspace"]["destroyed"] is True
        headers = stage["download"]["safe_response_headers"]
        assert headers["status_chain"] == [302, 200]
        assert headers["final_content_length"] == 71_776_346
        assert headers["sensitive_headers_retained"] is False
        assert stage["verification"]["status"] == "verified_local_package"
        assert stage["reconstruction"]["mismatches_count"] == 0
        assert (
            stage["reconciliation_interpretation"][
                "restored_state_unexplained_mismatches"
            ]
            == []
        )


def test_recovery_runbook_uses_exact_published_filename() -> None:
    """Keep the runbook pinned to the published package filename."""
    text = (ROOT / "docs/legislation/independent-durable-recovery.md").read_text(
        encoding="utf-8"
    )
    assert "/<digest>/canonical-state.zip" in text
    assert "/<digest>/state.zip" not in text
