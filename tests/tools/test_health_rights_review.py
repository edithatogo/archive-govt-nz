# SPDX-License-Identifier: Apache-2.0
"""Rights evidence cannot be widened by graph projection or JSON-LD aliases."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

# Imported fixtures retain their prerequisite fixture in this module.
from tests.domains.health_appropriations import (
    test_qualified_overview_metadata as shared,
)
from tests.health_rights_review_support import RIGHTS_REVIEW

from archive_govt_nz.domains.health_appropriations import qualified_overview_metadata

metadata_input = shared.metadata_input
qualified_inputs = shared.qualified_inputs


def test_qualified_projection_binds_every_grant_to_its_resource(
    metadata_input: qualified_overview_metadata.QualifiedOverviewInput,
    tmp_path: Path,
) -> None:
    """All four graphs repeat the exact two resource-scoped assertions."""
    value = metadata_input
    manifest = json.loads((value.package / "MANIFEST.json").read_bytes())
    rights = RIGHTS_REVIEW.ResourceRights(
        manifest["license_uri"],
        manifest["attribution"],
        manifest["rights_scope"],
        "urn:sha256:" + manifest["output_sha256"]["rights.json"],
    )
    resources = {
        "urn:archive-govt-nz:health:qualified:"
        + value.manifest_sha256
        + ":"
        + r["path"]: rights
        for r in manifest["resource_rights"]
    }
    docs = qualified_overview_metadata.project_qualified_overview_metadata((value,))
    first = RIGHTS_REVIEW.review_graph_claims(docs, resources)
    assert first == RIGHTS_REVIEW.review_graph_claims(docs, resources)
    assert first["resource_count"] == 2
    assert sum(r["predicate"].endswith("/license") for r in first["statements"]) == 8
    assert first["positive_links"] == 0
    assert first["release_readiness"] == "not_assessed"
    packet = tmp_path / "metadata-packet"
    qualified_overview_metadata.export_qualified_overview_metadata((value,), packet)
    pin = hashlib.sha256((packet / "MANIFEST.json").read_bytes()).hexdigest()
    reviewed = RIGHTS_REVIEW.review_qualified_packet(
        (value,), packet, manifest_sha256=pin
    )
    assert reviewed["graph_review"] == first
    assert reviewed["source_evidence"][0]["manifest_sha256"] == value.manifest_sha256
    (packet / "dcat.json").write_text("{}")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        RIGHTS_REVIEW.review_qualified_packet((value,), packet, manifest_sha256=pin)


@pytest.mark.parametrize(
    ("context", "property_name", "expected"),
    [
        (
            {"claim": {"@id": "http://schema.org/license", "@type": "@id"}},
            "claim",
            "unbound_claim",
        ),
        (
            {"claim": {"@id": "http://www.w3.org/2002/07/owl#sameAs", "@type": "@id"}},
            "claim",
            "positive_link_unapproved",
        ),
        ("https://example.invalid/remote-context", "claim", "external_context"),
        (
            {"@import": "https://example.invalid/remote-context"},
            "claim",
            "external_context",
        ),
    ],
)
def test_aliases_and_remote_contexts_cannot_bypass_review(
    context: object,
    property_name: str,
    expected: str,
) -> None:
    """Expanded predicates and contexts reject hidden claims before access."""
    doc = {"@context": context, "@id": "urn:whole-dataset", property_name: "urn:grant"}
    with pytest.raises(ValueError, match="rights_review_" + expected):
        RIGHTS_REVIEW.review_graph_claims({"dcat.json": json.dumps(doc).encode()}, {})


def test_inventory_graph_has_no_authority_to_grant_rights() -> None:
    """Missing grants cannot be counted as successful qualified coverage."""
    doc = {
        "@context": {"name": "http://schema.org/name"},
        "@id": "urn:data",
        "name": "Inventory",
    }
    report = RIGHTS_REVIEW.review_graph_claims(
        {"dcat.json": json.dumps(doc).encode()}, {}
    )
    assert report["statements"] == []
    with pytest.raises(ValueError, match="licence_coverage"):
        RIGHTS_REVIEW.review_graph_claims(
            {"dcat.json": json.dumps(doc).encode()},
            {
                "urn:data": RIGHTS_REVIEW.ResourceRights(
                    "urn:licence", "credit", "scope", "urn:decision"
                )
            },
        )
