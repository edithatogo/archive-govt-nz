"""Rebuildable local Gold metadata; no source, rights or release approval."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

    import pyarrow as pa

from archive_govt_nz.domains.health_appropriations import (
    budget_comparison_gold as budget,
)
from archive_govt_nz.domains.health_appropriations import (
    fiscal_analytical_gold as fiscal,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

VERSION = "archive-govt-nz.health-gold-metadata/v2"
MAX_BYTES = 16 * 1024 * 1024
MAX_PACKAGES = 8
FILES = {
    "catalogue.json",
    "schemas.json",
    "dcat.jsonld",
    "prov.jsonld",
    "DATASET_CARD.md",
    "citations.json",
    "changelog.json",
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


def _table(name: str, table: pa.Table, package_id: str) -> dict[str, Any]:
    periods = {
        str(value) for value in table["period_end"].to_pylist() if value is not None
    }
    status_field = "state" if "state" in table.column_names else "status"
    statuses = (
        dict(sorted(Counter(table[status_field].to_pylist()).items()))
        if status_field in table.column_names
        else {"source_observation": table.num_rows}
    )
    schema = table.schema.serialize().to_pybytes()
    return {
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


def _package(value: GoldInput) -> dict[str, Any]:
    _require(
        type(value) is GoldInput
        and value.profile in {"budget_comparison", "fiscal_analytical"}
    )
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
    inventory = []
    for name, binding in sorted(bindings.items()):
        payload = verified_snapshot(
            value.root / name, binding["sha256"], max_bytes=MAX_BYTES
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


def project_gold_metadata(values: tuple[GoldInput, ...]) -> dict[str, bytes]:
    """Verify supported packages before returning metadata-only local projections.

    Supplied manifests bind source assertions, not independently reverified Bronze.
    IPC schema bytes preserve nested fields and metadata. Period extrema describe
    observations only, never continuous coverage. No private paths or data rows
    are emitted. Graph contexts are inline; full standards conformance is unasserted.
    """
    _require(type(values) is tuple and 0 < len(values) <= MAX_PACKAGES)
    packages = sorted((_package(v) for v in values), key=lambda p: p["id"])
    _require(len({p["id"] for p in packages}) == len(packages))
    catalogue = _json(
        {
            "schema_version": VERSION,
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
            "schema_version": VERSION,
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
            "schema_version": VERSION,
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
    schemas = _json(
        {
            "schema_version": VERSION,
            "encoding": "arrow_ipc_schema_hex",
            "recordsets": [t for p in packages for t in p["tables"]],
        }
    )
    lines = [
        "# Local Health analytical Gold dataset card",
        "",
        (
            "Pinned Gold snapshots only; Bronze sources and semantics "
            "are not reverified."
        ),
        (
            "Rights are not evaluated; publication is not performed; "
            "release readiness is blocked."
        ),
        "Dates below are observed period-end extrema, not continuous coverage.",
        (
            "No health-input cost deflator, causal inference or performance "
            "variance is asserted."
        ),
        "",
        "| Local citation identifier | Rows | Observed period ends |",
        "| --- | --- | --- |",
    ]
    for p in packages:
        lines.extend(
            f"| {t['id']} | {t['rows']} | "
            f"{t['observed_period_end_min']} to {t['observed_period_end_max']} "
            f"({t['observed_period_end_count']} distinct) |"
            for t in p["tables"]
        )
        lines.extend(["", p["profile"] + " caveats: " + ", ".join(p["caveats"]), ""])
    result = {
        "catalogue.json": catalogue,
        "schemas.json": schemas,
        "dcat.jsonld": _json(dcat),
        "prov.jsonld": _json(prov),
        "DATASET_CARD.md": ("\n".join(lines) + "\n").encode(),
        "citations.json": citations,
        "changelog.json": changelog,
    }
    _require(all(len(b) <= MAX_BYTES for b in result.values()))
    return result


def export_gold_metadata(
    values: tuple[GoldInput, ...], output: Path, *, write: bool = False
) -> dict[str, Any]:
    """Dry run by default; preserve partial evidence and never overwrite inputs."""
    _require(type(values) is tuple and 0 < len(values) <= MAX_PACKAGES)
    for v in values:
        _require(type(v) is GoldInput)
        target, source = output.resolve(), v.root.resolve()
        _require(
            not target.is_relative_to(source) and not source.is_relative_to(target)
        )
    payloads = project_gold_metadata(values)
    marker = _json(
        {
            "schema_version": VERSION,
            "payloads": {
                n: {"sha256": _sha(b), "bytes": len(b)}
                for n, b in sorted(payloads.items())
            },
            "input_manifest_sha256": sorted(v.manifest_sha256 for v in values),
            "rights": "not_evaluated",
            "publication": "not_performed",
        }
    )
    if write:
        output.mkdir(parents=True, exist_ok=False)
        for name, content in {**payloads, "MANIFEST.json": marker}.items():
            with (output / name).open("xb") as stream:
                stream.write(content)
    return {
        "schema_version": VERSION,
        "status": "written" if write else "dry_run",
        "manifest_sha256": _sha(marker),
        "packages": len(values),
        "rights": "not_evaluated",
        "publication": "not_performed",
    }


def verify_gold_metadata(
    values: tuple[GoldInput, ...], output: Path, manifest_sha256: str
) -> dict[str, Any]:
    """Rebuild from verified Gold and compare every retained metadata byte."""
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
