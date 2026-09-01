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
SCHEMA_PATH = ROOT / "schemas/legislation-huggingface-registry-v1.schema.json"
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


def test_registry_is_bound_to_coverage_and_blocked_operational_proof() -> None:
    """Coverage remains bounded and the failed Prompt 13 prerequisite is explicit."""
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
        "status": "blocked_prerequisite",
        "remote_write_authorized": False,
        "prompt13_operational_proof": False,
        "prompt13_receipt_sha256": _sha256(prompt13),
        "payload_rights": "source_specific_review_required",
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


def test_registry_rejects_publication_authority_and_aggregate_count() -> None:
    """A registry candidate cannot grant publication or sum unlike surfaces."""
    registry = copy.deepcopy(_load(REGISTRY_PATH))
    registry["publication_gate"]["remote_write_authorized"] = True
    registry["coverage"]["published_counts_aggregate"] = 6609
    errors = list(Draft202012Validator(_load(SCHEMA_PATH)).iter_errors(registry))
    assert len(errors) == 2


def test_registry_revisions_and_surface_counts_match_prompt14_observations() -> None:
    """Each identity must retain its own observed revision and surface counts."""
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
        observed = surfaces[identity["slug"]]
        assert identity["observed_revision"] == observed["observed_revision"]
        assert identity["file_count"] == observed["file_inventory"]["total_files"]
        assert identity["published_row_count"] == observed["published_row_count"]
