"""Fail-closed GitHub release correction preparation tests."""

# ruff: noqa: ANN401, D103, E501, PT018, S108

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
from tools.legislation_release_correction import (
    BAD_CYCLE_1,
    GOOD_CYCLE_1,
    GOOD_CYCLE_2,
    ReleaseCorrectionError,
    prepare_correction,
    render_addendum,
    validate_receipt,
)

ROOT = Path(__file__).parents[2]
SNAPSHOT = Path("evidence/live-release.json")
ADDENDUM = Path(
    "docs/migrations/corpus-legislation-nz/releases/legislation-cutover-v1.0.0-addendum.md"
)


def _release() -> dict[str, Any]:
    release = {
        "id": 375146205,
        "tag_name": "legislation-cutover-v1.0.0",
        "name": "Legislation consolidation cutover v1.0.0",
        "html_url": "https://github.com/edithatogo/archive-govt-nz/releases/tag/legislation-cutover-v1.0.0",
        "draft": False,
        "prerelease": False,
        "immutable": False,
        "published_at": "2026-08-23T07:41:01Z",
        "retrieved_at": "2026-09-01T16:27:02Z",
        "etag": 'W/"099720399f4fb72f4fe3af88937d831ee0ecf15657f54df60aac43acd8b47cd9"',
        "raw_response_sha256": "ec5769a274441890950fff2c7137b8c11ebe68774671380818d8b18ddbd0587f",
        "assets": [],
        "resolved_tag_commit": "949f6f6abed0cfb668fc5f163129f11e54f335a3",
        "body": "Formal cutover release for the corpus-legislation-nz consolidation programme (epic #131).\n\nEvidence:\n- 2 successful target observation cycles (2026-08-23), each: bounded harvest -> reconciliation (consistent) -> recovery drill (verified):\n  - Cycle 1: harvest 32625516235, reconciliation 32625566353, recovery 32626113799\n  - Cycle 2 (with full-state continuation): harvest 32625990438, reconciliation 32626071396, recovery 32626113799\n- Donor repository edithatogo/corpus-legislation-nz archived 2026-08-23T07:40:08Z after the contract postcondition (2 observation cycles) was satisfied\n- Attestation: evidence/migrations/corpus-legislation-nz/shadow-operation-cutover-attestation.json\n- Gate authorization: evidence/migrations/corpus-legislation-nz/operational-gate-authorization.json\n\nSupersedes invalidated receipts (observation-receipt, cutover-receipt from PR #124 era).\n",
    }
    release["body_sha256"] = hashlib.sha256(release["body"].encode()).hexdigest()
    return release


def _attestation() -> dict[str, Any]:
    return {
        "schema_version": "archive-govt-nz.shadow-operation-cutover-attestation/v1",
        "attested_at": "2026-08-23T07:40:30Z",
        "observation_cycles": [
            {
                "cycle_number": 1,
                "harvest_run_id": 32625516235,
                "reconciliation_run_id": 32625566353,
                "recovery_run_id": 32625612739,
            },
            {
                "cycle_number": 2,
                "harvest_run_id": 32625990438,
                "reconciliation_run_id": 32626071396,
                "recovery_run_id": 32626113799,
            },
        ],
    }


def _root(tmp_path: Path, release: Any = None, attestation: Any = None) -> Path:
    schema = tmp_path / "schemas/legislation-github-release-correction-v1.schema.json"
    schema.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / schema.relative_to(tmp_path), schema)
    snapshot = tmp_path / SNAPSHOT
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    snapshot.write_text(json.dumps(_release() if release is None else release) + "\n")
    authority = (
        tmp_path
        / "evidence/migrations/corpus-legislation-nz/shadow-operation-cutover-attestation.json"
    )
    authority.parent.mkdir(parents=True, exist_ok=True)
    authority.write_text(
        json.dumps(_attestation() if attestation is None else attestation) + "\n"
    )
    local_addendum = tmp_path / ADDENDUM
    local_addendum.parent.mkdir(parents=True, exist_ok=True)
    local_addendum.write_text(
        "Date 2026-09-02; cycles 32625516235 32625566353 32625612739 32626113799\n"
    )
    post = (
        tmp_path
        / "evidence/migrations/corpus-legislation-nz/cutover-release-provenance/release-post-readback.json"
    )
    post.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(
        ROOT
        / "evidence/migrations/corpus-legislation-nz/cutover-release-provenance/release-post-readback.json",
        post,
    )
    return tmp_path


def _prepare(root: Path) -> tuple[str, dict[str, Any]]:
    return prepare_correction(
        root,
        SNAPSHOT,
        issued_at="2026-09-02T00:00:00Z",
        addendum_path=ADDENDUM,
    )


def test_schema_fixture_and_deterministic_preparation(tmp_path: Path) -> None:
    schema = json.loads(
        (
            ROOT / "schemas/legislation-github-release-correction-v1.schema.json"
        ).read_text()
    )
    fixture = json.loads(
        (
            ROOT / "tests/fixtures/legislation-github-release-correction-v1.json"
        ).read_text()
    )
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(fixture)
    root = _root(tmp_path)
    first = _prepare(root)
    second = _prepare(root)
    assert first == second
    addendum, receipt = first
    assert GOOD_CYCLE_1 in addendum and GOOD_CYCLE_2 in addendum
    assert BAD_CYCLE_1 not in addendum
    assert receipt["external_action"] == {"status": "prepared_not_applied"}
    assert (
        receipt["addendum"]["rendered_remote_addendum_sha256"]
        == hashlib.sha256(addendum.encode()).hexdigest()
    )


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("id", 1),
        ("tag_name", "wrong"),
        ("name", "wrong"),
        ("html_url", "wrong"),
        ("draft", True),
        ("prerelease", True),
        ("resolved_tag_commit", "0" * 40),
    ],
)
def test_release_identity_mismatch_rejected(
    tmp_path: Path, key: str, value: object
) -> None:
    release = _release()
    release[key] = value
    with pytest.raises(ReleaseCorrectionError, match="release_identity_mismatch"):
        _prepare(_root(tmp_path, release))


def test_missing_or_drifted_release_body_rejected(tmp_path: Path) -> None:
    release = _release()
    release["body"] = None
    with pytest.raises(ReleaseCorrectionError, match="release_body_missing"):
        _prepare(_root(tmp_path, release))
    for body, error in [
        (GOOD_CYCLE_2, "source_claim_drift"),
        (f"{BAD_CYCLE_1}\n{BAD_CYCLE_1}\n{GOOD_CYCLE_2}", "source_claim_drift"),
        (f"{BAD_CYCLE_1}\n", "source_cycle_semantics_drift"),
        (
            f"{BAD_CYCLE_1}\n{GOOD_CYCLE_1}\n{GOOD_CYCLE_2}",
            "source_cycle_semantics_drift",
        ),
        (
            f"{BAD_CYCLE_1}\n{GOOD_CYCLE_2}\n## Correction addendum",
            "correction_already_present",
        ),
    ]:
        release = _release()
        release["body"] = body
        with pytest.raises(ReleaseCorrectionError, match=error):
            _prepare(_root(tmp_path, release))


def test_attestation_failures_rejected(tmp_path: Path) -> None:
    att = _attestation()
    att["schema_version"] = "wrong"
    with pytest.raises(ReleaseCorrectionError, match="attestation_schema_mismatch"):
        _prepare(_root(tmp_path, attestation=att))
    att = _attestation()
    att["observation_cycles"] = []
    with pytest.raises(ReleaseCorrectionError, match="attestation_cycles_invalid"):
        _prepare(_root(tmp_path, attestation=att))
    att = _attestation()
    att["observation_cycles"][0]["recovery_run_id"] = 32626113799
    with pytest.raises(
        ReleaseCorrectionError, match="attestation_cycle_identity_mismatch"
    ):
        _prepare(_root(tmp_path, attestation=att))
    att = _attestation()
    att["observation_cycles"][0] = "bad"
    with pytest.raises(
        ReleaseCorrectionError, match="attestation_cycle_identity_mismatch"
    ):
        _prepare(_root(tmp_path, attestation=att))


@pytest.mark.parametrize(
    "relative",
    [Path("../outside.json"), Path("/tmp/outside.json"), Path(r"evidence\..\outside")],
)
def test_unsafe_paths_rejected(tmp_path: Path, relative: Path) -> None:
    with pytest.raises(ReleaseCorrectionError, match="unsafe_path"):
        prepare_correction(
            tmp_path, relative, issued_at="2026-09-02T00:00:00Z", addendum_path=ADDENDUM
        )


def test_symlink_escape_rejected(tmp_path: Path) -> None:
    root = _root(tmp_path)
    outside = tmp_path.parent / "outside-release.json"
    outside.write_text(json.dumps(_release()))
    (root / SNAPSHOT).unlink()
    (root / SNAPSHOT).symlink_to(outside)
    with pytest.raises(ReleaseCorrectionError, match="unsafe_path"):
        _prepare(root)


def test_malformed_json_inputs_rejected(tmp_path: Path) -> None:
    root = _root(tmp_path)
    (root / SNAPSHOT).write_text("[")
    with pytest.raises(ReleaseCorrectionError, match="unreadable_json"):
        _prepare(root)
    root = _root(tmp_path, release=[])
    with pytest.raises(ReleaseCorrectionError, match="expected_object"):
        _prepare(root)


def _applied(root: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    document = copy.deepcopy(receipt)
    body = document["release"]["original_body"] + "\n" + render_addendum()
    document["external_action"] = {
        "status": "applied_readback_verified",
        "applied_at": "2026-09-02T01:00:00Z",
        "operation_id": "github-release-patch-1",
        "readback": {
            "retrieved_at": "2026-09-02T01:01:00Z",
            "etag": 'W/"post-readback"',
            "body_sha256": hashlib.sha256(body.encode()).hexdigest(),
            "body": body,
            "release_identity": {
                "id": 375146205,
                "tag": "legislation-cutover-v1.0.0",
                "name": "Legislation consolidation cutover v1.0.0",
                "url": "https://github.com/edithatogo/archive-govt-nz/releases/tag/legislation-cutover-v1.0.0",
                "published_at": document["release"]["published_at"],
                "draft": False,
                "prerelease": False,
                "is_immutable": document["release"]["is_immutable"],
                "tag_commit": "949f6f6abed0cfb668fc5f163129f11e54f335a3",
                "assets": [],
                "body": body,
            },
        },
    }
    identity = document["external_action"]["readback"]["release_identity"]
    document["external_action"]["readback"]["normalized_response_sha256"] = (
        hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    document["external_action"]["readback"]["raw_response_path"] = (
        "evidence/migrations/corpus-legislation-nz/cutover-release-provenance/release-post-readback.json"
    )
    document["external_action"]["readback"]["raw_response_sha256"] = (
        "dd9a0d71aa8356a5c33cf4134a19d40ff01f38f2a3e3749b33650f7259f2063a"
    )
    document["limitations"] = [
        "The GitHub release body addendum was applied and independently read back; tag, assets, and release identity were unchanged.",
        "No release, tag, asset, DOI, dataset, donor, or external publication was created or altered beyond the release-body addendum.",
    ]
    validate_receipt(root, document)
    return document


def test_applied_readback_requires_exact_claims_and_hash(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    applied = _applied(root, receipt)
    bad = copy.deepcopy(applied)
    bad["external_action"]["readback"]["body"] = GOOD_CYCLE_1
    with pytest.raises(ReleaseCorrectionError, match="applied_readback_claim_mismatch"):
        validate_receipt(root, bad)
    bad = copy.deepcopy(applied)
    bad["external_action"]["readback"]["body_sha256"] = "0" * 64
    with pytest.raises(ReleaseCorrectionError, match="applied_readback_hash_mismatch"):
        validate_receipt(root, bad)


def test_schema_forbids_fabricated_remote_success(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    receipt["external_action"]["operation_id"] = "fabricated"
    with pytest.raises(ReleaseCorrectionError, match="receipt_schema_invalid"):
        validate_receipt(root, receipt)
    receipt["external_action"] = {"status": "blocked", "reason": "API unavailable"}
    validate_receipt(root, receipt)


def test_hash_and_local_addendum_drift_rejected(tmp_path: Path) -> None:
    release = _release()
    release["body_sha256"] = "0" * 64
    with pytest.raises(ReleaseCorrectionError, match="source_body_hash_mismatch"):
        _prepare(_root(tmp_path, release))
    root = _root(tmp_path)
    (root / ADDENDUM).write_text("2026-09-02 incomplete\n")
    with pytest.raises(
        ReleaseCorrectionError, match="local_addendum_semantics_invalid"
    ):
        _prepare(root)


def test_hosted_evidence_is_exact_and_fixity_bound(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    assert len(receipt["hosted_evidence"]["runs"]) == 6
    assert all(
        not run["artifacts"][0]["expired"] for run in receipt["hosted_evidence"]["runs"]
    )
    bad = copy.deepcopy(receipt)
    bad["hosted_evidence"]["runs"][2]["run_id"] = 32626113799
    with pytest.raises(ReleaseCorrectionError, match="hosted_evidence_mismatch"):
        validate_receipt(root, bad)
    bad = copy.deepcopy(receipt)
    bad["hosted_evidence"]["normalized_sha256"] = "0" * 64
    with pytest.raises(ReleaseCorrectionError, match="receipt_schema_invalid"):
        validate_receipt(root, bad)


def test_applied_identity_and_response_hash_drift_rejected(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    applied = _applied(root, receipt)
    bad = copy.deepcopy(applied)
    bad["external_action"]["readback"]["release_identity"]["name"] = "wrong"
    with pytest.raises(ReleaseCorrectionError, match="receipt_schema_invalid"):
        validate_receipt(root, bad)
    bad = copy.deepcopy(applied)
    bad["external_action"]["readback"]["release_identity"]["is_immutable"] = True
    with pytest.raises(
        ReleaseCorrectionError, match="applied_readback_identity_mismatch"
    ):
        validate_receipt(root, bad)
    bad = copy.deepcopy(applied)
    bad["external_action"]["readback"]["normalized_response_sha256"] = "0" * 64
    with pytest.raises(ReleaseCorrectionError, match="applied_response_hash_mismatch"):
        validate_receipt(root, bad)


@pytest.mark.parametrize(
    ("section", "path_key"),
    [
        ("release", "snapshot_path"),
        ("authority", "path"),
        ("addendum", "local_document_path"),
    ],
)
def test_receipt_rejects_governed_file_drift(
    tmp_path: Path, section: str, path_key: str
) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    (root / receipt[section][path_key]).write_bytes(b"drift")
    with pytest.raises(ReleaseCorrectionError, match="evidence_fixity_mismatch"):
        validate_receipt(root, receipt)


def test_receipt_rejects_rendered_addendum_hash_drift(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    receipt["addendum"]["rendered_remote_addendum_sha256"] = "0" * 64
    with pytest.raises(
        ReleaseCorrectionError, match="rendered_addendum_fixity_mismatch"
    ):
        validate_receipt(root, receipt)


def test_applied_receipt_rejects_post_snapshot_and_limitations_drift(
    tmp_path: Path,
) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    applied = _applied(root, receipt)
    bad = copy.deepcopy(applied)
    bad["limitations"] = receipt["limitations"]
    with pytest.raises(ReleaseCorrectionError, match="receipt_schema_invalid"):
        validate_receipt(root, bad)
    post = root / applied["external_action"]["readback"]["raw_response_path"]
    post.write_bytes(b"drift")
    with pytest.raises(ReleaseCorrectionError, match="post_readback_fixity_mismatch"):
        validate_receipt(root, applied)


def test_applied_receipt_rejects_raw_response_identity_drift(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    applied = _applied(root, receipt)
    post = root / applied["external_action"]["readback"]["raw_response_path"]
    raw = json.loads(post.read_text())
    raw["name"] = "wrong"
    payload = json.dumps(raw, indent=2).encode() + b"\n"
    post.write_bytes(payload)
    applied["external_action"]["readback"]["raw_response_sha256"] = hashlib.sha256(
        payload
    ).hexdigest()
    schema = json.loads(
        (
            root / "schemas/legislation-github-release-correction-v1.schema.json"
        ).read_text()
    )
    schema["properties"]["external_action"]["oneOf"][1]["properties"]["readback"][
        "properties"
    ]["raw_response_sha256"] = {"pattern": "^[0-9a-f]{64}$"}
    (root / "schemas/legislation-github-release-correction-v1.schema.json").write_text(
        json.dumps(schema)
    )
    with pytest.raises(ReleaseCorrectionError, match="post_raw_identity_mismatch"):
        validate_receipt(root, applied)


def test_receipt_rejects_unreadable_governed_evidence(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    (root / receipt["authority"]["path"]).unlink()
    with pytest.raises(ReleaseCorrectionError, match="unreadable_evidence"):
        validate_receipt(root, receipt)


def test_applied_receipt_rejects_unreadable_post_snapshot(tmp_path: Path) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    applied = _applied(root, receipt)
    (root / applied["external_action"]["readback"]["raw_response_path"]).unlink()
    with pytest.raises(ReleaseCorrectionError, match="unreadable_post_readback"):
        validate_receipt(root, applied)


def test_applied_semantics_reject_limitations_when_schema_is_relaxed(
    tmp_path: Path,
) -> None:
    root = _root(tmp_path)
    _, receipt = _prepare(root)
    applied = _applied(root, receipt)
    applied["limitations"] = ["misleading"]
    schema_path = root / "schemas/legislation-github-release-correction-v1.schema.json"
    schema = json.loads(schema_path.read_text())
    schema.pop("allOf")
    schema_path.write_text(json.dumps(schema))
    with pytest.raises(ReleaseCorrectionError, match="applied_limitations_mismatch"):
        validate_receipt(root, applied)
