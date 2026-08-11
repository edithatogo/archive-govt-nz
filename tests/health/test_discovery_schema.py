"""Schema and committed-evidence tests for broader-health discovery."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from jsonschema import Draft202012Validator, FormatChecker


def test_committed_health_evidence_and_manifest_schema() -> None:
    """The paired evidence is machine-readable and retains the safety gates."""
    schema = cast(
        "dict[str, Any]",
        json.loads(
            Path("schemas/health-discovery-v1.schema.json").read_text(encoding="utf-8")
        ),
    )
    evidence = cast(
        "dict[str, Any]",
        json.loads(
            Path("evidence/health-discovery-20260811.json").read_text(encoding="utf-8")
        ),
    )
    Draft202012Validator.check_schema(schema)
    assert evidence["status"] == "observed"
    assert evidence["scope_counts"]["unique_datasets"] == 815
    assert evidence["payload_eligible"] == 0
    assert evidence["gates"]["publication"] is False


def test_manifest_schema_rejects_payload_eligibility() -> None:
    """A Track 12 manifest cannot authorize a resource payload."""
    schema = json.loads(
        Path("schemas/health-discovery-v1.schema.json").read_text(encoding="utf-8")
    )
    manifest = {
        "schema_version": "archive-govt-nz.health-discovery/v1",
        "observed_at": "2026-08-11T08:00:00Z",
        "catalogue_url": "https://catalogue.data.govt.nz",
        "status": "observed",
        "dataset_count": 1,
        "datasets": [
            {
                "dataset_id": "one",
                "name": "one",
                "title": "One",
                "scopes": ["text-health"],
                "organization_id": None,
                "licence": None,
                "metadata_modified": None,
                "resource_count": 0,
                "classification": "decision-required",
                "health_relevance": "matched-versioned-health-scope",
                "payload_eligible": True,
                "sensitivity": "decision-required",
            }
        ],
        "scopes": {"text-health": ["one"]},
        "metadata_fingerprints": {"one": "0" * 64},
        "rerun": {"changed": [], "new": ["one"], "unchanged": [], "withdrawn": []},
        "pages": [],
        "policy": {
            "metadata_only": True,
            "payload_capture": False,
            "publication": False,
            "max_page_size": 100,
            "post_primary_get_after_failure": True,
            "unknown_rights_fail_closed": True,
            "sensitivity_requires_decision": True,
        },
    }
    errors = list(
        Draft202012Validator(  # pyright: ignore[reportUnknownMemberType]
            schema, format_checker=FormatChecker()
        ).iter_errors(manifest)
    )
    assert any(error.validator == "const" for error in errors)
