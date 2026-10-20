"""Rebuildable local Gold metadata; no source, rights or release approval."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from dataclasses import dataclass
from itertools import islice
from typing import TYPE_CHECKING, Any

import pyarrow as pa
import pyarrow.parquet as pq

if TYPE_CHECKING:
    from pathlib import Path

from archive_govt_nz.domains.health_appropriations import (
    budget_comparison_gold as budget,
)
from archive_govt_nz.domains.health_appropriations import (
    canonical_gold_queries as canonical,
)
from archive_govt_nz.domains.health_appropriations import (
    canonical_gold_verification as canonical_verifier,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_gold as fiscal,
)
from archive_govt_nz.domains.health_appropriations import (
    operation_context_gold as operation_gold,
)
from archive_govt_nz.domains.health_appropriations.operation_gold_output import (
    reserve_gold_directory,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

VERSION = "archive-govt-nz.health-gold-metadata/v3"
CANONICAL_VERSION = "archive-govt-nz.health-gold-metadata/v4"
OPERATION_VERSION = "archive-govt-nz.health-gold-metadata/v5"
SOURCE_DRILLTHROUGH_VERSION = "archive-govt-nz.health-gold-source-drillthrough/v1"
CANONICAL_SOURCE_DRILLTHROUGH_VERSION = (
    "archive-govt-nz.health-gold-source-drillthrough/v2"
)
OPERATION_SOURCE_DRILLTHROUGH_VERSION = (
    "archive-govt-nz.health-gold-source-drillthrough/v3"
)
MAX_BYTES = 16 * 1024 * 1024
MAX_PACKAGES = 8
SHA256_HEX_LENGTH = 64
FILES = {
    "catalogue.json",
    "schemas.json",
    "dcat.jsonld",
    "prov.jsonld",
    "DATASET_CARD.md",
    "citations.json",
    "changelog.json",
    "source_drillthrough.json",
}
SOURCE_HASH_FIELDS = {
    "source_manifest_sha256",
    "source_object_sha256",
    "raw_manifest_sha256",
}
CONTEXT = {
    "dcat": "http://www.w3.org/ns/dcat#",
    "dct": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "spdx": "http://spdx.org/rdf/terms#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
}


@dataclass(frozen=True)
class GoldInput:
    """One explicit supported local Gold package and its exact manifest pin."""

    profile: str
    root: Path
    manifest_sha256: str


@dataclass(frozen=True)
class OperationContextGoldInput:
    """Gold/input pins and trusted Bronze scope for source re-verification."""

    root: Path
    manifest_sha256: str
    operations: tuple[operation_gold.OperationContextInput, ...]
    source_root: Path

    @property
    def profile(self) -> str:
        """Expose the fixed source-regenerated metadata profile identity."""
        return "operation_context"


type MetadataInput = GoldInput | OperationContextGoldInput


def with_canonical_input(
    values: tuple[GoldInput, ...], root: Path | None, pin: str | None
) -> tuple[GoldInput, ...]:
    """Append one explicit canonical input; reject half-specified pairs."""
    if root is None or pin is None:
        _require(root is None and pin is None)
        return values
    return (*values, GoldInput("canonical_source_separated", root, pin))


def _require(condition: object) -> None:
    if not condition:
        message = "gold_metadata_contract"
        raise ValueError(message)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()


def _sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _source_references(
    value: object, path: str = "", *, operation_context: bool = False
) -> list[dict[str, str]]:
    """Copy only explicitly named source references from a verified manifest."""
    references: list[dict[str, str]] = []
    hash_fields = SOURCE_HASH_FIELDS | (
        {"operation_manifest_sha256"} if operation_context else set()
    )
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}/{key.replace('~', '~0').replace('/', '~1')}"
            if isinstance(child, str):
                if key in hash_fields:
                    _require(
                        re.fullmatch(r"[a-f0-9]{64}", child) is not None
                        and len(child) == SHA256_HEX_LENGTH
                    )
                    references.append(
                        {
                            "field_path": child_path,
                            "kind": "sha256",
                            "value": child,
                        }
                    )
                elif key.endswith(("_source_url", "_definition_url")) or (
                    operation_context and key == "source_locator"
                ):
                    _require(
                        child.startswith("https://")
                        and not any(character.isspace() for character in child)
                    )
                    references.append(
                        {
                            "field_path": child_path,
                            "kind": "recorded_https_locator",
                            "value": child,
                        }
                    )
            references.extend(
                _source_references(
                    child, child_path, operation_context=operation_context
                )
            )
    elif isinstance(value, list):
        for index, child in enumerate(value):
            references.extend(
                _source_references(
                    child, f"{path}/{index}", operation_context=operation_context
                )
            )
    return sorted(
        references, key=lambda item: (item["field_path"], item["kind"], item["value"])
    )


def _table(
    name: str, table: pa.Table, package_id: str, *, nullable_status: bool = False
) -> dict[str, Any]:
    periods = {
        str(value)
        for value in (
            table["period_end"].to_pylist()
            if "period_end" in table.column_names
            else []
        )
        if value is not None
    }
    status_field = "state" if "state" in table.column_names else "status"
    observed = (
        table[status_field].to_pylist() if status_field in table.column_names else None
    )
    statuses = (
        dict(
            sorted(
                Counter(
                    v for v in observed if not nullable_status or v is not None
                ).items()
            )
        )
        if observed is not None
        else {"source_observation": table.num_rows}
    )
    schema = table.schema.serialize().to_pybytes()
    descriptor = {
        "id": package_id + ":" + name,
        "path": name,
        "rows": table.num_rows,
        "states": statuses,
        "observed_period_end_count": len(periods),
        "observed_period_end_min": min(periods) if periods else None,
        "observed_period_end_max": max(periods) if periods else None,
        "schema_sha256": _sha(schema),
        "schema_ipc_hex": schema.hex(),
        "fields": [
            {"name": f.name, "type": str(f.type), "nullable": f.nullable}
            for f in table.schema
        ],
    }
    if nullable_status:
        descriptor["null_status_rows"] = observed.count(None) if observed else 0
        descriptor["status_field"] = status_field if observed is not None else None
        if observed is None:
            descriptor["states"] = {}
    return descriptor


def _inventory(
    value: GoldInput,
    marker_name: str,
    marker: bytes,
    bindings: dict[str, Any],
    *,
    max_bytes: int = MAX_BYTES,
) -> list[dict[str, Any]]:
    inventory = []
    for name, binding in sorted(bindings.items()):
        payload = verified_snapshot(
            value.root / name, binding["sha256"], max_bytes=max_bytes
        )
        _require(len(payload) == binding["bytes"])
        inventory.append(
            {"path": name, "sha256": binding["sha256"], "bytes": len(payload)}
        )
    inventory.append(
        {"path": marker_name, "sha256": value.manifest_sha256, "bytes": len(marker)}
    )
    verified_snapshot(
        value.root / marker_name, value.manifest_sha256, max_bytes=MAX_BYTES
    )
    return inventory


def _canonical_package(value: GoldInput) -> dict[str, Any]:
    _require(
        canonical_verifier.verify_canonical_gold_package(
            value.root, value.manifest_sha256
        )["status"]
        == "verified"
    )
    marker = verified_snapshot(
        value.root / "MANIFEST.json",
        value.manifest_sha256,
        max_bytes=canonical_verifier.MAX_MANIFEST_BYTES,
    )
    manifest = json.loads(marker)
    _require(
        manifest.get("rights_state") == "not_evaluated"
        and manifest.get("publication") == "not_performed"
        and bool(manifest["products"])
        and set(manifest["products"]) <= set(canonical.PRODUCTS)
    )
    package_id = "urn:archive-govt-nz:health:gold:" + value.manifest_sha256
    tables = []
    for product in sorted(manifest["products"]):
        table = canonical.read_canonical_gold_product(
            value.root, value.manifest_sha256, product
        )
        name = canonical.PRODUCTS[product][0]
        descriptor = _table(name, table, package_id)
        descriptor.update(
            period_basis=(
                "replayed_biff8_year_integer_rendered_as_string"
                if product in {"biff8_budget", "biff8_revenue"}
                else "source_tokens_not_interpreted"
            ),
            observed_period_tokens=sorted(
                {v for v in table["period_token"].to_pylist() if v is not None}
            ),
        )
        del table
        tables.append(descriptor)
    inventory = _inventory(
        value,
        "MANIFEST.json",
        marker,
        manifest["outputs"],
        max_bytes=canonical.MAX_BYTES,
    )
    return {
        "id": package_id,
        "profile": value.profile,
        "gold_schema_version": manifest["schema_version"],
        "manifest_sha256": value.manifest_sha256,
        "inventory": sorted(inventory, key=lambda item: item["path"]),
        "tables": sorted(tables, key=lambda item: item["path"]),
        "caveats": [
            "source_tokens_not_interpreted_as_dates",
            "classification_mapping_not_inferred",
            "revision_interpretation_not_assessed",
            "cross_source_comparison_not_performed",
            "producer_metadata_not_replaced",
        ],
        "verification_scope": "pinned_gold_package_snapshots",
        "source_reverification": "not_performed",
        "source_semantics": "not_reassessed",
        "source_references": _source_references(manifest),
        "rights": manifest["rights_state"],
        "publication": manifest["publication"],
    }


def _operation_package(value: OperationContextGoldInput) -> dict[str, Any]:
    try:
        verified = operation_gold.read_verified_operation_context_gold(
            value.operations,
            value.source_root,
            value.root,
            manifest_sha256=value.manifest_sha256,
        )
    except ValueError:
        message = "gold_metadata_contract"
        raise ValueError(message) from None
    manifest = verified.manifest
    _require(
        manifest["rights_state"] == "not_evaluated"
        and manifest["publication"] == "not_performed"
        and _sha(verified.manifest_bytes) == value.manifest_sha256
    )
    package_id = "urn:archive-govt-nz:health:gold:" + value.manifest_sha256
    tables = []
    inventory = []
    for name, payload in sorted(verified.products.items()):
        inventory.append({"path": name, "sha256": _sha(payload), "bytes": len(payload)})
        if not name.endswith(".parquet"):
            continue
        table = pq.read_table(pa.BufferReader(payload))
        descriptor = _table(name, table, package_id, nullable_status=True)
        descriptor.update(
            record_kind=(
                "field_lineage"
                if name.startswith("canonical_") and name.endswith("_lineage.parquet")
                else "canonical_fact"
                if name.startswith("canonical_")
                else "context_observation"
                if name == "context_observations.parquet"
                else "coverage_summary"
                if name == "context_coverage.parquet"
                else "quality_summary"
            ),
            period_basis="source_tokens_not_interpreted",
            period_token_field_present="period_token" in table.column_names,
            observed_period_tokens=sorted(
                {v for v in table["period_token"].to_pylist() if v is not None}
            )
            if "period_token" in table.column_names
            else [],
        )
        tables.append(descriptor)
    inventory.append(
        {
            "path": "MANIFEST.json",
            "sha256": value.manifest_sha256,
            "bytes": len(verified.manifest_bytes),
        }
    )
    return {
        "id": package_id,
        "profile": value.profile,
        "gold_schema_version": manifest["schema_version"],
        "manifest_sha256": value.manifest_sha256,
        "inventory": sorted(inventory, key=lambda item: item["path"]),
        "tables": tables,
        "caveats": [
            "source_period_tokens_not_continuous_coverage",
            "null_publisher_status_count_retained_without_invented_status",
            "source_semantics_and_rights_not_reassessed",
            "currency_denominator_and_cross_source_joins_not_admitted",
        ],
        "verification_scope": "source_regenerated_canonical_products",
        "source_reverification": "performed_from_pinned_Bronze",
        "source_semantics": "not_reassessed",
        "source_references": _source_references(manifest, operation_context=True),
        "rights": manifest["rights_state"],
        "publication": manifest["publication"],
    }


def _package(value: MetadataInput) -> dict[str, Any]:
    if type(value) is OperationContextGoldInput:
        return _operation_package(value)
    if type(value) is GoldInput:
        return _snapshot_package(value)
    message = "gold_metadata_contract"
    raise ValueError(message)


def _snapshot_package(value: GoldInput) -> dict[str, Any]:
    _require(
        type(value) is GoldInput
        and value.profile
        in {"budget_comparison", "fiscal_analytical", "canonical_source_separated"}
    )
    if value.profile == "canonical_source_separated":
        return _canonical_package(value)
    if value.profile == "budget_comparison":
        table, summary = budget.read_budget_comparison(
            value.root, value.manifest_sha256
        )
        tables = {"comparison.parquet": table}
        marker_name = "MANIFEST.json"
        caveats = summary["comparison_receipt"]["caveats"]
        version = budget.VERSION
    else:
        tables = {
            name + ".parquet": fiscal.read_fiscal_analytical_gold(
                value.root, value.manifest_sha256, table=name
            )
            for name in fiscal.TABLE_SCHEMAS
        }
        marker_name = "manifest.json"
        caveats = [
            "source_qualifications_retained_in_gold_rows_and_manifest",
            "health_input_cost_deflator_not_asserted",
            "currency_iso_not_asserted",
            "not_causal_or_performance_inference",
        ]
        version = fiscal.VERSION
    marker = verified_snapshot(
        value.root / marker_name, value.manifest_sha256, max_bytes=MAX_BYTES
    )
    manifest = json.loads(marker)
    _require(
        manifest.get("rights") == "not_evaluated"
        and manifest.get("publication") == "not_performed"
    )
    bindings = (
        manifest["payloads"]
        if value.profile == "budget_comparison"
        else {entry["filename"]: entry for entry in manifest["tables"].values()}
    )
    inventory = _inventory(value, marker_name, marker, bindings)
    package_id = "urn:archive-govt-nz:health:gold:" + value.manifest_sha256
    return {
        "id": package_id,
        "profile": value.profile,
        "gold_schema_version": version,
        "manifest_sha256": value.manifest_sha256,
        "inventory": sorted(inventory, key=lambda item: item["path"]),
        "tables": [
            _table(name, table, package_id) for name, table in sorted(tables.items())
        ],
        "caveats": caveats,
        "verification_scope": "pinned_gold_package_snapshots",
        "source_reverification": "not_performed",
        "source_semantics": "not_reassessed",
        "source_references": _source_references(manifest),
        "rights": manifest["rights"],
        "publication": manifest["publication"],
    }


def _graphs(
    packages: list[dict[str, Any]], catalogue_pin: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    dcat, prov = [], []
    for package in packages:
        members = [
            {"@id": package["id"] + ":" + item["path"]} for item in package["inventory"]
        ]
        prov.append(
            {
                "@id": package["id"],
                "@type": "prov:Collection",
                "prov:hadMember": members,
            }
        )
        prov.extend({"@id": m["@id"], "@type": "prov:Entity"} for m in members)
        for table in package["tables"]:
            item = next(i for i in package["inventory"] if i["path"] == table["path"])
            distribution = table["id"] + ":distribution"
            dcat.extend(
                [
                    {
                        "@id": table["id"],
                        "@type": "dcat:Dataset",
                        "dct:identifier": table["id"],
                        "dct:title": package["profile"] + ": " + table["path"],
                        "dcat:distribution": {"@id": distribution},
                    },
                    {
                        "@id": distribution,
                        "@type": "dcat:Distribution",
                        "dcat:mediaType": {
                            "@id": "https://www.iana.org/assignments/media-types/application/vnd.apache.parquet"
                        },
                        "dcat:byteSize": {
                            "@value": str(item["bytes"]),
                            "@type": "xsd:nonNegativeInteger",
                        },
                        "spdx:checksum": {
                            "@type": "spdx:Checksum",
                            "spdx:algorithm": {"@id": "spdx:checksumAlgorithm_sha256"},
                            "spdx:checksumValue": {
                                "@value": item["sha256"],
                                "@type": "xsd:hexBinary",
                            },
                        },
                    },
                ]
            )
    prov.append(
        {
            "@id": "urn:archive-govt-nz:health:metadata:" + catalogue_pin,
            "@type": "prov:Entity",
            "prov:wasDerivedFrom": [{"@id": p["id"]} for p in packages],
        }
    )
    return (
        {"@context": CONTEXT, "@graph": sorted(dcat, key=lambda n: n["@id"])},
        {"@context": CONTEXT, "@graph": sorted(prov, key=lambda n: n["@id"])},
    )


def _period_text(table: dict[str, Any]) -> str:
    if table.get("period_token_field_present") is False:
        return "not applicable: no period-token field"
    if "observed_period_tokens" in table:
        return (
            f"{len(table['observed_period_tokens'])} distinct source tokens "
            "(not date-interpreted)"
        )
    return (
        f"{table['observed_period_end_min']} to {table['observed_period_end_max']} "
        f"({table['observed_period_end_count']} distinct)"
    )


def _version(values: tuple[MetadataInput, ...]) -> str:
    if any(type(v) is OperationContextGoldInput for v in values):
        return OPERATION_VERSION
    return (
        CANONICAL_VERSION
        if any(v.profile == "canonical_source_separated" for v in values)
        else VERSION
    )


def project_gold_metadata(values: tuple[MetadataInput, ...]) -> dict[str, bytes]:
    """Verify supported packages before returning metadata-only local projections.

    Operation-context inputs are regenerated from pinned Bronze; other profiles
    bind recorded source assertions through verified Gold snapshots.
    IPC schema bytes preserve nested fields and metadata. Period extrema describe
    observations only, never continuous coverage. No private paths or data rows
    are emitted. Graph contexts are inline; full standards conformance is unasserted.
    """
    _require(type(values) is tuple and 0 < len(values) <= MAX_PACKAGES)
    packages = sorted((_package(v) for v in values), key=lambda p: p["id"])
    _require(len({p["id"] for p in packages}) == len(packages))
    version = _version(values)
    catalogue = _json(
        {
            "schema_version": version,
            "packages": packages,
            "release_readiness": "blocked_unassessed_rights_and_publication",
            "rights": "not_evaluated",
            "publication": "not_performed",
            "full_standards_conformance": "not_asserted",
            "citation_scope": "local_content_addressed_identifiers_only",
        }
    )
    dcat, prov = _graphs(packages, _sha(catalogue))
    citations = _json(
        {
            "schema_version": version,
            "scope": "local_content_addressed_gold_packages",
            "source_citation": "not_asserted",
            "records": [
                {
                    "package_id": p["id"],
                    "profile": p["profile"],
                    "manifest_sha256": p["manifest_sha256"],
                    "identifier_scope": p["verification_scope"],
                    "rights": p["rights"],
                    "publication": p["publication"],
                }
                for p in packages
            ],
        }
    )
    changelog = _json(
        {
            "schema_version": version,
            "comparison": "snapshot_only_no_prior_version_comparison",
            "federation": "no_approved_links_emitted",
            "packages": [
                {
                    "package_id": p["id"],
                    "profile": p["profile"],
                    "manifest_sha256": p["manifest_sha256"],
                    "gold_schema_version": p["gold_schema_version"],
                    "tables": [
                        {"path": t["path"], "rows": t["rows"]} for t in p["tables"]
                    ],
                    "rights": p["rights"],
                    "publication": p["publication"],
                    "change_status": "current_verified_snapshot",
                }
                for p in packages
            ],
        }
    )
    source_drillthrough = _json(
        {
            "schema_version": (
                OPERATION_SOURCE_DRILLTHROUGH_VERSION
                if version == OPERATION_VERSION
                else CANONICAL_SOURCE_DRILLTHROUGH_VERSION
                if version == CANONICAL_VERSION
                else SOURCE_DRILLTHROUGH_VERSION
            ),
            "scope": "source_manifest_field_references_only",
            "rights": "not_evaluated",
            "publication": "not_performed",
            "locator_semantics": "recorded_reference_only_no_access_or_rights_claim",
            "packages": [
                {
                    "package_id": p["id"],
                    "profile": p["profile"],
                    "manifest_sha256": p["manifest_sha256"],
                    "references": p["source_references"],
                    "no_reference_reason": (
                        None
                        if p["source_references"]
                        else "source_reference_fields_absent_from_package_manifest"
                    ),
                }
                for p in packages
            ],
        }
    )
    schemas = _json(
        {
            "schema_version": version,
            "encoding": "arrow_ipc_schema_hex",
            "recordsets": [t for p in packages for t in p["tables"]],
        }
    )
    has_tokens = any(
        p["profile"] in {"canonical_source_separated", "operation_context"}
        for p in packages
    )
    has_operation = any(p["profile"] == "operation_context" for p in packages)
    lines = [
        "# Local Health analytical Gold dataset card",
        "",
        (
            "Operation-context Bronze inputs are reverified; other profiles retain "
            "snapshot verification only. Source semantics are not reassessed."
            if has_operation
            else "Pinned Gold snapshots only; Bronze sources and semantics "
            "are not reverified."
        ),
        (
            "Rights are not evaluated; publication is not performed; "
            "release readiness is blocked."
        ),
        (
            "Observed dates and literal source tokens are not continuous coverage."
            if has_tokens
            else "Dates below are observed period-end extrema, not continuous coverage."
        ),
        (
            "No health-input cost deflator, causal inference or performance "
            "variance is asserted."
        ),
        "",
        (
            "| Local citation identifier | Rows | Observed periods |"
            if has_tokens
            else "| Local citation identifier | Rows | Observed period ends |"
        ),
        "| --- | --- | --- |",
    ]
    for p in packages:
        lines.extend(
            f"| {t['id']} | {t['rows']} | {_period_text(t)} |" for t in p["tables"]
        )
        if not has_operation:
            lines.extend(
                ["", p["profile"] + " caveats: " + ", ".join(p["caveats"]), ""]
            )
    if has_operation:
        for p in packages:
            lines.extend(
                ["", p["profile"] + " caveats: " + ", ".join(p["caveats"]), ""]
            )
    result = {
        "catalogue.json": catalogue,
        "schemas.json": schemas,
        "dcat.jsonld": _json(dcat),
        "prov.jsonld": _json(prov),
        "DATASET_CARD.md": ("\n".join(lines) + "\n").encode(),
        "citations.json": citations,
        "changelog.json": changelog,
        "source_drillthrough.json": source_drillthrough,
    }
    _require(all(len(b) <= MAX_BYTES for b in result.values()))
    return result


def _metadata_marker(
    values: tuple[MetadataInput, ...], payloads: dict[str, bytes]
) -> bytes:
    return _json(
        {
            "schema_version": _version(values),
            "payloads": {
                n: {"sha256": _sha(b), "bytes": len(b)}
                for n, b in sorted(payloads.items())
            },
            "input_manifest_sha256": sorted(v.manifest_sha256 for v in values),
            "rights": "not_evaluated",
            "publication": "not_performed",
        }
    )


def _safe_metadata_path(path: Path) -> None:
    _require(not any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)))


def _operation_output_scope(values: tuple[MetadataInput, ...], output: Path) -> None:
    _require(all(type(v) in {GoldInput, OperationContextGoldInput} for v in values))
    _safe_metadata_path(output)
    target = output.resolve()
    for value in values:
        protected = [value.root]
        if type(value) is OperationContextGoldInput:
            protected.extend(
                [value.source_root, *(item.package_dir for item in value.operations)]
            )
        for root in protected:
            source = root.resolve()
            _require(
                not target.is_relative_to(source) and not source.is_relative_to(target)
            )


def _operation_metadata_readback(
    output: Path, pin: str, marker: bytes, payloads: dict[str, bytes]
) -> None:
    _safe_metadata_path(output)
    _require(isinstance(pin, str) and re.fullmatch(r"[a-f0-9]{64}", pin))
    _require(_sha(marker) == pin)
    _require(
        {p.name for p in islice(output.iterdir(), len(payloads) + 2)}
        == {"MANIFEST.json", *payloads}
    )
    path = output / "MANIFEST.json"
    _safe_metadata_path(path)
    _require(verified_snapshot(path, pin, max_bytes=len(marker)) == marker)
    for name, content in payloads.items():
        member = output / name
        _safe_metadata_path(member)
        _require(
            verified_snapshot(member, _sha(content), max_bytes=len(content)) == content
        )
    _require(verified_snapshot(path, pin, max_bytes=len(marker)) == marker)


def _export_operation_metadata(
    values: tuple[MetadataInput, ...], output: Path, *, write: bool
) -> dict[str, Any]:
    _require(type(write) is bool)
    _operation_output_scope(values, output)
    if write:
        _require(output.parent.is_dir() and not output.exists())
    payloads = project_gold_metadata(values)
    marker = _metadata_marker(values, payloads)
    pin = _sha(marker)
    if write:
        with reserve_gold_directory(output) as directory:
            for name, content in payloads.items():
                directory.write(name, content)
            directory.write("MANIFEST.json", marker)
            _operation_metadata_readback(output, pin, marker, payloads)
    return {
        "schema_version": _version(values),
        "status": "written" if write else "dry_run",
        "manifest_sha256": pin,
        "packages": len(values),
        "rights": "not_evaluated",
        "publication": "not_performed",
    }


def export_gold_metadata(
    values: tuple[MetadataInput, ...], output: Path, *, write: bool = False
) -> dict[str, Any]:
    """Dry run by default; preserve partial evidence and never overwrite inputs."""
    _require(type(values) is tuple and 0 < len(values) <= MAX_PACKAGES)
    if any(type(v) is OperationContextGoldInput for v in values):
        return _export_operation_metadata(values, output, write=write)
    for v in values:
        _require(type(v) is GoldInput)
        target, source = output.resolve(), v.root.resolve()
        _require(
            not target.is_relative_to(source) and not source.is_relative_to(target)
        )
    payloads = project_gold_metadata(values)
    version = _version(values)
    marker = _metadata_marker(values, payloads)
    if write:
        output.mkdir(parents=True, exist_ok=False)
        for name, content in {**payloads, "MANIFEST.json": marker}.items():
            with (output / name).open("xb") as stream:
                stream.write(content)
    return {
        "schema_version": version,
        "status": "written" if write else "dry_run",
        "manifest_sha256": _sha(marker),
        "packages": len(values),
        "rights": "not_evaluated",
        "publication": "not_performed",
    }


def verify_gold_metadata(
    values: tuple[MetadataInput, ...], output: Path, manifest_sha256: str
) -> dict[str, Any]:
    """Rebuild from verified Gold and compare every retained metadata byte."""
    _require(type(values) is tuple and 0 < len(values) <= MAX_PACKAGES)
    if any(type(v) is OperationContextGoldInput for v in values):
        _operation_output_scope(values, output)
        payloads = project_gold_metadata(values)
        marker = _metadata_marker(values, payloads)
        _operation_metadata_readback(output, manifest_sha256, marker, payloads)
        return {
            "schema_version": _version(values),
            "status": "verified",
            "manifest_sha256": manifest_sha256,
            "packages": len(values),
            "rights": "not_evaluated",
            "publication": "not_performed",
            "verification_scope": "source_regenerated_gold_metadata_reconstructed",
        }
    _require(not output.is_symlink() and output.is_dir())
    _require({p.name for p in output.iterdir()} == FILES | {"MANIFEST.json"})
    marker = verified_snapshot(
        output / "MANIFEST.json", manifest_sha256, max_bytes=MAX_BYTES
    )
    expected = export_gold_metadata(values, output)
    _require(expected["manifest_sha256"] == manifest_sha256)
    manifest = json.loads(marker)
    payloads = project_gold_metadata(values)
    for name, content in payloads.items():
        binding = manifest["payloads"][name]
        snapshot = verified_snapshot(
            output / name, binding["sha256"], max_bytes=MAX_BYTES
        )
        _require(len(snapshot) == binding["bytes"] and snapshot == content)
    verified_snapshot(output / "MANIFEST.json", manifest_sha256, max_bytes=MAX_BYTES)
    return {
        **expected,
        "status": "verified",
        "verification_scope": "gold_reverified_metadata_reconstructed",
    }
