"""Pure PROV entity/derivation projection, not observed execution provenance."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.local_provenance import (
    build_local_provenance,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.local_provenance import (
        ProductDescriptor,
    )


@dataclass(frozen=True)
class ProvProjection:
    """Fresh graph, complete source inventory and separate assertion-only receipt."""

    document: dict[str, Any]
    inventory: dict[str, Any]
    receipt: dict[str, Any]


def _digest(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode()
    return hashlib.sha256(payload).hexdigest()


def project_local_prov(values: tuple[ProductDescriptor, ...]) -> ProvProjection:
    """Map validated descriptors to an inline-context, entity-only PROV graph.

    Complete physical metadata and edge kinds remain in the accompanying
    inventory. Dependencies are caller assertions, not independently observed
    activities. No files, remote contexts, actors, dates or rights are inferred.
    External JSON-LD/RDF/PROV processor validation remains outside this helper.
    """
    inventory = build_local_provenance(values)
    inputs: dict[str, list[str]] = {row["id"]: [] for row in inventory["products"]}
    for edge in inventory["edges"]:
        inputs[edge["product"]].append(edge["input"])
    nodes: list[dict[str, Any]] = [
        {"@id": source["id"], "@type": "prov:Entity"} for source in inventory["sources"]
    ]
    nodes.extend(
        {
            "@id": product["id"],
            "@type": "prov:Entity",
            "prov:wasDerivedFrom": [
                {"@id": source} for source in sorted(inputs[product["id"]])
            ],
        }
        for product in inventory["products"]
    )
    document = {
        "@context": {"prov": "http://www.w3.org/ns/prov#"},
        "@graph": sorted(nodes, key=lambda node: node["@id"]),
    }
    return ProvProjection(
        document=document,
        inventory=inventory,
        receipt={
            "schema_version": "archive-govt-nz.health-local-prov-projection/v1",
            "projection_scope": "asserted_entity_derivation_only",
            "input_fixity": "not_performed",
            "semantic_validation": "not_performed",
            "standards_processor_validation": "not_performed",
            "rights_state": "not_evaluated",
            "approval": "not_granted",
            "publication": "not_performed",
            "graph_sha256": _digest(document),
            "inventory_sha256": _digest(inventory),
            "entities": len(nodes),
            "derivations": len(inventory["edges"]),
        },
    )
