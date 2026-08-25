"""Cross-repository medallion vocabulary conformance tests."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts/medallion/v1"
SCHEMA_PATH = CONTRACT / "medallion-conformance.schema.json"
VALID_PATH = CONTRACT / "fixtures/valid.json"
INVALID_GATE_PATH = CONTRACT / "fixtures/invalid-missing-gate.json"
FIELD_LINEAGE_V2 = ROOT / "contracts/medallion/v2"
SCHEMA_SHA256 = "4c1ee81b026c64cf8f962d602cd64441a4a023c132346349c8b27dab0981f10e"
FIELD_LINEAGE_V2_SHA256 = (
    "bf31ee62a3566a8fde512748b79f644e0fab760f60924e4eb9d510d3c1ef6f8a"
)
ALLOWED_TRANSITIONS = {
    ("bronze_b0", "bronze_b1"),
    ("bronze_b1", "bronze_b2"),
    ("bronze_b1", "silver"),
    ("bronze_b2", "silver"),
    ("silver", "gold"),
    ("gold", "platinum"),
}


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _semantic_errors(document: dict[str, Any]) -> list[str]:
    artifacts = {item["artifact_id"]: item for item in document["artifacts"]}
    errors: list[str] = []
    for decision in document["promotion_decisions"]:
        transition = (decision["from_layer"], decision["to_layer"])
        if transition not in ALLOWED_TRANSITIONS:
            errors.append("layer_skip")
        subject = artifacts.get(decision["subject_artifact_id"])
        if subject is None:
            errors.append("unknown_subject")
            continue
        if subject["layer"] != decision["to_layer"]:
            errors.append("target_layer_mismatch")
        if set(subject["lineage"]["input_sha256"]) != set(decision["input_sha256"]):
            errors.append("lineage_checksum_mismatch")
        if decision["status"] == "approved":
            missing = set(decision["required_gate_ids"]) - set(
                decision["passed_gate_ids"]
            )
            if missing:
                errors.append("missing_required_gate")
            if decision["rights_decision"]["status"] != "approved":
                errors.append("rights_not_approved")
            if subject["promotion_status"] != "approved_within_scope":
                errors.append("artifact_not_approved")
    return errors


def test_schema_is_byte_identical_to_v1_contract_digest() -> None:
    """Pin v1 to one byte-identical schema in every repository."""
    assert hashlib.sha256(SCHEMA_PATH.read_bytes()).hexdigest() == SCHEMA_SHA256


def test_valid_fixture_conforms_to_schema_and_semantics() -> None:
    """Accept a fully gated adjacent promotion."""
    schema = _load(SCHEMA_PATH)
    document = _load(VALID_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(document)
    assert _semantic_errors(document) == []


def test_approved_promotion_fails_closed_when_gate_is_missing() -> None:
    """Reject approval when one declared gate is absent."""
    document = _load(INVALID_GATE_PATH)
    Draft202012Validator(_load(SCHEMA_PATH)).validate(document)
    assert "missing_required_gate" in _semantic_errors(document)


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("rights", "rights_not_approved"),
        ("skip", "layer_skip"),
        ("checksum", "lineage_checksum_mismatch"),
    ],
)
def test_approved_promotion_rejects_nonconformant_semantics(
    mutation: str, expected: str
) -> None:
    """Reject rights, transition, and lineage violations."""
    document = copy.deepcopy(_load(VALID_PATH))
    decision = document["promotion_decisions"][0]
    if mutation == "rights":
        decision["rights_decision"]["status"] = "pending"
    elif mutation == "skip":
        decision["from_layer"] = "bronze_b0"
    else:
        decision["input_sha256"] = ["c" * 64]
    assert expected in _semantic_errors(document)


def test_schema_rejects_invalid_checksum_and_non_fail_closed_decision() -> None:
    """Reject malformed fixity and opt-out fail-closed flags."""
    document = copy.deepcopy(_load(VALID_PATH))
    document["artifacts"][0]["sha256"] = "not-a-sha256"
    document["promotion_decisions"][0]["fail_closed"] = False
    errors = list(Draft202012Validator(_load(SCHEMA_PATH)).iter_errors(document))
    assert len(errors) == 2


def test_v2_field_lineage_fixture_is_versioned_and_fail_closed() -> None:
    """Pin v2 bytes and reject an unversioned transformation."""
    assert (
        hashlib.sha256(
            (FIELD_LINEAGE_V2 / "field-lineage.schema.json").read_bytes()
        ).hexdigest()
        == FIELD_LINEAGE_V2_SHA256
    )
    schema = _load(FIELD_LINEAGE_V2 / "field-lineage.schema.json")
    valid = _load(FIELD_LINEAGE_V2 / "fixtures/valid-field-lineage.json")
    invalid = _load(FIELD_LINEAGE_V2 / "fixtures/invalid-unversioned-code.json")
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(valid)
    errors = list(Draft202012Validator(schema).iter_errors(invalid))
    assert len(errors) == 1
    assert list(errors[0].path)[-1] == "code_version"
