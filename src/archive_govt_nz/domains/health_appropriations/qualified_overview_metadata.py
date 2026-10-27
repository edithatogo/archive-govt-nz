# SPDX-License-Identifier: Apache-2.0
"""Resource-scoped DCAT, Croissant, RO-Crate and PROV for qualified headlines."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from io import BytesIO
from typing import TYPE_CHECKING, Any

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations.gold_discovery_profiles import (
    project_inventory_candidates,
)
from archive_govt_nz.domains.health_appropriations.gold_metadata import (
    project_inventory_graphs,
)
from archive_govt_nz.domains.health_appropriations.overview_rights import (
    verify_qualified_overview_package,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.domains.health_appropriations.source_operations import (
        SourceRequest,
    )

_MAX_INPUTS = 5
_MAX_BYTES = 4 * 1024 * 1024
_SCHEMA = "archive-govt-nz.qualified-overview-metadata/v1"


@dataclass(frozen=True)
class QualifiedOverviewInput:
    """Independent source/Silver/qualified-Gold pins and retained evidence."""

    request: SourceRequest
    silver_manifest_sha256: str
    evidence_root: Path
    package: Path
    manifest_sha256: str


def _require(value: object) -> None:
    if not value:
        message = "qualified_overview_metadata_contract"
        raise ValueError(message)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()


def _safe(path: Path) -> None:
    _require(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)))


def _package(value: QualifiedOverviewInput) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = verify_qualified_overview_package(
        value.request,
        value.silver_manifest_sha256,
        value.evidence_root,
        value.package,
        manifest_sha256=value.manifest_sha256,
    )
    identity = "urn:archive-govt-nz:health:qualified:" + value.manifest_sha256
    inventory, tables = [], []
    for resource in manifest["resource_rights"]:
        name, pin = resource["path"], resource["payload_sha256"]
        payload = verified_snapshot(value.package / name, pin, max_bytes=_MAX_BYTES)
        inventory.append({"path": name, "sha256": pin, "bytes": len(payload)})
        if name.endswith(".parquet"):
            with pq.ParquetFile(
                BytesIO(payload),
                thrift_string_size_limit=_MAX_BYTES,
                thrift_container_size_limit=100_000,
            ) as parquet:
                schema = parquet.schema_arrow
                ipc = schema.serialize().to_pybytes()
                tables.append(
                    {
                        "id": identity + ":" + name,
                        "path": name,
                        "rows": parquet.metadata.num_rows,
                        "schema_sha256": hashlib.sha256(ipc).hexdigest(),
                        "schema_ipc_hex": ipc.hex(),
                        "fields": [
                            {
                                "name": f.name,
                                "type": str(f.type),
                                "nullable": f.nullable,
                            }
                            for f in schema
                        ],
                    }
                )
    _require(len(tables) == 1)
    return {
        "id": identity,
        "profile": value.request.profile,
        "manifest_sha256": value.manifest_sha256,
        "inventory": inventory,
        "tables": tables,
    }, {
        "manifest": manifest,
        "decision": json.loads(
            verified_snapshot(
                value.package / "rights.json",
                manifest["output_sha256"]["rights.json"],
                max_bytes=_MAX_BYTES,
            )
        ),
    }


def _provenance(
    package: dict[str, Any],
    manifest: dict[str, Any],
    decision: dict[str, Any],
    prov: dict[str, Any],
) -> str:
    decision_id = "urn:sha256:" + manifest["output_sha256"]["rights.json"]
    sources = [
        "urn:sha256:" + manifest["source_object_sha256"],
        "urn:sha256:" + manifest["source_silver_manifest_sha256"],
        "urn:sha256:" + manifest["output_sha256"]["vote_health_overview_facts.parquet"],
    ]
    evidence_ids = ["urn:sha256:" + pin for pin in decision["evidence_sha256"].values()]
    for identity in (*sources, *evidence_ids):
        if not any(n["@id"] == identity for n in prov["@graph"]):
            prov["@graph"].append({"@id": identity, "@type": "prov:Entity"})
    prov["@graph"].append(
        {
            "@id": decision_id,
            "@type": ["prov:Entity", "dct:RightsStatement"],
            "dct:description": manifest["rights_scope"],
            "prov:wasDerivedFrom": [{"@id": i} for i in sorted(evidence_ids)],
        }
    )
    for node in prov["@graph"]:
        if node["@id"] in {
            package["id"] + ":" + r["path"] for r in manifest["resource_rights"]
        }:
            node.update(
                {
                    "prov:wasDerivedFrom": [{"@id": i} for i in sources],
                    "dct:relation": {"@id": decision_id},
                }
            )
    return decision_id


def _enrich(
    packages: list[dict[str, Any]], decisions: dict[str, dict[str, Any]]
) -> dict[str, bytes]:
    catalogue = {
        "schema_version": _SCHEMA,
        "packages": packages,
        "publication": "not_performed",
        "rights_scope": "per_verified_data_resource_only",
    }
    catalogue_bytes = _json(catalogue)
    croissant, crate, report = project_inventory_candidates(
        catalogue,
        name="Qualified Vote Health headline data",
        description=(
            "Verified local source-separated headline resources; rights are "
            "qualified per data resource. Publication and complete standards "
            "conformance remain unasserted."
        ),
    )
    dcat, prov = project_inventory_graphs(
        packages, hashlib.sha256(catalogue_bytes).hexdigest()
    )
    resource_rights = {}
    decision_ids = {}
    for package in packages:
        context = decisions[package["id"]]
        manifest, decision = context["manifest"], context["decision"]
        for resource in manifest["resource_rights"]:
            resource_rights[package["id"] + ":" + resource["path"]] = {
                "license": {"@id": manifest["license_uri"]},
                "creditText": manifest["attribution"],
                "hag:rightsScope": manifest["rights_scope"],
            }
        query_id = package["id"] + ":query.json"
        query = next(i for i in package["inventory"] if i["path"] == "query.json")
        dataset = next(
            n
            for n in dcat["@graph"]
            if n.get("@type") == "dcat:Dataset"
            and n["@id"] == package["tables"][0]["id"]
        )
        dataset["@id"] += ":dataset"
        dataset["dct:identifier"] = dataset["@id"]
        dataset["dcat:distribution"] = [
            dataset["dcat:distribution"],
            {"@id": query_id + ":distribution"},
        ]
        dcat["@graph"].append(
            {
                "@id": query_id + ":distribution",
                "@type": "dcat:Distribution",
                "dcat:mediaType": {
                    "@id": "https://www.iana.org/assignments/media-types/application/json"
                },
                "dcat:byteSize": {
                    "@value": str(query["bytes"]),
                    "@type": "xsd:nonNegativeInteger",
                },
                "spdx:checksum": {
                    "@type": "spdx:Checksum",
                    "spdx:algorithm": {"@id": "spdx:checksumAlgorithm_sha256"},
                    "spdx:checksumValue": {
                        "@value": query["sha256"],
                        "@type": "xsd:hexBinary",
                    },
                },
            }
        )
        decision_id = _provenance(package, manifest, decision, prov)
        dcat["@graph"].append(
            {
                "@id": decision_id,
                "@type": "dct:RightsStatement",
                "dct:description": manifest["rights_scope"],
            }
        )
        for resource in manifest["resource_rights"]:
            decision_ids[package["id"] + ":" + resource["path"]] = decision_id
    for node in croissant["distribution"]:
        node.update(resource_rights[node["@id"]])
    for node in crate["@graph"]:
        if node["@id"] in resource_rights:
            node.update(resource_rights[node["@id"]])
    licence = next(iter(resource_rights.values()))["license"]["@id"]
    crate["@graph"].append(
        {
            "@id": licence,
            "@type": "CreativeWork",
            "name": "Creative Commons Attribution 4.0 International",
        }
    )
    for document in (dcat, prov):
        document["@context"] = {**document["@context"], "schema": "http://schema.org/"}
        for node in document["@graph"]:
            identity = (
                node["@id"].removesuffix(":distribution")
                if node.get("@type") == "dcat:Distribution"
                else node["@id"]
            )
            if identity in resource_rights and (
                document is prov or node.get("@type") == "dcat:Distribution"
            ):
                rights = resource_rights[identity]
                node.update(
                    {
                        "dct:license": rights["license"],
                        "schema:creditText": rights["creditText"],
                        "dct:rights": {"@id": decision_ids[identity]},
                    }
                )
        document["@graph"].sort(key=lambda n: n["@id"])
    report.update(
        {
            "schema_version": _SCHEMA,
            "rights": "qualified_data_resources_only",
            "qualified_packages": len(packages),
            "qualified_data_resources": len(resource_rights),
            "source_reverification": "performed_with_pinned_rights_and_source_evidence",
            "dataset_wide_licence": "not_asserted",
            "payload_staging": "verified_external_packages_not_copied",
            "root_licence_omission": "intentional_no_dataset_wide_grant",
            "rights_overlay": (
                "source_row_normalization_state_retained; "
                "effective resource assessment projected"
            ),
            "publication": "not_performed",
            "federation": "no_links_emitted",
        }
    )
    return {
        "catalogue.json": catalogue_bytes,
        "dcat.json": _json(dcat),
        "prov.json": _json(prov),
        "croissant.json": _json(croissant),
        "ro-crate-metadata.json": _json(crate),
        "profile-validation.json": _json(report),
    }


def project_qualified_overview_metadata(
    values: tuple[QualifiedOverviewInput, ...],
) -> dict[str, bytes]:
    """Verify all supplied products and project rights without modifying inputs."""
    _require(type(values) is tuple and 0 < len(values) <= _MAX_INPUTS)
    _require(len({v.request.profile for v in values}) == len(values))
    packages, decisions = [], {}
    for value in sorted(values, key=lambda v: v.request.profile):
        package, decision = _package(value)
        packages.append(package)
        decisions[package["id"]] = decision
    return _enrich(packages, decisions)


def export_qualified_overview_metadata(
    values: tuple[QualifiedOverviewInput, ...], output: Path
) -> dict[str, str]:
    """Write an exclusive metadata-only version after complete input verification."""
    _safe(output)
    _require(not output.exists() and output.parent.is_dir())
    for value in values:
        for protected in (
            value.package,
            value.request.output_dir,
            value.request.source,
            value.evidence_root,
        ):
            _safe(protected)
            a, b = output.resolve(), protected.resolve()
            _require(not a.is_relative_to(b) and not b.is_relative_to(a))
    payloads = project_qualified_overview_metadata(values)
    pins = {
        name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()
    }
    output.mkdir(exist_ok=False)
    for name, payload in {
        **payloads,
        "MANIFEST.json": _json(
            {
                "schema_version": _SCHEMA,
                "output_sha256": pins,
                "publication": "not_performed",
                "full_conformance": "not_asserted",
            }
        ),
    }.items():
        with (output / name).open("xb") as stream:
            stream.write(payload)
        _require((output / name).read_bytes() == payload)
    return pins
