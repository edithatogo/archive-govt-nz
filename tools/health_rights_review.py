# SPDX-License-Identifier: Apache-2.0
"""Independent, offline interpretation of verified Health metadata rights claims.

This is a development assurance tool, not a source of rights or release authority.
Callers must first verify the packet and its resource evidence. Expanded RDF
predicates prevent JSON-LD aliases from disguising blanket grants or joins.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from rdflib import Dataset, URIRef

from archive_govt_nz.domains.health_appropriations.qualified_overview_metadata import (
    verify_qualified_overview_metadata,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from archive_govt_nz.domains.health_appropriations import (
        qualified_overview_metadata,
    )
    from archive_govt_nz.domains.health_appropriations.partner_snapshots import (
        PartnerSnapshot,
    )

_MAX_BYTES = 32 * 1024 * 1024
_MAX_DEPTH = 64
_DCT = "http://purl.org/dc/terms/"
_SCHEMA = ("http://schema.org/", "https://schema.org/")
_SCOPE = "urn:archive-govt-nz:health:discovery:rightsScope"
_POSITIVE = {
    "http://www.w3.org/2002/07/owl#sameAs",
    "http://www.w3.org/2004/02/skos/core#exactMatch",
    "http://www.w3.org/2004/02/skos/core#closeMatch",
    *(base + "sameAs" for base in _SCHEMA),
}
_GRAPH_FILES = (
    "dcat.json",
    "prov.json",
    "dcat.jsonld",
    "prov.jsonld",
    "croissant.json",
    "ro-crate-metadata.json",
)


@dataclass(frozen=True)
class ResourceRights:
    """An exact resource assertion taken from independently verified evidence."""

    licence: str
    attribution: str
    scope: str
    decision: str


def _require(condition: bool, reason: str) -> None:  # noqa: FBT001 - assertion helper
    if not condition:
        raise ValueError(reason)


def _local_contexts(value: object, depth: int = 0) -> None:
    _require(depth <= _MAX_DEPTH, "rights_review_document_depth")
    if isinstance(value, dict):
        for key, child in value.items():
            _require(key != "@import", "rights_review_external_context")
            if key == "@context":
                contexts = child if isinstance(child, list) else [child]
                _require(
                    all(isinstance(c, dict) or c is None for c in contexts),
                    "rights_review_external_context",
                )
            _local_contexts(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _local_contexts(child, depth + 1)


def _claim_expected(
    subject: str, predicate: str, resources: Mapping[str, ResourceRights]
) -> str | None:
    identity = subject.removesuffix(":distribution")
    resource = resources.get(identity)
    if resource is not None:
        if predicate in {_DCT + "license", *(b + "license" for b in _SCHEMA)}:
            return resource.licence
        if predicate in {b + "creditText" for b in _SCHEMA}:
            return resource.attribution
        if predicate == _SCOPE:
            return resource.scope
        if predicate == _DCT + "rights":
            return resource.decision
    if predicate == _DCT + "description":
        scopes = {r.scope for r in resources.values() if r.decision == subject}
        if len(scopes) == 1:
            return next(iter(scopes))
    return None


def review_graph_claims(
    documents: Mapping[str, bytes], resources: Mapping[str, ResourceRights]
) -> dict[str, Any]:
    """Check graph assertions against supplied verified evidence, without fetches.

    An empty resource map is mandatory for inventory-only projections. This
    function checks statements, not the authenticity of caller-supplied evidence.
    Packet/source reconstruction is a separate prerequisite.
    """
    statements = []
    documents_reviewed = {}
    predicates = {
        _DCT + "license",
        _DCT + "rights",
        _SCOPE,
        *(b + "license" for b in _SCHEMA),
        *(b + "creditText" for b in _SCHEMA),
    }
    for name in _GRAPH_FILES:
        if name not in documents:
            continue
        payload = documents[name]
        _require(len(payload) <= _MAX_BYTES, "rights_review_document_size")
        document = json.loads(payload)
        _local_contexts(document)
        graph = Dataset().parse(data=payload.decode("utf-8"), format="json-ld")
        documents_reviewed[name] = hashlib.sha256(payload).hexdigest()
        licensed = set()
        for subject, predicate, value, _context in graph.quads():
            s, p, v = str(subject), str(predicate), str(value)
            _require(p not in _POSITIVE, "rights_review_positive_link_unapproved")
            expected = _claim_expected(s, p, resources)
            if p not in predicates and expected is None:
                continue
            _require(
                expected is not None and v == expected, "rights_review_unbound_claim"
            )
            if p in {_DCT + "license", *(b + "license" for b in _SCHEMA)}:
                _require(isinstance(value, URIRef), "rights_review_licence_not_iri")
                licensed.add(s.removesuffix(":distribution"))
            statements.append(
                {"document": name, "subject": s, "predicate": p, "value": v}
            )
        _require(licensed == set(resources), "rights_review_licence_coverage")
    _require(bool(documents_reviewed), "rights_review_no_graphs")
    return {
        "schema_version": "archive-govt-nz.health-rights-graph-review/v1",
        "documents_sha256": documents_reviewed,
        "resource_count": len(resources),
        "statements": sorted(
            statements,
            key=lambda row: (
                row["document"],
                row["subject"],
                row["predicate"],
                row["value"],
            ),
        ),
        "positive_links": 0,
        "evidence_authentication": "caller_must_verify_packet_and_resources",
        "release_readiness": "not_assessed",
        "publication": "not_performed",
    }


def review_qualified_packet(  # noqa: PLR0913 - exact pins and opt-in profiles are explicit.
    values: tuple[qualified_overview_metadata.QualifiedOverviewInput, ...],
    package: Path,
    *,
    manifest_sha256: str,
    include_discovery: bool = False,
    partner_snapshots: tuple[PartnerSnapshot, ...] = (),
    include_federation_tables: bool = False,
) -> dict[str, Any]:
    """Requalify sources/evidence, reconstruct every member, then review claims.

    Cards, citations, changelogs and federation sidecars are byte-compared with
    their evidence-derived projections. Graph claims get an additional semantic
    interpretation independent of their JSON field names. No rights are granted
    to the metadata or federation tables themselves.
    """
    receipt = verify_qualified_overview_metadata(
        values,
        package,
        manifest_sha256=manifest_sha256,
        include_discovery=include_discovery,
        partner_snapshots=partner_snapshots,
        include_federation_tables=include_federation_tables,
    )
    manifest = json.loads(
        verified_snapshot(
            package / "MANIFEST.json", manifest_sha256, max_bytes=_MAX_BYTES
        )
    )
    documents = {
        name: verified_snapshot(package / name, pin, max_bytes=_MAX_BYTES)
        for name, pin in manifest["output_sha256"].items()
    }
    resources = {}
    source_evidence = []
    for value in values:
        source = json.loads(
            verified_snapshot(
                value.package / "MANIFEST.json",
                value.manifest_sha256,
                max_bytes=_MAX_BYTES,
            )
        )
        rights = ResourceRights(
            source["license_uri"],
            source["attribution"],
            source["rights_scope"],
            "urn:sha256:" + source["output_sha256"]["rights.json"],
        )
        prefix = "urn:archive-govt-nz:health:qualified:" + value.manifest_sha256 + ":"
        resources.update(
            {prefix + r["path"]: rights for r in source["resource_rights"]}
        )
        source_evidence.append(
            {
                "manifest_sha256": value.manifest_sha256,
                "source_sha256": source["source_object_sha256"],
                "rights_decision_sha256": source["output_sha256"]["rights.json"],
                "evidence_sha256": source["evidence_sha256"],
            }
        )
    return {
        "schema_version": "archive-govt-nz.health-qualified-rights-review/v1",
        "packet_verification": receipt,
        "graph_review": review_graph_claims(documents, resources),
        "all_member_sha256": manifest["output_sha256"],
        "source_evidence": sorted(source_evidence, key=lambda r: r["manifest_sha256"]),
        "non_graph_review": "exact_evidence_derived_projection_reconstruction",
        "metadata_and_federation_rights": "not_inherited_not_evaluated",
        "release_readiness": "not_assessed",
        "publication": "not_performed",
    }
