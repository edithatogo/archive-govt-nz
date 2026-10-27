# SPDX-License-Identifier: Apache-2.0
"""Governed discovery retains source references and blocks unsupported links."""

import copy
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError
from tests.domains.health_appropriations import (
    test_qualified_overview_metadata as shared,
)

from archive_govt_nz.domains.health_appropriations import (
    qualified_overview_metadata as metadata,
)

qualified_inputs = shared.qualified_inputs
metadata_input = shared.metadata_input


def test_discovery_records_bind_verified_sources_without_approved_links(
    metadata_input: metadata.QualifiedOverviewInput, tmp_path: Path
) -> None:
    value = metadata_input
    baseline = metadata.project_qualified_overview_metadata((value,))
    docs = metadata.project_qualified_overview_discovery((value,))
    assert all(docs[name] == payload for name, payload in baseline.items())
    assert docs == metadata.project_qualified_overview_discovery((value,))
    citations = json.loads(docs["citations.json"])
    citation = citations["records"][0]
    assert citation["manifest_sha256"] == value.manifest_sha256
    assert citation["identifier_scope"] == "local_content_addressed_package"
    assert len(citation["resource_rights"]) == 2
    references = json.loads(docs["source_drillthrough.json"])["records"][0]
    assert references["source_object_sha256"] == value.request.expected_sha256
    assert references["source_locator"] == value.request.source_locator
    assert references["source_silver_manifest_sha256"] == value.silver_manifest_sha256
    changes = json.loads(docs["changelog.json"])
    assert changes["comparison"] == "snapshot_only_no_prior_version_comparison"
    readiness = json.loads(docs["federation_readiness.json"])
    assert readiness["approved_links"] == []
    assert len(readiness["records"]) == 2
    assert {r["target_repository"] for r in readiness["records"]} == {
        "reimbursement-atlas",
        "global-medicines-atlas",
    }
    assert all(r["disposition"] == "pending" for r in readiness["records"])
    assert all(r["target_manifest_sha256"] is None for r in readiness["records"])
    assert b"Synthetic test attribution" in docs["DATASET_CARD.md"]
    first = metadata.export_qualified_overview_metadata(
        (value,), tmp_path / "first", include_discovery=True
    )
    second = metadata.export_qualified_overview_metadata(
        (value,), tmp_path / "second", include_discovery=True
    )
    assert first == second
    marker = json.loads((tmp_path / "first/MANIFEST.json").read_bytes())
    assert marker["schema_version"].endswith("/v2")
    assert set(marker["output_sha256"]) == set(docs)
    assert all(
        hashlib.sha256(payload).hexdigest() == first[n] for n, payload in docs.items()
    )


def test_readiness_schema_rejects_invented_approvals(
    metadata_input: metadata.QualifiedOverviewInput,
) -> None:
    schema = json.loads(
        (
            Path(__file__).parents[3]
            / "schemas/health-federation-readiness-v1.schema.json"
        ).read_text()
    )
    validator = Draft202012Validator(schema)
    Draft202012Validator.check_schema(schema)
    report = json.loads(
        metadata.project_qualified_overview_discovery((metadata_input,))[
            "federation_readiness.json"
        ]
    )
    validator.validate(report)
    for mutation in ("approved", "target", "confidence", "period"):
        changed = copy.deepcopy(report)
        if mutation == "approved":
            changed["approved_links"] = [{"target": "invented"}]
        elif mutation == "target":
            changed["records"][0]["target_manifest_sha256"] = "a" * 64
        elif mutation == "confidence":
            changed["records"][0]["confidence"] = 1.0
        else:
            changed["records"][0]["effective_start"] = "2022-07-01"
        with pytest.raises(ValidationError):
            validator.validate(changed)
