"""Tests for evidence-index-driven legislation completion evaluation."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture
    from _pytest.monkeypatch import MonkeyPatch

sys.path.insert(0, str(Path(__file__).parents[2]))

from tools.evaluate_legislation_completion import DIMENSIONS, evaluate_completion, main

ROOT = Path(__file__).parents[2]


def _write_repo(tmp_path: Path, statuses: dict[str, str] | None = None) -> Path:
    schema = tmp_path / "schemas/legislation-evidence-index-v1.schema.json"
    schema.parent.mkdir(parents=True)
    shutil.copy(ROOT / "schemas/legislation-evidence-index-v1.schema.json", schema)
    dimension_statuses = statuses or dict.fromkeys(DIMENSIONS, "complete")
    complete_kinds = {
        "code_capability_migration": "capability_matrix",
        "operational_state_migration": "state_verification",
        "corpus_custody_recoverability": "recovery_readback",
        "publication_identity_migration": "identity_verification",
    }
    entries = []
    evaluator_inputs = {}
    dimensions = {}
    for name in DIMENSIONS:
        status = dimension_statuses[name]
        evidence_id = f"proof-{name}"
        evidence = tmp_path / f"evidence/{evidence_id}.json"
        evidence.parent.mkdir(parents=True, exist_ok=True)
        evidence.write_text('{"status":"verified"}\n', encoding="utf-8")
        classification = "active" if status == "complete" else status
        entries.append(
            {
                "evidence_id": evidence_id,
                "path": f"evidence/{evidence_id}.json",
                "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                "classification": classification,
                "artefact_type": "receipt",
                "proof_kind": (
                    complete_kinds[name]
                    if classification == "active"
                    else "blocker_receipt"
                ),
                "claim_dimensions": [name],
                "rationale": f"Controlled proof for {name}.",
            }
        )
        evaluator_inputs[name] = [evidence_id] if classification == "active" else []
        dimensions[name] = {
            "status": status,
            "proof_ids": [evidence_id],
            "rationale": "Controlled test dimension.",
        }
    index: dict[str, Any] = {
        "schema_version": "archive-govt-nz.legislation-evidence-index/v1",
        "index_id": "test-index-v1",
        "generated_at": "2026-09-02T00:00:00Z",
        "target_repository": "edithatogo/archive-govt-nz",
        "target_commit": "6" * 40,
        "donor_repository": "edithatogo/corpus-legislation-nz",
        "donor_commit": "b" * 40,
        "entries": entries,
        "evaluator_inputs": evaluator_inputs,
        "dimensions": dimensions,
    }
    path = tmp_path / "evidence/migrations/corpus-legislation-nz/evidence-index.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(index) + "\n", encoding="utf-8")
    return tmp_path


def test_all_complete_active_selected_proofs_pass(tmp_path: Path) -> None:
    """Four complete dimensions with selected active proof pass."""
    complete, result = evaluate_completion(_write_repo(tmp_path))
    assert complete is True
    assert result["status"] == "complete"
    assert all(row["proof_eligible"] for row in result["dimensions"].values())


def test_missing_index_fails_closed(tmp_path: Path) -> None:
    """A missing canonical index cannot produce a completion claim."""
    schema = tmp_path / "schemas/legislation-evidence-index-v1.schema.json"
    schema.parent.mkdir(parents=True)
    shutil.copy(ROOT / "schemas/legislation-evidence-index-v1.schema.json", schema)
    complete, result = evaluate_completion(tmp_path)
    assert complete is False
    assert result["evidence_index_valid"] is False
    assert "unreadable_json" in result["errors"][0]


def test_bad_index_fails_closed(tmp_path: Path) -> None:
    """A malformed canonical index fails before evidence evaluation."""
    base = _write_repo(tmp_path)
    path = base / "evidence/migrations/corpus-legislation-nz/evidence-index.json"
    path.write_text("[]\n", encoding="utf-8")
    complete, result = evaluate_completion(base)
    assert complete is False
    assert "expected_object" in result["errors"][0]


def test_invalidated_evidence_cannot_be_evaluator_input(tmp_path: Path) -> None:
    """An invalidated receipt cannot remain selected as evaluator proof."""
    base = _write_repo(tmp_path)
    path = base / "evidence/migrations/corpus-legislation-nz/evidence-index.json"
    index = json.loads(path.read_text(encoding="utf-8"))
    index["entries"][0]["classification"] = "invalidated"
    index["entries"][0]["invalidated_by"] = "correction"
    correction = base / "evidence/correction.json"
    correction.write_text('{"status":"verified"}\n', encoding="utf-8")
    index["entries"].append(
        {
            "evidence_id": "correction",
            "path": "evidence/correction.json",
            "sha256": hashlib.sha256(correction.read_bytes()).hexdigest(),
            "classification": "active",
            "artefact_type": "receipt",
            "proof_kind": "capability_matrix",
            "claim_dimensions": list(DIMENSIONS),
            "rationale": "Superseding controlled test proof.",
        }
    )
    path.write_text(json.dumps(index) + "\n", encoding="utf-8")
    complete, result = evaluate_completion(base)
    assert complete is False
    assert "non_active_evaluator_input" in result["errors"][0]


def test_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    """Changed evidence bytes invalidate their indexed proof."""
    base = _write_repo(tmp_path)
    first_path = json.loads(
        (
            base / "evidence/migrations/corpus-legislation-nz/evidence-index.json"
        ).read_text()
    )["entries"][0]["path"]
    (base / first_path).write_text('{"status":"changed"}\n', encoding="utf-8")
    complete, result = evaluate_completion(base)
    assert complete is False
    assert "evidence_hash_mismatch" in result["errors"][0]


def test_incomplete_dimension_blocks_overall_completion(tmp_path: Path) -> None:
    """Any incomplete dimension keeps the aggregate result incomplete."""
    statuses: dict[str, str] = dict.fromkeys(DIMENSIONS, "complete")
    statuses["corpus_custody_recoverability"] = "incomplete"
    complete, result = evaluate_completion(_write_repo(tmp_path, statuses))
    assert complete is False
    assert result["status"] == "incomplete"
    assert (
        "dimension_incomplete:corpus_custody_recoverability:incomplete"
        in result["blockers"]
    )


def test_unselected_proof_is_ineligible(tmp_path: Path) -> None:
    """Dimension proof must also be an explicit evaluator input."""
    base = _write_repo(tmp_path)
    path = base / "evidence/migrations/corpus-legislation-nz/evidence-index.json"
    index = json.loads(path.read_text(encoding="utf-8"))
    index["evaluator_inputs"]["publication_identity_migration"] = []
    path.write_text(json.dumps(index) + "\n", encoding="utf-8")
    complete, result = evaluate_completion(base)
    assert complete is False
    assert (
        "dimension_proof_ineligible:publication_identity_migration"
        in result["blockers"]
    )


def test_main_writes_incomplete_receipt(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """The CLI writes and reports the truthful non-complete state."""
    base = _write_repo(
        tmp_path,
        {
            name: "incomplete" if name == DIMENSIONS[0] else "complete"
            for name in DIMENSIONS
        },
    )
    output = base / "current.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["evaluator", "--root", str(base), "--output", str(output)],
    )
    assert main() == 1
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "incomplete"
    assert "[BLOCKER]" in capsys.readouterr().out


def test_main_reports_index_error(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """The CLI persists and displays an evidence-index validation error."""
    output = tmp_path / "current.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["evaluator", "--root", str(tmp_path), "--output", str(output)],
    )
    assert main() == 1
    assert "[ERROR]" in capsys.readouterr().out


def test_main_complete_exit(
    tmp_path: Path, monkeypatch: MonkeyPatch, capsys: CaptureFixture[str]
) -> None:
    """The CLI returns zero only for four eligible completed dimensions."""
    base = _write_repo(tmp_path)
    output = base / "current.json"
    monkeypatch.setattr(
        sys,
        "argv",
        ["evaluator", "--root", str(base), "--output", str(output)],
    )
    assert main() == 0
    assert "COMPLETE" in capsys.readouterr().out
