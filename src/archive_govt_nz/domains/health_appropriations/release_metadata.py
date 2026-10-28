# SPDX-License-Identifier: Apache-2.0
"""Pinned resource-level metadata profiles; qualification never grants publication.

The expected contract pin is an operator trust input, not discovered authority.
Evidence bytes are verified; neither their legal accuracy nor publication approval
can be inferred. Facts, dates, creators and grants must be explicit, never defaults.
"""

# ruff: noqa: SLF001 -- reuse existing strict JSON and portable inventory boundaries.

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from importlib.resources import files
from itertools import islice
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Any, cast

from jsonschema import Draft202012Validator, FormatChecker

from archive_govt_nz.domains.health_appropriations import candidate_inventory
from archive_govt_nz.domains.health_appropriations.candidate_metadata import (
    EXTENDED_MEMBERS,
    MAX_MEMBERS,
    MAX_NODES,
    MAX_PACKAGE_BYTES,
    MAX_PAYLOAD_BYTES,
    project_candidate_inventory,
)
from archive_govt_nz.domains.health_appropriations.candidate_metadata import (
    GENERATED_MEMBERS as BASE_MEMBERS,
)
from archive_govt_nz.domains.health_appropriations.metadata_application import (
    _load,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

VERSION = "archive-govt-nz.health-metadata-release-contract/v1"
VOCAB = (
    "https://raw.githubusercontent.com/edithatogo/archive-govt-nz/"
    "main/docs/health-metadata-contracts.md#"
)
GENERATED_MEMBERS = BASE_MEMBERS | EXTENDED_MEMBERS
MAX_RELEASE_MEMBERS = MAX_MEMBERS + len(GENERATED_MEMBERS)
# Exact representation descriptors only; payload values are never cast.
_CROISSANT_TYPES = {
    **{
        f"{sign}int{bits}": "cr:" + ("U" if sign else "") + "Int" + str(bits)
        for sign in ("", "u")
        for bits in (8, 16, 32, 64)
    },
    "bool": "sc:Boolean",
    "string": "sc:Text",
    "large_string": "sc:Text",
    "halffloat": "cr:Float16",
    "float": "cr:Float32",
    "double": "cr:Float64",
}

_SCHEMA = json.loads(
    files(__package__).joinpath("metadata-release-contract-v1.schema.json").read_text()
)
_MANIFEST_SCHEMA = json.loads(
    files(__package__).joinpath("candidate-v2.schema.json").read_text()
)
_VERIFICATION_SCHEMA = json.loads(
    files(__package__)
    .joinpath("metadata-release-verification-v1.schema.json")
    .read_text()
)
_ERROR = "metadata_release_contract"


@dataclass(frozen=True)
class MetadataReleaseInput:
    """Explicit operator-selected contract and content-addressed evidence root."""

    contract_path: Path
    contract_sha256: str
    evidence_root: Path


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _safe(path: Path) -> None:
    _require(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)))


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()


def _validate(value: dict[str, Any], schema: dict[str, Any]) -> None:
    _require(
        Draft202012Validator(schema, format_checker=FormatChecker()).is_valid(value)
    )


def validate_release_manifest(manifest: dict[str, Any]) -> None:
    """Reject malformed or non-portable v2 records before any member read."""
    _validate(manifest, _MANIFEST_SCHEMA)
    candidate_inventory._unique(
        [*[r["path"] for r in manifest["files"]], "MANIFEST.json"]
    )


def render_card(facts: dict[str, Any], resources: list[dict[str, Any]]) -> bytes:
    """Summarize explicit mixed grants without blanket licensing or hash cycles."""
    _validate(facts, _SCHEMA["$defs"]["facts"])
    rows = [
        "# " + facts["name"],
        "",
        facts["description"],
        "",
        "Version: " + facts["version"],
        "",
        "## Resource-specific rights",
        "",
        "No dataset-wide grant is asserted.",
        "This document grants no publication approval.",
        "",
    ]
    rows.extend(
        f"- {row['path']}: {row['state']}; "
        f"{row['license_uri'] or 'no redistribution grant'}"
        for row in sorted(resources, key=lambda r: r["path"])
    )
    return ("\n".join(rows) + "\n").encode()


def _notice(facts: dict[str, Any]) -> dict[str, Any]:
    return {
        "@id": facts["identifier"] + ":resource-rights-notice",
        "@type": "CreativeWork",
        "name": "Resource-specific rights",
        "description": (
            "Per-resource licences apply; no dataset-wide grant is asserted."
        ),
    }


def _apply_facts(
    croissant: dict[str, Any], crate: dict[str, Any], facts: dict[str, Any]
) -> None:
    notice = _notice(facts)
    root = next(n for n in crate["@graph"] if n["@id"] == "./")
    for target in (croissant, root):
        target.update(
            {
                "name": facts["name"],
                "description": facts["description"],
                "version": facts["version"],
                "identifier": facts["identifier"],
                "license": notice if target is croissant else {"@id": notice["@id"]},
            }
        )
        if facts["url"] is not None:
            target["url"] = facts["url"]
        if facts["date_published"] is not None:
            target["datePublished"] = facts["date_published"]
        if facts["creators"] is not None:
            target["creator"] = [
                {"@id": a["id"], "@type": a["type"], "name": a["name"]}
                for a in facts["creators"]
            ]
    complete = all(facts[k] is not None for k in ("url", "date_published", "creators"))
    if complete:
        croissant["dct:conformsTo"] = "http://mlcommons.org/croissant/1.0"
        descriptor = next(
            n for n in crate["@graph"] if n["@id"] == "ro-crate-metadata.json"
        )
        descriptor["dct:conformsTo"] = {"@id": "https://w3id.org/ro/crate/1.1"}
    if facts["url"] is not None:
        root["url"] = {"@id": facts["url"]}
    root["identifier"] = {"@id": facts["identifier"]}
    crate["@graph"].append(notice)
    if facts["creators"] is not None:
        root["creator"] = [{"@id": actor["id"]} for actor in facts["creators"]]
        crate["@graph"].extend(
            {"@id": actor["id"], "@type": actor["type"], "name": actor["name"]}
            for actor in facts["creators"]
        )


def _apply_rights(
    nodes: list[dict[str, Any]], kind: str, rights: dict[str, Any]
) -> None:
    for node in nodes:
        identity = (
            node["@id"].removesuffix(":distribution")
            if node.get("@type") == "dcat:Distribution"
            else node["@id"]
        )
        if identity not in rights:
            continue
        decision = rights[identity]
        node["hag:rightsState"] = decision["state"]
        if decision["state"] == "eligible_asserted":
            node["license" if kind == "schema" else "dct:license"] = {
                "@id": decision["license_uri"]
            }
            node["creditText" if kind == "schema" else "schema:creditText"] = decision[
                "attribution"
            ]


def _staged_references(
    croissant: dict[str, Any],
    crate: dict[str, Any],
    dcat: dict[str, Any],
    prov: dict[str, Any],
    rights: dict[str, Any],
) -> None:
    croissant["@context"]["contentUrl"] = {
        "@id": "https://schema.org/contentUrl",
    }
    for node in croissant["distribution"]:
        node["contentUrl"] = "../" + rights[node["@id"]]["path"]
    for node in dcat["@graph"]:
        if node["@type"] == "dcat:Distribution":
            member = rights[node["@id"].removesuffix(":distribution")]["path"]
            node["dcat:accessURL"] = {"@id": "../" + member}
            node["dcat:downloadURL"] = {"@id": "../" + member}
    for node in prov["@graph"]:
        if node["@id"] in rights:
            node["prov:atLocation"] = {"@id": "../" + rights[node["@id"]]["path"]}
    mapping = {identity: decision["path"] for identity, decision in rights.items()}
    for node in crate["@graph"]:
        if node["@id"] in mapping:
            node["@id"] = mapping[node["@id"]]
    root = next(n for n in crate["@graph"] if n["@id"] == "./")
    root["hasPart"] = [{"@id": mapping[item["@id"]]} for item in root["hasPart"]]
    crate["@graph"].append(
        {
            "@id": VOCAB + "rightsState",
            "@type": "rdf:Property",
            "rdfs:label": "rightsState",
            "rdfs:comment": (
                "State in the operator-pinned resource contract; not a legal judgment."
            ),
        }
    )


def _profile_graphs(
    base: dict[str, bytes], facts: dict[str, Any], resources: list[dict[str, Any]]
) -> dict[str, bytes]:
    """Enrich observed inventories with explicit facts and scoped assertions."""
    croissant = json.loads(base["metadata/croissant.json"])
    crate = json.loads(base["ro-crate-metadata.json"])
    dcat = json.loads(base["metadata/dcat.json"])
    prov = json.loads(base["metadata/prov.json"])
    inventory = json.loads(base["metadata/payload-inventory.json"])["inventory"]
    package_id = (
        "urn:archive-govt-nz:health:candidate-payload-inventory:"
        + hashlib.sha256(base["metadata/payload-inventory.json"]).hexdigest()
    )
    by_path = {row["path"]: row for row in resources}
    _require(len(by_path) == len(resources))
    _require(all(row["path"] in by_path for row in inventory))
    rights = {package_id + ":" + i["path"]: by_path[i["path"]] for i in inventory}
    actor_ids = [a["id"] for a in facts["creators"] or []]
    _require(len(set(actor_ids)) == len(actor_ids))
    _require(facts["identifier"] not in rights and _notice(facts)["@id"] not in rights)
    _require(
        not (
            set(actor_ids)
            & (set(rights) | {facts["identifier"], _notice(facts)["@id"]})
        )
    )
    for document in (croissant, crate):
        document["@context"] = {
            **document["@context"],
            "dct": "http://purl.org/dc/terms/",
        }
    croissant["@context"]["@language"] = None
    croissant["@context"]["@vocab"] = "https://schema.org/"
    croissant["@context"]["sc"] = "https://schema.org/"
    _apply_facts(croissant, crate, facts)
    for record in croissant["cr:recordSet"]:
        for field in record["cr:field"]:
            physical = field["hag:arrowType"]
            if physical in _CROISSANT_TYPES:
                field["cr:dataType"] = {"@id": _CROISSANT_TYPES[physical]}
            else:
                croissant.pop("dct:conformsTo", None)

    for document in (croissant, crate, dcat, prov):
        document["@context"] = {
            **document["@context"],
            "schema": "http://schema.org/",
            "hag": VOCAB,
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        }
    for nodes, kind in (
        (croissant["distribution"], "schema"),
        (crate["@graph"], "schema"),
        (dcat["@graph"], "dcat"),
        (prov["@graph"], "prov"),
    ):
        _apply_rights(nodes, kind, rights)
    _staged_references(croissant, crate, dcat, prov, rights)
    return {
        **base,
        "metadata/croissant.json": _json(croissant),
        "ro-crate-metadata.json": _json(crate),
        "metadata/dcat.json": _json(dcat),
        "metadata/prov.json": _json(prov),
    }


def project_release_metadata(
    root: Path, facts: dict[str, Any], resources: list[dict[str, Any]]
) -> dict[str, bytes]:
    """Project supplied facts and resource assertions, without approving them.

    A producer may call this before final metadata hashes exist. Qualification
    subsequently requires the separately pinned complete contract over every
    final member, including these metadata outputs and MANIFEST.json itself.
    """
    _validate(facts, _SCHEMA["$defs"]["facts"])
    for row in resources:
        _validate(row, _SCHEMA["$defs"]["resource"])
    base = project_candidate_inventory(root, reconstruct=True)
    result = _profile_graphs(base, facts, resources)
    inventory = json.loads(base["metadata/payload-inventory.json"])["inventory"]
    tables = json.loads(base["metadata/schemas.json"])["tables"]
    pin = hashlib.sha256(base["metadata/payload-inventory.json"]).hexdigest()
    common = {
        "schema_version": VERSION,
        "inventory_sha256": pin,
        "publication": "not_performed",
    }
    result.update(
        {
            "metadata/catalogue.json": _json(
                {**common, "facts": facts, "inventory": inventory, "tables": tables}
            ),
            "metadata/citations.json": _json(
                {
                    **common,
                    "scope": "included_member_references_not_upstream_source_citations",
                    "records": [
                        {
                            "id": "urn:sha256:" + r["sha256"],
                            "path": r["path"],
                            "payload_sha256": r["sha256"],
                        }
                        for r in inventory
                    ],
                }
            ),
            "metadata/changelog.json": _json(
                {**common, "scope": "snapshot_inventory_only", "records": inventory}
            ),
            "metadata/source_drillthrough.json": _json(
                {
                    **common,
                    "scope": (
                        "included_member_fixity_only_no_upstream_reference_inferred"
                    ),
                    "records": [
                        {"path": r["path"], "reference": "urn:sha256:" + r["sha256"]}
                        for r in inventory
                    ],
                }
            ),
        }
    )
    report = json.loads(base["metadata/profile-validation.json"])
    report.update(
        {
            "schema_version": VERSION,
            "rights": "per_resource_assertions_only",
            "ml_loading": "not_qualified_no_data_loading_performed",
            "release_readiness": "requires_pinned_contract_verification",
            "fact_gaps": [
                k for k in ("url", "date_published", "creators") if facts[k] is None
            ],
            "dataset_wide_licence": "not_asserted",
            "publication_approval": "not_granted",
        }
    )
    report["croissant"]["missing_dataset_properties"] = [
        name
        for key, name in [
            ("url", "url"),
            ("date_published", "datePublished"),
            ("creators", "creator"),
        ]
        if facts[key] is None
    ]
    if report["fact_gaps"]:
        report["croissant"]["missing_dataset_properties"].append("dct:conformsTo")
    report["ro_crate"]["missing_root_properties"] = (
        ["datePublished"] if facts["date_published"] is None else []
    )

    report["unsupported_croissant_arrow_types"] = sorted(
        {
            f["type"]
            for table in tables
            for f in table["fields"]
            if f["type"] not in _CROISSANT_TYPES
        }
    )
    if report["unsupported_croissant_arrow_types"]:
        report["croissant"]["missing_dataset_properties"].append("supported_dataType")
    report["croissant"]["missing_content_urls"] = 0
    report["payload_staging"] = "verified_local_candidate_members"
    report["ro_crate"]["descriptor_conformance_assertion"] = (
        "declared_for_explicit_profile" if not report["fact_gaps"] else "withheld"
    )
    result["metadata/profile-validation.json"] = _json(report)
    _require(set(result) == GENERATED_MEMBERS)
    return result


def _payloads(root: Path, manifest: dict[str, Any]) -> dict[str, bytes]:
    records = manifest.get("files")
    _require(type(records) is list and 0 < len(records) <= MAX_RELEASE_MEMBERS)
    records = cast("list[dict[str, Any]]", records)
    _require(
        all(type(r) is dict and set(r) == {"path", "bytes", "sha256"} for r in records)
    )
    names = [r["path"] for r in records]
    candidate_inventory._unique(names)
    _require(
        "MANIFEST.json" not in names and set(names) >= GENERATED_MEMBERS | {"README.md"}
    )
    result = {}
    total = 0
    for row in records:
        _require(type(row) is dict and set(row) == {"path", "bytes", "sha256"})
        _require(type(row["bytes"]) is int and 0 <= row["bytes"] <= MAX_PAYLOAD_BYTES)
        _safe(root / row["path"])
        body = verified_snapshot(
            root / row["path"], row["sha256"], max_bytes=MAX_PAYLOAD_BYTES
        )
        _require(len(body) == row["bytes"])
        total += len(body)
        _require(total <= MAX_PACKAGE_BYTES)
        result[row["path"]] = body
    nodes = list(islice(root.rglob("*"), MAX_NODES + 1))
    _require(len(nodes) <= MAX_NODES)
    _require(all(not p.is_symlink() and not p.is_junction() for p in nodes))
    _require(
        {p.relative_to(root).as_posix() for p in nodes if p.is_file()}
        == set(result) | {"MANIFEST.json"}
    )
    expected_dirs = {
        parent.as_posix()
        for name in names
        for parent in PurePosixPath(name).parents
        if parent != PurePosixPath(".")
    }
    _require(
        {p.relative_to(root).as_posix() for p in nodes if p.is_dir()} == expected_dirs
    )

    return result


def _evidence(contract: dict[str, Any], inputs: MetadataReleaseInput) -> int:
    pins = {
        r["evidence_sha256"]
        for r in contract["resources"]
        if r["evidence_sha256"] is not None
    }
    if contract["facts_evidence_sha256"] is not None:
        pins.add(contract["facts_evidence_sha256"])
    total = 0
    for pin in pins:
        _safe(inputs.evidence_root / "sha256" / pin[:2] / pin)
        body = verified_snapshot(
            inputs.evidence_root / "sha256" / pin[:2] / pin,
            pin,
            max_bytes=MAX_PAYLOAD_BYTES,
        )
        total += len(body)
        _require(total <= MAX_PACKAGE_BYTES)
    return len(pins)


def verify_release_metadata(
    root: Path, manifest_sha256: str, inputs: MetadataReleaseInput
) -> dict[str, Any]:
    """Verify all-resource assertions and complete profile bindings read-only.

    No caller-supplied success flag substitutes for reconstruction. An approved
    expected contract pin remains the external trust boundary; hash consistency
    cannot establish the legal truth of the supplied evidence or approve release.
    """
    try:
        return _verify(root, manifest_sha256, inputs)
    except (ValueError, OSError, KeyError, TypeError, StopIteration) as error:
        raise ValueError(_ERROR) from error


def _verify(
    root: Path, manifest_sha256: str, inputs: MetadataReleaseInput
) -> dict[str, Any]:
    _safe(root)
    _safe(root / "MANIFEST.json")
    _safe(inputs.contract_path)
    raw = verified_snapshot(
        root / "MANIFEST.json", manifest_sha256, max_bytes=MAX_PAYLOAD_BYTES
    )
    manifest = _load(raw, manifest_sha256)
    validate_release_manifest(manifest)
    _require(manifest.get("dataset") == "edithatogo/nz-health-appropriations")
    contract_raw = verified_snapshot(
        inputs.contract_path, inputs.contract_sha256, max_bytes=2 * 1024 * 1024
    )
    contract = _load(contract_raw, inputs.contract_sha256)
    _validate(contract, _SCHEMA)
    _require(contract["candidate_manifest_sha256"] == manifest_sha256)
    facts = contract["facts"]
    resources = contract["resources"]
    _require(
        manifest.get("version") == facts["version"]
        and manifest.get("metadata_identifier") == facts["identifier"]
    )
    _require(manifest.get("metadata_profile") == VERSION)
    observed = _payloads(root, manifest)
    observed["MANIFEST.json"] = raw
    names = [r["path"] for r in resources]
    candidate_inventory._unique(names)
    _require(set(names) == set(observed))
    _require(
        all(
            hashlib.sha256(observed[r["path"]]).hexdigest() == r["payload_sha256"]
            for r in resources
        )
    )
    count = _evidence(contract, inputs)
    expected = project_release_metadata(root, facts, resources)
    _require(all(observed[name] == payload for name, payload in expected.items()))
    _require(observed["README.md"] == render_card(facts, resources))
    _require(
        verified_snapshot(
            root / "MANIFEST.json", manifest_sha256, max_bytes=MAX_PAYLOAD_BYTES
        )
        == raw
    )
    blockers = [
        f"rights:{r['state']}:{r['path']}"
        for r in resources
        if r["state"] != "eligible_asserted"
    ]
    blockers.extend(
        "metadata_fact_missing:" + k
        for k in ("url", "date_published", "creators")
        if facts[k] is None
    )
    profile = json.loads(expected["metadata/profile-validation.json"])
    blockers.extend(
        "croissant_type_unsupported:" + name
        for name in profile["unsupported_croissant_arrow_types"]
    )
    if contract["facts_evidence_sha256"] is None:
        blockers.append("metadata_fact_evidence_missing")
    result = {
        "schema_version": VERSION,
        "status": "blocked" if blockers else "qualified_for_explicit_gate",
        "candidate_manifest_sha256": manifest_sha256,
        "contract_sha256": inputs.contract_sha256,
        "rights_scope": "all_candidate_members_including_manifest",
        "scope": "metadata_and_resource_assertions_only",
        "source_disposition_validation": "outside_metadata_contract",
        "resources_verified": len(resources),
        "metadata_files_verified": len(expected),
        "evidence_objects_verified": count,
        "rights_validation": (
            "pinned_assertions_and_supplied_evidence_fixity_not_legal_judgment"
        ),
        "licenses": sorted(
            {r["license_uri"] for r in resources if r["license_uri"] is not None}
        ),
        "blockers": sorted(blockers),
        "publication_approval": "not_granted",
        "publication": "not_performed",
        "full_conformance": "not_asserted",
        "ml_loading": "not_qualified",
    }
    _validate(result, _VERIFICATION_SCHEMA)
    return result
