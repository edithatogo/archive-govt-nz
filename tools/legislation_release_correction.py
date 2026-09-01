"""Prepare a fail-closed GitHub release-note correction without remote mutation."""

# ruff: noqa: E501, PLR2004

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, NoReturn, cast

from jsonschema import Draft202012Validator, FormatChecker

RELEASE_ID = 375146205
RELEASE_TAG = "legislation-cutover-v1.0.0"
RELEASE_NAME = "Legislation consolidation cutover v1.0.0"
RELEASE_URL = (
    "https://github.com/edithatogo/archive-govt-nz/releases/tag/"
    "legislation-cutover-v1.0.0"
)
TAG_COMMIT = "949f6f6abed0cfb668fc5f163129f11e54f335a3"
TARGET_BASELINE_COMMIT = "740389b7420ea7ba7382d40a23ad3e23ba2c680a"
PRE_BODY_SHA256 = "812b5d997a193e37abf21fcf22df7a8ec872efa8407eb29a4f70501e7fb540c6"
PRE_RESPONSE_SHA256 = "ec5769a274441890950fff2c7137b8c11ebe68774671380818d8b18ddbd0587f"
PRE_ETAG = 'W/"099720399f4fb72f4fe3af88937d831ee0ecf15657f54df60aac43acd8b47cd9"'
PRE_RETRIEVED_AT = "2026-09-01T16:27:02Z"
HOSTED_EVIDENCE = [
    {
        "run_id": 32625516235,
        "url": "https://github.com/edithatogo/archive-govt-nz/actions/runs/32625516235",
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "head_sha": "cd338bbce9e0d5d7b033377ac9c3794acb8b93d1",
        "created_at": "2026-08-23T07:25:18Z",
        "updated_at": "2026-08-23T07:25:41Z",
        "jobs": [
            {
                "id": 97160157379,
                "name": "harvest-legislation",
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-08-23T07:25:21Z",
                "completed_at": "2026-08-23T07:25:40Z",
            }
        ],
        "artifacts": [
            {
                "id": 9489568248,
                "name": "legislation-state-32625516235",
                "size_in_bytes": 4958,
                "expired": False,
                "created_at": "2026-08-23T07:25:37Z",
                "expires_at": "2026-11-21T07:25:19Z",
            }
        ],
        "receipt_sha256": "8e585267b113d809cdfc76f85af949838d9693c77fdae1f965aa8c1242358cd0",
    },
    {
        "run_id": 32625566353,
        "url": "https://github.com/edithatogo/archive-govt-nz/actions/runs/32625566353",
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "head_sha": "cd338bbce9e0d5d7b033377ac9c3794acb8b93d1",
        "created_at": "2026-08-23T07:26:27Z",
        "updated_at": "2026-08-23T07:26:45Z",
        "jobs": [
            {
                "id": 97160279865,
                "name": "reconcile",
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-08-23T07:26:30Z",
                "completed_at": "2026-08-23T07:26:44Z",
            }
        ],
        "artifacts": [
            {
                "id": 9489580978,
                "name": "legislation-reconciliation-32625566353",
                "size_in_bytes": 432,
                "expired": False,
                "created_at": "2026-08-23T07:26:42Z",
                "expires_at": "2026-11-21T07:26:28Z",
            }
        ],
        "receipt_sha256": "3c6b03a1bc7279d064e195c701ec2a5a45cdb32069f9352301f48958cb19fd8e",
    },
    {
        "run_id": 32625612739,
        "url": "https://github.com/edithatogo/archive-govt-nz/actions/runs/32625612739",
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "head_sha": "cd338bbce9e0d5d7b033377ac9c3794acb8b93d1",
        "created_at": "2026-08-23T07:27:29Z",
        "updated_at": "2026-08-23T07:27:49Z",
        "jobs": [
            {
                "id": 97160390180,
                "name": "recovery",
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-08-23T07:27:32Z",
                "completed_at": "2026-08-23T07:27:48Z",
            }
        ],
        "artifacts": [
            {
                "id": 9489593885,
                "name": "legislation-recovery-32625612739",
                "size_in_bytes": 2420,
                "expired": False,
                "created_at": "2026-08-23T07:27:46Z",
                "expires_at": "2026-11-21T07:27:30Z",
            }
        ],
        "receipt_sha256": "c429c2120474dac4c3001b9ca341977312fa50602a60f81ba081ca11b8bb739a",
    },
    {
        "run_id": 32625990438,
        "url": "https://github.com/edithatogo/archive-govt-nz/actions/runs/32625990438",
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "head_sha": "abdb814347b78caefa3402bae749a13088d6134f",
        "created_at": "2026-08-23T07:36:01Z",
        "updated_at": "2026-08-23T07:36:29Z",
        "jobs": [
            {
                "id": 97161327754,
                "name": "harvest-legislation",
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-08-23T07:36:04Z",
                "completed_at": "2026-08-23T07:36:28Z",
            }
        ],
        "artifacts": [
            {
                "id": 9489696307,
                "name": "legislation-state-32625990438",
                "size_in_bytes": 21774,
                "expired": False,
                "created_at": "2026-08-23T07:36:25Z",
                "expires_at": "2026-11-21T07:36:02Z",
            }
        ],
        "receipt_sha256": "461709c836dfb14ff21ff65568b34ae6f9c306cf2c224a46f52a71b1b8ba0629",
    },
    {
        "run_id": 32626071396,
        "url": "https://github.com/edithatogo/archive-govt-nz/actions/runs/32626071396",
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "head_sha": "949f6f6abed0cfb668fc5f163129f11e54f335a3",
        "created_at": "2026-08-23T07:37:51Z",
        "updated_at": "2026-08-23T07:38:14Z",
        "jobs": [
            {
                "id": 97161523517,
                "name": "reconcile",
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-08-23T07:37:54Z",
                "completed_at": "2026-08-23T07:38:13Z",
            }
        ],
        "artifacts": [
            {
                "id": 9489716374,
                "name": "legislation-reconciliation-32626071396",
                "size_in_bytes": 434,
                "expired": False,
                "created_at": "2026-08-23T07:38:12Z",
                "expires_at": "2026-11-21T07:37:53Z",
            }
        ],
        "receipt_sha256": "ca6f1d287ede09a85bb11484d7ccc47a5530edf2bae0fe7e5a79efa4cc6cfca3",
    },
    {
        "run_id": 32626113799,
        "url": "https://github.com/edithatogo/archive-govt-nz/actions/runs/32626113799",
        "event": "workflow_dispatch",
        "status": "completed",
        "conclusion": "success",
        "head_sha": "949f6f6abed0cfb668fc5f163129f11e54f335a3",
        "created_at": "2026-08-23T07:38:51Z",
        "updated_at": "2026-08-23T07:39:10Z",
        "jobs": [
            {
                "id": 97161626752,
                "name": "recovery",
                "status": "completed",
                "conclusion": "success",
                "started_at": "2026-08-23T07:38:54Z",
                "completed_at": "2026-08-23T07:39:09Z",
            }
        ],
        "artifacts": [
            {
                "id": 9489726767,
                "name": "legislation-recovery-32626113799",
                "size_in_bytes": 12535,
                "expired": False,
                "created_at": "2026-08-23T07:39:08Z",
                "expires_at": "2026-11-21T07:38:52Z",
            }
        ],
        "receipt_sha256": "bba10c4325901faf122c76abc6915c8299a3ebc677e9975c7d57765f69e6428a",
    },
]
HOSTED_EVIDENCE_SHA256 = (
    "0ec8c03f295bc866039da9a82500f1ca8e27d760d524e57302cad141f6c68d70"
)
BAD_CYCLE_1 = (
    "Cycle 1: harvest 32625516235, reconciliation 32625566353, recovery 32626113799"
)
GOOD_CYCLE_1 = (
    "Cycle 1: harvest 32625516235, reconciliation 32625566353, recovery 32625612739"
)
GOOD_CYCLE_2 = "Cycle 2 (with full-state continuation): harvest 32625990438, reconciliation 32626071396, recovery 32626113799"
ATTESTATION = Path(
    "evidence/migrations/corpus-legislation-nz/shadow-operation-cutover-attestation.json"
)
SCHEMA = Path("schemas/legislation-github-release-correction-v1.schema.json")
POST_READBACK = Path(
    "evidence/migrations/corpus-legislation-nz/cutover-release-provenance/release-post-readback.json"
)
POST_RAW_SHA256 = "dd9a0d71aa8356a5c33cf4134a19d40ff01f38f2a3e3749b33650f7259f2063a"
PREPARED_LIMITATIONS = [
    "No GitHub release mutation was performed by this preparation step.",
    "Applied status requires an independent post-write GitHub API readback.",
]
APPLIED_LIMITATIONS = [
    "The GitHub release body addendum was applied and independently read back; tag, assets, and release identity were unchanged.",
    "No release, tag, asset, DOI, dataset, donor, or external publication was created or altered beyond the release-body addendum.",
]


class ReleaseCorrectionError(ValueError):
    """Release correction inputs cannot support an exact correction."""


def _fail(message: str, cause: BaseException | None = None) -> NoReturn:
    if cause is None:
        raise ReleaseCorrectionError(message)
    raise ReleaseCorrectionError(message) from cause


def _safe(root: Path, relative: Path) -> Path:
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or any("\\" in part for part in relative.parts)
    ):
        _fail(f"unsafe_path:{relative}")
    path = (root / relative).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        _fail(f"unsafe_path:{relative}", exc)
    return path


def _object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        _fail(f"unreadable_json:{path}", exc)
    if not isinstance(value, dict):
        _fail(f"expected_object:{path}")
    return cast("dict[str, Any]", value)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _validate_release(snapshot: dict[str, Any]) -> str:
    expected = {
        "id": RELEASE_ID,
        "tag_name": RELEASE_TAG,
        "name": RELEASE_NAME,
        "html_url": RELEASE_URL,
        "draft": False,
        "prerelease": False,
        "resolved_tag_commit": TAG_COMMIT,
        "immutable": False,
        "assets": [],
        "raw_response_sha256": PRE_RESPONSE_SHA256,
        "etag": PRE_ETAG,
        "retrieved_at": PRE_RETRIEVED_AT,
    }
    if any(snapshot.get(key) != value for key, value in expected.items()):
        _fail("release_identity_mismatch")
    body = snapshot.get("body")
    if not isinstance(body, str):
        _fail("release_body_missing")
    if body.count(BAD_CYCLE_1) != 1:
        _fail("source_claim_drift")
    if body.count(GOOD_CYCLE_2) != 1 or GOOD_CYCLE_1 in body:
        _fail("source_cycle_semantics_drift")
    if "## Correction addendum" in body:
        _fail("correction_already_present")
    if (
        snapshot.get("body_sha256") != PRE_BODY_SHA256
        or _sha(body.encode()) != PRE_BODY_SHA256
    ):
        _fail("source_body_hash_mismatch")
    return body


def _validate_attestation(attestation: dict[str, Any]) -> None:
    if attestation.get("schema_version") != (
        "archive-govt-nz.shadow-operation-cutover-attestation/v1"
    ):
        _fail("attestation_schema_mismatch")
    cycles = attestation.get("observation_cycles")
    if not isinstance(cycles, list) or len(cycles) != 2:
        _fail("attestation_cycles_invalid")
    expected = (
        (1, 32625516235, 32625566353, 32625612739),
        (2, 32625990438, 32626071396, 32626113799),
    )
    observed = tuple(
        (
            row.get("cycle_number"),
            row.get("harvest_run_id"),
            row.get("reconciliation_run_id"),
            row.get("recovery_run_id"),
        )
        for row in cycles
        if isinstance(row, dict)
    )
    if observed != expected:
        _fail("attestation_cycle_identity_mismatch")


def render_addendum() -> str:
    """Render the single correction without rewriting the historical release."""
    return (
        "## Correction addendum — 2026-09-02\n\n"
        "The Cycle 1 recovery run ID in the original release note was incorrect. "
        "The verified Cycle 1 tuple is:\n\n"
        f"- {GOOD_CYCLE_1}\n\n"
        f"Cycle 2 remains unchanged: `{GOOD_CYCLE_2}`. This addendum changes no "
        "tag, release asset, archived donor state, or external publication. The "
        "authoritative source is `evidence/migrations/corpus-legislation-nz/"
        "shadow-operation-cutover-attestation.json`.\n"
    )


def prepare_correction(
    root: Path,
    release_snapshot: Path,
    *,
    issued_at: str,
    addendum_path: Path,
) -> tuple[str, dict[str, Any]]:
    """Authenticate local inputs and return deterministic addendum and receipt."""
    release_file = _safe(root, release_snapshot)
    attestation_file = _safe(root, ATTESTATION)
    local_addendum_file = _safe(root, addendum_path)
    release_bytes = release_file.read_bytes()
    attestation_bytes = attestation_file.read_bytes()
    local_addendum_bytes = local_addendum_file.read_bytes()
    release = _object(release_file)
    attestation = _object(attestation_file)
    body = _validate_release(release)
    _validate_attestation(attestation)
    addendum = render_addendum()
    local_addendum = local_addendum_bytes.decode("utf-8")
    if (
        "2026-09-02" not in local_addendum
        or "32625516235" not in local_addendum
        or "32625566353" not in local_addendum
        or "32625612739" not in local_addendum
        or "32626113799" not in local_addendum
    ):
        _fail("local_addendum_semantics_invalid")
    document = {
        "schema_version": "archive-govt-nz.legislation-github-release-correction/v1",
        "correction_id": "legislation-cutover-v1.0.0-cycle-1-recovery-run",
        "issued_at": issued_at,
        "repository": "edithatogo/archive-govt-nz",
        "target_baseline_commit": TARGET_BASELINE_COMMIT,
        "release": {
            "id": RELEASE_ID,
            "tag": RELEASE_TAG,
            "name": RELEASE_NAME,
            "url": RELEASE_URL,
            "published_at": release["published_at"],
            "draft": False,
            "prerelease": False,
            "is_immutable": bool(release.get("immutable", False)),
            "tag_commit": TAG_COMMIT,
            "asset_count": 0,
            "assets": [],
            "snapshot_path": release_snapshot.as_posix(),
            "normalized_snapshot_sha256": _sha(release_bytes),
            "body_sha256": PRE_BODY_SHA256,
            "original_body": body,
            "pre_readback": {
                "retrieved_at": release["retrieved_at"],
                "etag": release["etag"],
                "raw_response_sha256": release["raw_response_sha256"],
            },
        },
        "hosted_evidence": {
            "verified_at": issued_at,
            "normalized_sha256": HOSTED_EVIDENCE_SHA256,
            "runs": HOSTED_EVIDENCE,
        },
        "correction": {
            "field": "cycle_1.recovery_run_id",
            "incorrect_value": 32626113799,
            "correct_value": 32625612739,
            "unchanged_cycle_2_recovery_run_id": 32626113799,
        },
        "authority": {
            "path": ATTESTATION.as_posix(),
            "sha256": _sha(attestation_bytes),
            "schema_version": attestation["schema_version"],
            "attested_at": attestation["attested_at"],
        },
        "addendum": {
            "local_document_path": addendum_path.as_posix(),
            "local_document_sha256": _sha(local_addendum_bytes),
            "rendered_remote_addendum_sha256": _sha(addendum.encode()),
        },
        "external_action": {"status": "prepared_not_applied"},
        "limitations": PREPARED_LIMITATIONS,
    }
    validate_receipt(root, document)
    return addendum, document


def _validate_local_fixity(root: Path, document: dict[str, Any]) -> None:
    release = cast("dict[str, Any]", document["release"])
    authority = cast("dict[str, Any]", document["authority"])
    addendum = cast("dict[str, Any]", document["addendum"])
    fixity = (
        (release["snapshot_path"], release["normalized_snapshot_sha256"]),
        (authority["path"], authority["sha256"]),
        (addendum["local_document_path"], addendum["local_document_sha256"]),
    )
    for relative, expected_sha in fixity:
        path = _safe(root, Path(relative))
        try:
            observed_sha = _sha(path.read_bytes())
        except OSError as exc:
            _fail(f"unreadable_evidence:{relative}", exc)
        if observed_sha != expected_sha:
            _fail(f"evidence_fixity_mismatch:{relative}")
    rendered_sha = _sha(render_addendum().encode())
    if addendum["rendered_remote_addendum_sha256"] != rendered_sha:
        _fail("rendered_addendum_fixity_mismatch")


def _validate_applied(root: Path, document: dict[str, Any]) -> None:
    if document["limitations"] != APPLIED_LIMITATIONS:
        _fail("applied_limitations_mismatch")
    action = cast("dict[str, Any]", document["external_action"])
    readback = cast("dict[str, Any]", action["readback"])
    post_path = _safe(root, Path(readback["raw_response_path"]))
    try:
        post_bytes = post_path.read_bytes()
    except OSError as exc:
        _fail("unreadable_post_readback", exc)
    if _sha(post_bytes) != readback["raw_response_sha256"]:
        _fail("post_readback_fixity_mismatch")
    post_response = _object(post_path)
    body = readback["body"]
    expected_body = (
        cast("str", document["release"]["original_body"]) + "\n" + render_addendum()
    )
    if body != expected_body:
        _fail("applied_readback_claim_mismatch")
    expected_identity = {
        "id": RELEASE_ID,
        "tag": RELEASE_TAG,
        "name": RELEASE_NAME,
        "url": RELEASE_URL,
        "published_at": document["release"]["published_at"],
        "draft": False,
        "prerelease": False,
        "is_immutable": document["release"]["is_immutable"],
        "tag_commit": TAG_COMMIT,
        "assets": [],
        "body": body,
    }
    if readback["release_identity"] != expected_identity:
        _fail("applied_readback_identity_mismatch")
    raw_identity = {
        "id": post_response.get("id"),
        "tag": post_response.get("tag_name"),
        "name": post_response.get("name"),
        "url": post_response.get("html_url"),
        "published_at": post_response.get("published_at"),
        "draft": post_response.get("draft"),
        "prerelease": post_response.get("prerelease"),
        "is_immutable": post_response.get("immutable"),
        "assets": post_response.get("assets"),
        "body": post_response.get("body"),
    }
    comparable_identity = {
        key: value for key, value in expected_identity.items() if key != "tag_commit"
    }
    if raw_identity != comparable_identity:
        _fail("post_raw_identity_mismatch")
    if _sha(body.encode()) != readback["body_sha256"]:
        _fail("applied_readback_hash_mismatch")
    canonical_response = json.dumps(
        expected_identity, sort_keys=True, separators=(",", ":")
    ).encode()
    if _sha(canonical_response) != readback["normalized_response_sha256"]:
        _fail("applied_response_hash_mismatch")


def validate_receipt(root: Path, document: dict[str, Any]) -> None:
    """Validate the correction receipt schema, fixity, and readback semantics."""
    schema = _object(_safe(root, SCHEMA))
    errors = list(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(
            document
        )
    )
    if errors:
        _fail(f"receipt_schema_invalid:{errors[0].message}")
    _validate_local_fixity(root, document)
    hosted = cast("dict[str, Any]", document["hosted_evidence"])
    canonical_hosted = json.dumps(
        hosted["runs"], sort_keys=True, separators=(",", ":")
    ).encode()
    if (
        hosted["runs"] != HOSTED_EVIDENCE
        or hosted["normalized_sha256"] != _sha(canonical_hosted)
        or hosted["normalized_sha256"] != HOSTED_EVIDENCE_SHA256
    ):
        _fail("hosted_evidence_mismatch")
    action = cast("dict[str, Any]", document["external_action"])
    if action["status"] == "applied_readback_verified":
        _validate_applied(root, document)


__all__ = [
    "ReleaseCorrectionError",
    "prepare_correction",
    "render_addendum",
    "validate_receipt",
]
