"""Fail-closed validation and resolution for legislation evidence indexes."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, NoReturn, cast

from jsonschema import Draft202012Validator, FormatChecker

DEFAULT_INDEX = Path("evidence/migrations/corpus-legislation-nz/evidence-index.json")
DEFAULT_SCHEMA = Path("schemas/legislation-evidence-index-v1.schema.json")
NON_ACTIVE = {
    "superseded",
    "invalidated",
    "historical",
    "incomplete",
    "externally_blocked",
}
COMPLETE_PROOF_KINDS = {
    "code_capability_migration": {"capability_matrix", "contract", "evaluator"},
    "operational_state_migration": {
        "state_verification",
        "state_merge",
        "operational_run",
    },
    "corpus_custody_recoverability": {"durable_package", "recovery_readback"},
    "publication_identity_migration": {
        "publication_readback",
        "identity_verification",
    },
}


class EvidenceIndexError(ValueError):
    """An evidence index cannot safely authorize completion proof."""


def _fail(message: str, cause: BaseException | None = None) -> NoReturn:
    """Raise one consistently formed validation error."""
    if cause is None:
        raise EvidenceIndexError(message)
    raise EvidenceIndexError(message) from cause


def _load_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"unreadable_json:{path}", exc)
    if not isinstance(value, dict):
        _fail(f"expected_object:{path}")
    return cast("dict[str, Any]", value)


def _safe_path(root: Path, raw: object) -> Path:
    if not isinstance(raw, str) or not raw:  # pragma: no cover - schema precondition
        _fail("invalid_evidence_path")
    relative = Path(raw)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or "\\" in raw
        or raw != relative.as_posix()
    ):
        _fail(f"unsafe_evidence_path:{raw}")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        _fail(f"unsafe_evidence_path:{raw}", exc)
    return resolved


def _reject_cycles(entries: dict[str, dict[str, Any]]) -> None:
    for origin in entries:
        seen: set[str] = set()
        current = origin
        while True:
            if current in seen:
                _fail(f"classification_link_cycle:{origin}")
            seen.add(current)
            entry = entries[current]
            target = entry.get("superseded_by") or entry.get("invalidated_by")
            if target is None:
                break
            current = cast("str", target)


def validate_evidence_index(  # noqa: C901, PLR0912, PLR0915
    root: Path, index_path: Path = DEFAULT_INDEX, schema_path: Path = DEFAULT_SCHEMA
) -> dict[str, Any]:
    """Validate schema, fixity, relationships, and active evaluator inputs."""
    index = _load_object(root / index_path)
    schema = _load_object(root / schema_path)
    errors = sorted(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(index),
        key=lambda error: list(error.absolute_path),
    )
    if errors:
        _fail(f"schema_validation:{errors[0].message}")

    rows = cast("list[dict[str, Any]]", index["entries"])
    entries: dict[str, dict[str, Any]] = {}
    paths: set[str] = set()
    for row in rows:
        evidence_id = cast("str", row["evidence_id"])
        raw_path = cast("str", row["path"])
        if evidence_id in entries:
            _fail(f"duplicate_evidence_id:{evidence_id}")
        if raw_path in paths:
            _fail(f"duplicate_evidence_path:{raw_path}")
        entries[evidence_id] = row
        paths.add(raw_path)

    for evidence_id, row in entries.items():
        for relation in ("superseded_by", "invalidated_by"):
            target = row.get(relation)
            if target is not None and target not in entries:
                _fail(f"dangling_{relation}:{evidence_id}:{target}")
        evidence_path = _safe_path(root, row["path"])
        try:
            evidence_bytes = evidence_path.read_bytes()
        except OSError as exc:
            _fail(f"missing_evidence:{row['path']}", exc)
        observed = hashlib.sha256(evidence_bytes).hexdigest()
        if observed != row["sha256"]:
            _fail(f"evidence_hash_mismatch:{evidence_id}")
        if row["classification"] == "active" and evidence_path.suffix == ".json":
            document = _load_object(evidence_path)
            if document.get("status") in NON_ACTIVE:
                _fail(f"active_evidence_has_non_active_status:{evidence_id}")

    _reject_cycles(entries)
    evaluator_selected: set[str] = set()
    for evidence_ids in cast(
        "dict[str, list[str]]", index["evaluator_inputs"]
    ).values():
        evaluator_selected.update(evidence_ids)
    for evidence_id in evaluator_selected:
        if evidence_id not in entries:
            _fail(f"unknown_evaluator_input:{evidence_id}")
        if entries[evidence_id]["classification"] != "active":
            _fail(f"non_active_evaluator_input:{evidence_id}")
    for dimension, evidence_ids in cast(
        "dict[str, list[str]]", index["evaluator_inputs"]
    ).items():
        for evidence_id in evidence_ids:
            if dimension not in entries[evidence_id]["claim_dimensions"]:
                _fail(f"evaluator_input_dimension_mismatch:{dimension}:{evidence_id}")
    for dimension, result in cast(
        "dict[str, dict[str, Any]]", index["dimensions"]
    ).items():
        status = cast("str", result["status"])
        for evidence_id in cast("list[str]", result["proof_ids"]):
            if evidence_id not in entries:
                _fail(f"unknown_dimension_proof:{evidence_id}")
            classification = cast("str", entries[evidence_id]["classification"])
            if dimension not in entries[evidence_id]["claim_dimensions"]:
                _fail(f"dimension_proof_mismatch:{dimension}:{evidence_id}")
            if classification in {"invalidated", "superseded", "historical"}:
                _fail(f"inadmissible_dimension_proof:{evidence_id}")
            if status == "complete" and classification != "active":
                _fail(f"non_active_complete_proof:{evidence_id}")
            if status not in {"complete", classification}:
                _fail(f"negative_proof_classification_mismatch:{evidence_id}")
            if (
                status == "complete"
                and entries[evidence_id]["artefact_type"] == "public_claim"
            ):
                _fail(f"public_claim_cannot_prove_completion:{evidence_id}")
            proof_kind = entries[evidence_id]["proof_kind"]
            if (
                status == "complete"
                and proof_kind not in COMPLETE_PROOF_KINDS[dimension]
            ):
                _fail(f"proof_kind_not_allowed:{dimension}:{evidence_id}")
            if status != "complete" and proof_kind != "blocker_receipt":
                _fail(f"negative_proof_kind_mismatch:{dimension}:{evidence_id}")
    return index


def resolve_active_evidence(
    root: Path, index: dict[str, Any], evidence_id: str
) -> Path:
    """Resolve one already validated active evidence ID to a safe local path."""
    matches = [
        row
        for row in cast("list[dict[str, Any]]", index.get("entries", []))
        if row.get("evidence_id") == evidence_id
    ]
    if len(matches) != 1 or matches[0].get("classification") != "active":
        _fail(f"evidence_not_active:{evidence_id}")
    return _safe_path(root, matches[0]["path"])


__all__ = [
    "DEFAULT_INDEX",
    "EvidenceIndexError",
    "resolve_active_evidence",
    "validate_evidence_index",
]
