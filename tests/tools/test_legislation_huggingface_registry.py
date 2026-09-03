"""Validate the governed legislation Hugging Face identity registry."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "schemas/legislation-huggingface-registry-v2.schema.json"
REGISTRY_PATH = ROOT / "config/legislation/huggingface-publication-registry.json"
EVIDENCE_ROOT = ROOT / "evidence/migrations/corpus-legislation-nz"


def _load(path: Path) -> Any:  # noqa: ANN401
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_registry_schema_and_document_are_valid() -> None:
    """The checked-in schema and registry must validate together."""
    schema = _load(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(_load(REGISTRY_PATH))


def test_registry_has_exact_non_conflicting_identity_roles() -> None:
    """The existing identities have one distinct governed role each."""
    identities = {item["slug"]: item for item in _load(REGISTRY_PATH)["identities"]}
    assert set(identities) == {
        "edithatogo/corpus-legislation-nz",
        "edithatogo/corpus-legislation-nz-historical",
        "edithatogo/nz-legislation-corpus",
    }
    assert {item["role"] for item in identities.values()} == {
        "canonical_living_dataset",
        "historical_superseded_operational_dataset",
        "immutable_doi_snapshot",
    }
    assert identities["edithatogo/corpus-legislation-nz"]["mutable"] is True
    assert all(
        not identities[slug]["mutable"]
        for slug in (
            "edithatogo/corpus-legislation-nz-historical",
            "edithatogo/nz-legislation-corpus",
        )
    )


def test_registry_is_bound_to_canonical_state_and_durable_package() -> None:
    """State roots and counts must reproduce Prompt 04 and Prompt 09 evidence."""
    registry = _load(REGISTRY_PATH)
    receipt = _load(
        EVIDENCE_ROOT / "final-state-merge/execution-02/final-state-merge-receipt.json"
    )
    durable = _load(EVIDENCE_ROOT / "durable-state/validation.json")
    assert registry["state"]["manifest_sha256"] == receipt["output"]["manifest_sha256"]
    assert (
        registry["state"]["inventory_sha256"] == receipt["output"]["inventory_sha256"]
    )
    assert registry["state"]["work_count"] == receipt["output"]["work_ids"]
    assert registry["state"]["record_count"] == receipt["output"]["records"]
    assert registry["state"]["object_count"] == receipt["output"]["objects"]
    assert (
        registry["state"]["durable_package_sha256"]
        == durable["canonical_package"]["package_sha256"]
    )


def test_registry_is_bound_to_coverage_and_publication_authority() -> None:
    """Coverage remains bounded and publication does not fabricate Prompt 13 proof."""
    registry = _load(REGISTRY_PATH)
    coverage = _load(
        EVIDENCE_ROOT / "historical-coverage/historical-coverage-report.json"
    )
    prompt13 = (
        EVIDENCE_ROOT / "500-work-operational-proof/500-work-target-revalidation.json"
    )
    assert (
        registry["coverage"]["candidate_ids"]
        == coverage["candidate_inventory"]["candidate_ids"]
    )
    assert (
        registry["coverage"]["candidate_inventory_sha256"]
        == coverage["candidate_inventory"]["candidate_sha256"]
    )
    assert registry["publication_gate"]["prompt13_receipt_sha256"] == _sha256(prompt13)
    assert _load(prompt13)["dispatch_performed"] is False
    assert registry["publication_gate"] == {
        "status": "published_verified",
        "remote_write_authorized": True,
        "authorization_date": "2026-09-03",
        "authorization_decision_id": (
            "archive-govt-nz-hf-publication-20260903-selected-552-v1"
        ),
        "authorization_source": (
            "accountable maintainer authorization in the canonical programme "
            "thread on 2026-09-03"
        ),
        "candidate_manifest_sha256": (
            "fb3caa39ffd3da9204f01ebd764237d276460dc61493eb809b7e207d17813646"
        ),
        "approved_package_sha256": (
            "2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c"
        ),
        "permitted_files": [
            "durable-state/v1/2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c/canonical-state.zip",
            "durable-state/v1/2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c/metadata.json",
            "README.md",
            "RIGHTS.md",
        ],
        "prompt13_operational_proof": False,
        "prompt13_receipt_sha256": _sha256(prompt13),
        "payload_rights": "approved_public_selected_552",
        "durable_package_revision": "ae4da4ef0446f68fddd8f53279ecb1245f1529b9",
        "metadata_revision": "04688f12dd687618e2085ae31f9b8a4a50a88b16",
        "readback_receipt_path": (
            "evidence/migrations/corpus-legislation-nz/huggingface-publication/"
            "publication-readback-20260903.json"
        ),
        "readback_receipt_sha256": _sha256(
            EVIDENCE_ROOT / "huggingface-publication/publication-readback-20260903.json"
        ),
    }


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("target_commit", "main"),
        ("authority_repository", "edithatogo/corpus-legislation-nz"),
    ],
)
def test_registry_rejects_unpinned_or_donor_origin(field: str, value: str) -> None:
    """Origin authority and revisions cannot drift to donor or floating values."""
    registry = copy.deepcopy(_load(REGISTRY_PATH))
    registry["origin"][field] = value
    with pytest.raises(ValidationError):
        Draft202012Validator(_load(SCHEMA_PATH)).validate(registry)


def test_registry_rejects_withdrawn_authority_and_aggregate_count() -> None:
    """Published state cannot lose its authority or sum unlike surfaces."""
    registry = copy.deepcopy(_load(REGISTRY_PATH))
    registry["publication_gate"]["remote_write_authorized"] = False
    registry["coverage"]["published_counts_aggregate"] = 6609
    errors = list(Draft202012Validator(_load(SCHEMA_PATH)).iter_errors(registry))
    assert len(errors) == 2


@pytest.mark.parametrize(
    "slug",
    [
        "edithatogo/corpus-legislation-nz-historical",
        "edithatogo/nz-legislation-corpus",
    ],
)
def test_registry_rejects_broadened_rights_approval(slug: str) -> None:
    """The selected-state approval cannot be assigned to preserved identities."""
    registry = copy.deepcopy(_load(REGISTRY_PATH))
    identity = next(item for item in registry["identities"] if item["slug"] == slug)
    identity["rights_status"] = "approved_public_selected_552"
    with pytest.raises(ValidationError):
        Draft202012Validator(_load(SCHEMA_PATH)).validate(registry)


def test_registry_rejects_canonical_rights_approval_downgrade() -> None:
    """Published canonical state cannot silently lose its bound approval."""
    registry = copy.deepcopy(_load(REGISTRY_PATH))
    identity = next(
        item
        for item in registry["identities"]
        if item["slug"] == "edithatogo/corpus-legislation-nz"
    )
    identity["rights_status"] = "source_specific_review_required"
    with pytest.raises(ValidationError):
        Draft202012Validator(_load(SCHEMA_PATH)).validate(registry)


def test_registry_revisions_match_superseding_and_historical_observations() -> None:
    """Canonical publication supersedes only the mutable identity observation."""
    registry = _load(REGISTRY_PATH)
    report = _load(
        EVIDENCE_ROOT / "historical-coverage/historical-coverage-report.json"
    )
    surfaces = {
        item["surface_id"].removeprefix("huggingface:"): item
        for item in report["publication_surfaces"]["surfaces"]
        if item["platform"] == "huggingface"
    }
    for identity in registry["identities"]:
        if identity["slug"] == "edithatogo/corpus-legislation-nz":
            receipt = _load(
                EVIDENCE_ROOT
                / "huggingface-publication/publication-readback-20260903.json"
            )
            api = receipt["anonymous_exact_revision_readback"]["api"]
            assert identity["observed_revision"] == api["returned_revision"]
            assert identity["file_count"] == api["file_count"]
            assert identity["published_row_count"] is None
        else:
            observed = surfaces[identity["slug"]]
            assert identity["observed_revision"] == observed["observed_revision"]
            assert identity["file_count"] == observed["file_inventory"]["total_files"]
            assert identity["published_row_count"] == observed["published_row_count"]


def test_public_readback_binds_all_published_bytes_and_access() -> None:
    """The receipt proves anonymous access and exact expected publication bytes."""
    receipt = _load(
        EVIDENCE_ROOT / "huggingface-publication/publication-readback-20260903.json"
    )
    assert receipt["status"] == "public_verified"
    assert receipt["dataset"] == {
        "slug": "edithatogo/corpus-legislation-nz",
        "role": "canonical_living_dataset",
        "created_new_identity": False,
        "private": False,
        "gated": False,
    }
    authority = receipt["authority"]
    assert authority["decision_id"] == (
        "archive-govt-nz-hf-publication-20260903-selected-552-v1"
    )
    assert authority["candidate_manifest_sha256"] == _sha256(
        EVIDENCE_ROOT / "huggingface-publication/publication-candidate-manifest.json"
    )
    assert authority["approved_package_sha256"] == (
        "2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c"
    )
    assert authority["payload_bytes_permitted"] is True
    files = {
        item["path"]: (item["size_bytes"], item["sha256"])
        for item in receipt["anonymous_exact_revision_readback"]["files"]
    }
    assert files["README.md"] == (
        2713,
        "d41be7b72c10b1e79754bed9b59deed5862d535b6ed0eead2a02df01392e8c4d",
    )
    assert files["RIGHTS.md"] == (
        771,
        "1cf3df1c833ab9f8a44b703a7668a91b25dfa1b2626972f89d11f7607a776d03",
    )
    package = next(value for path, value in files.items() if path.endswith(".zip"))
    assert package == (
        71776346,
        "2e4b75333e947d812842147c939117fc666799e4497b80f125104f721ef68e3c",
    )
    permitted = {
        item["path"]: (item["size_bytes"], item["sha256"])
        for item in authority["permitted_files"]
    }
    assert permitted == files
    assert (
        "not a copy of canonical-state.zip"
        in receipt["github_relationship"]["relationship"]
    )
