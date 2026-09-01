"""Fail-closed evidence-index schema and relationship tests."""

# ruff: noqa: D103, S108

from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).parents[2]))
from tools.legislation_evidence_index import (
    EvidenceIndexError,
    resolve_active_evidence,
    validate_evidence_index,
)

ROOT = Path(__file__).parents[2]
DIMENSIONS = (
    "code_capability_migration",
    "operational_state_migration",
    "corpus_custody_recoverability",
    "publication_identity_migration",
)


def _write(root: Path, relative: str, document: dict[str, Any]) -> str:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, sort_keys=True) + "\n", encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _index(root: Path) -> dict[str, Any]:
    digest = _write(root, "proof/active.json", {"status": "verified"})
    entry = {
        "evidence_id": "active-proof",
        "path": "proof/active.json",
        "sha256": digest,
        "classification": "active",
        "artefact_type": "receipt",
        "proof_kind": "capability_matrix",
        "claim_dimensions": [DIMENSIONS[0]],
        "rationale": "Exact active proof fixture.",
    }
    proof_kinds = {
        DIMENSIONS[1]: "state_verification",
        DIMENSIONS[2]: "recovery_readback",
        DIMENSIONS[3]: "identity_verification",
    }
    entries = [entry]
    proof_ids = {DIMENSIONS[0]: "active-proof"}
    for dimension, proof_kind in proof_kinds.items():
        evidence_id = f"active-{dimension}"
        path = f"proof/{evidence_id}.json"
        entries.append(
            {
                "evidence_id": evidence_id,
                "path": path,
                "sha256": _write(root, path, {"status": "verified"}),
                "classification": "active",
                "artefact_type": "receipt",
                "proof_kind": proof_kind,
                "claim_dimensions": [dimension],
                "rationale": "Dimension-specific active proof fixture.",
            }
        )
        proof_ids[dimension] = evidence_id
    return {
        "schema_version": "archive-govt-nz.legislation-evidence-index/v1",
        "index_id": "test-index-v1",
        "generated_at": "2026-09-02T00:00:00Z",
        "target_repository": "edithatogo/archive-govt-nz",
        "target_commit": "a" * 40,
        "donor_repository": "edithatogo/corpus-legislation-nz",
        "donor_commit": "b" * 40,
        "entries": entries,
        "evaluator_inputs": {
            dimension: [proof_ids[dimension]] for dimension in DIMENSIONS
        },
        "dimensions": {
            dimension: {
                "status": "complete",
                "proof_ids": [proof_ids[dimension]],
                "rationale": "Exact active proof fixture.",
            }
            for dimension in DIMENSIONS
        },
    }


def _prepare(tmp_path: Path, index: dict[str, Any]) -> None:
    (tmp_path / "schemas").mkdir(exist_ok=True)
    shutil.copyfile(
        ROOT / "schemas/legislation-evidence-index-v1.schema.json",
        tmp_path / "schemas/legislation-evidence-index-v1.schema.json",
    )
    _write(tmp_path, "index.json", index)


def _validate(tmp_path: Path, index: dict[str, Any]) -> dict[str, Any]:
    _prepare(tmp_path, index)
    return validate_evidence_index(tmp_path, Path("index.json"))


def test_representative_schema_and_semantic_validation(tmp_path: Path) -> None:
    """The typed fixture and a fixity-bound isolated index both validate."""
    schema = json.loads(
        (ROOT / "schemas/legislation-evidence-index-v1.schema.json").read_text()
    )
    fixture = json.loads(
        (ROOT / "tests/fixtures/legislation-evidence-index-v1.json").read_text()
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(fixture)
    index = _index(tmp_path)
    loaded = _validate(tmp_path, index)
    assert resolve_active_evidence(tmp_path, loaded, "active-proof") == (
        tmp_path / "proof/active.json"
    )


@pytest.mark.parametrize("field", ["evidence_id", "path"])
def test_duplicate_identity_or_path_rejected(tmp_path: Path, field: str) -> None:
    index = _index(tmp_path)
    duplicate = copy.deepcopy(index["entries"][0])
    duplicate["evidence_id"] = "second-proof"
    duplicate["path"] = "proof/second.json"
    duplicate["sha256"] = _write(tmp_path, duplicate["path"], {"status": "verified"})
    duplicate[field] = index["entries"][0][field]
    index["entries"].append(duplicate)
    with pytest.raises(
        EvidenceIndexError,
        match=f"duplicate_evidence_{'id' if field == 'evidence_id' else 'path'}",
    ):
        _validate(tmp_path, index)


@pytest.mark.parametrize(
    "path", ["../escape.json", "/tmp/escape.json", "proof\\bad.json"]
)
def test_unsafe_path_rejected(tmp_path: Path, path: str) -> None:
    index = _index(tmp_path)
    index["entries"][0]["path"] = path
    with pytest.raises(EvidenceIndexError, match="unsafe_evidence_path"):
        _validate(tmp_path, index)


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    """A repo-relative symlink cannot escape the validated repository root."""
    index = _index(tmp_path)
    outside = tmp_path.parent / "outside-proof.json"
    outside.write_text('{"status":"verified"}\n', encoding="utf-8")
    link = tmp_path / "proof/escape.json"
    link.symlink_to(outside)
    index["entries"][0]["path"] = "proof/escape.json"
    index["entries"][0]["sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()
    with pytest.raises(EvidenceIndexError, match="unsafe_evidence_path"):
        _validate(tmp_path, index)


def test_schema_violation_rejected_before_semantic_use(tmp_path: Path) -> None:
    """Malformed index structure fails before any evidence can be selected."""
    index = _index(tmp_path)
    index["unexpected"] = True
    with pytest.raises(EvidenceIndexError, match="schema_validation"):
        _validate(tmp_path, index)


def test_missing_and_hash_mismatched_evidence_rejected(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index["entries"][0]["path"] = "proof/missing.json"
    with pytest.raises(EvidenceIndexError, match="missing_evidence"):
        _validate(tmp_path, index)
    index = _index(tmp_path)
    index["entries"][0]["sha256"] = "0" * 64
    with pytest.raises(EvidenceIndexError, match="evidence_hash_mismatch"):
        _validate(tmp_path, index)


def test_active_label_cannot_hide_invalidated_document(tmp_path: Path) -> None:
    index = _index(tmp_path)
    digest = _write(tmp_path, "proof/active.json", {"status": "invalidated"})
    index["entries"][0]["sha256"] = digest
    with pytest.raises(
        EvidenceIndexError, match="active_evidence_has_non_active_status"
    ):
        _validate(tmp_path, index)


def _add_linked_entry(
    tmp_path: Path, index: dict[str, Any], evidence_id: str, classification: str
) -> dict[str, Any]:
    path = f"proof/{evidence_id}.json"
    digest = _write(tmp_path, path, {"status": classification})
    row: dict[str, Any] = {
        "evidence_id": evidence_id,
        "path": path,
        "sha256": digest,
        "classification": classification,
        "artefact_type": "receipt",
        "proof_kind": "blocker_receipt",
        "claim_dimensions": list(DIMENSIONS),
        "rationale": "Negative or blocked evidence fixture.",
    }
    if classification == "invalidated":
        row["invalidated_by"] = "active-proof"
    elif classification == "superseded":
        row["superseded_by"] = "active-proof"
    index["entries"].append(row)
    return row


def test_dangling_and_cyclic_classification_links_rejected(tmp_path: Path) -> None:
    index = _index(tmp_path)
    row = _add_linked_entry(tmp_path, index, "old-proof", "invalidated")
    row["invalidated_by"] = "absent-proof"
    with pytest.raises(EvidenceIndexError, match="dangling_invalidated_by"):
        _validate(tmp_path, index)

    index = _index(tmp_path)
    first = _add_linked_entry(tmp_path, index, "old-one", "superseded")
    second = _add_linked_entry(tmp_path, index, "old-two", "superseded")
    first["superseded_by"] = "old-two"
    second["superseded_by"] = "old-one"
    with pytest.raises(EvidenceIndexError, match="classification_link_cycle"):
        _validate(tmp_path, index)


def test_classification_links_are_mutually_exclusive(tmp_path: Path) -> None:
    """One historical record cannot be both superseded and invalidated."""
    index = _index(tmp_path)
    row = _add_linked_entry(tmp_path, index, "old-proof", "invalidated")
    row["superseded_by"] = "active-proof"
    with pytest.raises(EvidenceIndexError, match="schema_validation"):
        _validate(tmp_path, index)


@pytest.mark.parametrize(
    "classification",
    ["invalidated", "superseded", "historical", "incomplete", "externally_blocked"],
)
def test_evaluator_inputs_require_active_evidence(
    tmp_path: Path, classification: str
) -> None:
    index = _index(tmp_path)
    row = _add_linked_entry(tmp_path, index, "non-active", classification)
    index["evaluator_inputs"][DIMENSIONS[0]] = [row["evidence_id"]]
    with pytest.raises(EvidenceIndexError, match="non_active_evaluator_input"):
        _validate(tmp_path, index)


@pytest.mark.parametrize("classification", ["invalidated", "superseded", "historical"])
def test_inadmissible_receipts_never_prove_a_dimension(
    tmp_path: Path, classification: str
) -> None:
    index = _index(tmp_path)
    row = _add_linked_entry(tmp_path, index, "bad-proof", classification)
    index["dimensions"][DIMENSIONS[0]] = {
        "status": "incomplete",
        "proof_ids": [row["evidence_id"]],
        "rationale": "Must still reject inadmissible history.",
    }
    with pytest.raises(EvidenceIndexError, match="inadmissible_dimension_proof"):
        _validate(tmp_path, index)


@pytest.mark.parametrize(
    ("dimension_status", "classification"),
    [("incomplete", "incomplete"), ("externally_blocked", "externally_blocked")],
)
def test_negative_dimension_may_cite_matching_non_active_evidence(
    tmp_path: Path, dimension_status: str, classification: str
) -> None:
    index = _index(tmp_path)
    row = _add_linked_entry(tmp_path, index, "negative-proof", classification)
    index["dimensions"][DIMENSIONS[0]] = {
        "status": dimension_status,
        "proof_ids": [row["evidence_id"]],
        "rationale": "The blocker itself is preserved as proof of non-completion.",
    }
    _validate(tmp_path, index)


def test_complete_dimension_requires_active_proof(tmp_path: Path) -> None:
    index = _index(tmp_path)
    row = _add_linked_entry(tmp_path, index, "incomplete-proof", "incomplete")
    index["dimensions"][DIMENSIONS[0]]["proof_ids"] = [row["evidence_id"]]
    with pytest.raises(EvidenceIndexError, match="non_active_complete_proof"):
        _validate(tmp_path, index)


def test_unknown_proof_and_resolver_rejected(tmp_path: Path) -> None:
    index = _index(tmp_path)
    index["dimensions"][DIMENSIONS[0]]["proof_ids"] = ["unknown-proof"]
    with pytest.raises(EvidenceIndexError, match="unknown_dimension_proof"):
        _validate(tmp_path, index)
    valid = _index(tmp_path)
    with pytest.raises(EvidenceIndexError, match="evidence_not_active"):
        resolve_active_evidence(tmp_path, valid, "unknown-proof")


def test_unknown_evaluator_input_rejected(tmp_path: Path) -> None:
    """An evaluator selection must resolve to an indexed evidence identity."""
    index = _index(tmp_path)
    index["evaluator_inputs"][DIMENSIONS[0]] = ["unknown-proof"]
    with pytest.raises(EvidenceIndexError, match="unknown_evaluator_input"):
        _validate(tmp_path, index)


def test_evaluator_input_must_declare_dimension(tmp_path: Path) -> None:
    """An active input cannot be reused outside its declared claim dimension."""
    index = _index(tmp_path)
    index["entries"][0]["claim_dimensions"] = [DIMENSIONS[1]]
    with pytest.raises(EvidenceIndexError, match="evaluator_input_dimension_mismatch"):
        _validate(tmp_path, index)


def test_dimension_proof_must_declare_dimension(tmp_path: Path) -> None:
    """Proof membership is checked independently from evaluator selection."""
    index = _index(tmp_path)
    index["entries"][0]["claim_dimensions"] = [DIMENSIONS[1]]
    index["evaluator_inputs"] = {dimension: [] for dimension in DIMENSIONS}
    with pytest.raises(EvidenceIndexError, match="dimension_proof_mismatch"):
        _validate(tmp_path, index)


def test_negative_proof_classification_must_match_status(tmp_path: Path) -> None:
    """Incomplete evidence cannot be relabelled as an external blocker."""
    index = _index(tmp_path)
    row = _add_linked_entry(tmp_path, index, "wrong-negative", "incomplete")
    index["dimensions"][DIMENSIONS[0]] = {
        "status": "externally_blocked",
        "proof_ids": [row["evidence_id"]],
        "rationale": "Deliberate mismatch.",
    }
    with pytest.raises(
        EvidenceIndexError, match="negative_proof_classification_mismatch"
    ):
        _validate(tmp_path, index)


def test_public_claim_cannot_prove_completed_dimension(tmp_path: Path) -> None:
    """A summary claim cannot bootstrap its own completed status."""
    index = _index(tmp_path)
    index["entries"][0]["artefact_type"] = "public_claim"
    with pytest.raises(
        EvidenceIndexError, match="public_claim_cannot_prove_completion"
    ):
        _validate(tmp_path, index)


def test_complete_proof_kind_is_dimension_specific(tmp_path: Path) -> None:
    """A valid proof for one dimension cannot complete another dimension."""
    index = _index(tmp_path)
    index["entries"][0]["proof_kind"] = "identity_verification"
    with pytest.raises(EvidenceIndexError, match="proof_kind_not_allowed"):
        _validate(tmp_path, index)


def test_negative_dimension_requires_blocker_receipt_kind(tmp_path: Path) -> None:
    """A negative status needs an explicit blocker receipt semantic role."""
    index = _index(tmp_path)
    row = _add_linked_entry(tmp_path, index, "weak-negative", "incomplete")
    row["proof_kind"] = "historical_record"
    index["dimensions"][DIMENSIONS[0]] = {
        "status": "incomplete",
        "proof_ids": [row["evidence_id"]],
        "rationale": "Deliberately weak negative evidence.",
    }
    with pytest.raises(EvidenceIndexError, match="negative_proof_kind_mismatch"):
        _validate(tmp_path, index)
