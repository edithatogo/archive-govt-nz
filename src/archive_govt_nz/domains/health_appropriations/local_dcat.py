"""Read-only DCAT metadata for verified local canonical recordset snapshots."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    read_local_provenance,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
        CanonicalPackageInput,
    )


@dataclass(frozen=True)
class DcatProjection:
    """Fresh graph, full verified physical inventory, and separate scope receipt."""

    document: dict[str, Any]
    verification: dict[str, Any]
    receipt: dict[str, Any]


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()


def read_local_dcat(values: tuple[CanonicalPackageInput, ...]) -> DcatProjection:
    """Verify bounded packages before describing each recordset's representation.

    Uses the existing reader's trusted-parent/snapshot contract. This describes
    locally retained tables, not public availability or a later filesystem state.
    Distinct recordsets and package versions are distinct datasets, not alternate
    serializations of one combined dataset. Exact schemas, rows, payload hashes
    and derivation edges remain in the accompanying verification inventory.
    No remote context, I/O write, publication locator, licence or date is inferred.
    Full DCAT application-profile/RDF conformance requires separate validation.
    """
    verification = read_local_provenance(values)
    products = verification["inventory"]["products"]
    nodes: list[dict[str, Any]] = []
    for product in products:
        digest = product["id"].removeprefix("product:sha256:")
        dataset_id = "urn:archive-govt-nz:health:dataset:" + digest
        distribution_id = "urn:archive-govt-nz:health:distribution:" + digest
        nodes.extend(
            [
                {
                    "@id": dataset_id,
                    "@type": "dcat:Dataset",
                    "dct:title": product["vintage"] + ": " + product["recordset"],
                    "dct:identifier": product["key"],
                    "dcat:distribution": {"@id": distribution_id},
                },
                {
                    "@id": distribution_id,
                    "@type": "dcat:Distribution",
                    "dcat:mediaType": {
                        "@id": (
                            "https://www.iana.org/assignments/media-types/"
                            "application/vnd.apache.parquet"
                        ),
                    },
                    "dcat:byteSize": {
                        "@value": str(product["bytes"]),
                        "@type": "xsd:nonNegativeInteger",
                    },
                    "spdx:checksum": {
                        "@type": "spdx:Checksum",
                        "spdx:algorithm": {"@id": "spdx:checksumAlgorithm_sha256"},
                        "spdx:checksumValue": {
                            "@value": product["payload_sha256"],
                            "@type": "xsd:hexBinary",
                        },
                    },
                },
            ]
        )
    document = {
        "@context": {
            "dcat": "http://www.w3.org/ns/dcat#",
            "dct": "http://purl.org/dc/terms/",
            "xsd": "http://www.w3.org/2001/XMLSchema#",
            "spdx": "http://spdx.org/rdf/terms#",
        },
        "@graph": sorted(nodes, key=lambda node: node["@id"]),
    }
    return DcatProjection(
        document=document,
        verification=verification,
        receipt={
            "schema_version": "archive-govt-nz.health-local-dcat/v1",
            "scope": "verified_local_recordset_snapshots",
            "verification_scope": verification["verification_scope"],
            "datasets": len(products),
            "distributions": len(products),
            "graph_sha256": _digest(document),
            "verification_sha256": _digest(verification),
            "standards_processor_validation": "not_performed",
            "rights_state": "not_evaluated",
            "approval": "not_granted",
            "publication": "not_performed",
        },
    )
