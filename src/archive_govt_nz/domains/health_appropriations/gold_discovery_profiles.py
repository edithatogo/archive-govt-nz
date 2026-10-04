"""Verified local discovery candidates with explicit missing standards properties."""

from __future__ import annotations

import hashlib
import json
from itertools import islice
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.gold_metadata import (
    MAX_BYTES,
    GoldInput,
    project_gold_metadata,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

VERSION = "archive-govt-nz.health-gold-discovery-candidates/v1"
FILES = {"croissant.json", "ro-crate-metadata.json", "profile-validation.json"}
CONTEXT = {
    "@vocab": "http://schema.org/",
    "cr": "http://mlcommons.org/croissant/",
    "hag": "urn:archive-govt-nz:health:discovery:",
    "File": "http://schema.org/MediaObject",
}
MEDIA = {
    ".parquet": "application/vnd.apache.parquet",
    ".json": "application/json",
    ".md": "text/markdown",
    ".png": "image/png",
}


def _require(condition: object) -> None:
    if not condition:
        message = "gold_discovery_profile_contract"
        raise ValueError(message)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()


def _sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def project_profiles(
    values: tuple[GoldInput, ...],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Read Gold before constructing inventory candidates; never claim full validity.

    Absolute content IDs describe externally retained local files, not staged
    payloads or download URLs. Custom Arrow type IRIs preserve physical meaning;
    they are not a tested ML loader mapping. Exact IPC schemas remain attached.
    Required licence, creator, URL and publication properties are intentionally
    absent until evidenced. Inline contexts require no network or context cache.
    """
    catalogue = json.loads(project_gold_metadata(values)["catalogue.json"])
    distributions, files, records = [], [], []
    for package in catalogue["packages"]:
        for item in package["inventory"]:
            identity = package["id"] + ":" + item["path"]
            media = MEDIA[
                next(suffix for suffix in MEDIA if item["path"].endswith(suffix))
            ]
            common = {
                "@id": identity,
                "name": item["path"],
                "encodingFormat": media,
                "sha256": item["sha256"],
            }
            distributions.append(
                {**common, "@type": "cr:FileObject", "contentSize": str(item["bytes"])}
            )
            files.append({**common, "@type": "File", "contentSize": str(item["bytes"])})
        for table in package["tables"]:
            record_id = table["id"] + ":recordset"
            fields = [
                {
                    "@id": record_id + "/" + field["name"],
                    "@type": "cr:Field",
                    "name": field["name"],
                    "cr:dataType": {
                        "@id": "urn:archive-govt-nz:health:arrow-type:"
                        + _sha(field["type"].encode())
                    },
                    "hag:arrowType": field["type"],
                    "hag:nullable": field["nullable"],
                    "cr:source": {
                        "cr:fileObject": {"@id": table["id"]},
                        "cr:extract": {"cr:column": field["name"]},
                    },
                }
                for field in table["fields"]
            ]
            records.append(
                {
                    "@id": record_id,
                    "@type": "cr:RecordSet",
                    "name": package["profile"] + ": " + table["path"],
                    "cr:field": fields,
                    "hag:arrowSchemaSha256": table["schema_sha256"],
                    "hag:arrowSchemaIpcHex": table["schema_ipc_hex"],
                }
            )
    description = (
        "Local Gold inventory candidate. Payloads remain in separately "
        "pinned Gold packages; rights and publication are unassessed."
    )
    croissant = {
        "@context": dict(CONTEXT),
        "@type": "Dataset",
        "name": "Local Health analytical Gold discovery candidate",
        "description": description,
        "distribution": distributions,
        "cr:recordSet": records,
    }
    crate = {
        "@context": dict(CONTEXT),
        "@graph": [
            {
                "@id": "ro-crate-metadata.json",
                "@type": "CreativeWork",
                "about": {"@id": "./"},
            },
            {
                "@id": "./",
                "@type": "Dataset",
                "name": "Local Health analytical Gold inventory candidate",
                "description": description,
                "hasPart": [{"@id": item["@id"]} for item in files],
            },
            *files,
        ],
    }
    report = {
        "schema_version": VERSION,
        "status": "passed_local_inventory_contract",
        "full_conformance": "not_asserted",
        "release_readiness": "blocked",
        "rights": "not_evaluated",
        "publication": "not_performed",
        "source_reverification": "not_performed",
        "payload_staging": "not_performed",
        "ml_loading": "not_validated_custom_arrow_type_identifiers",
        "recordsets": len(records),
        "fields": sum(len(record["cr:field"]) for record in records),
        "file_objects": len(distributions),
        "croissant": {
            "target_specification": "http://mlcommons.org/croissant/1.0",
            "missing_dataset_properties": [
                "creator",
                "datePublished",
                "dct:conformsTo",
                "license",
                "url",
            ],
            "missing_content_urls": len(distributions),
        },
        "ro_crate": {
            "target_specification": "https://w3id.org/ro/crate/1.1",
            "missing_root_properties": ["datePublished", "license"],
            "descriptor_conformance_assertion": "withheld",
        },
        "input_manifest_sha256": sorted(
            p["manifest_sha256"] for p in catalogue["packages"]
        ),
    }
    _require(all(len(_json(v)) <= MAX_BYTES for v in (croissant, crate, report)))
    return croissant, crate, report


def validate_documents(
    values: tuple[GoldInput, ...], croissant: dict[str, Any], crate: dict[str, Any]
) -> dict[str, Any]:
    """Reject changed identity, extraction, types or unsupported promotion claims."""
    expected_cr, expected_ro, report = project_profiles(values)
    _require(
        _json(croissant) == _json(expected_cr) and _json(crate) == _json(expected_ro)
    )
    return report


def _payloads(values: tuple[GoldInput, ...]) -> tuple[dict[str, bytes], bytes]:
    cr, ro, report = project_profiles(values)
    data = {
        "croissant.json": _json(cr),
        "ro-crate-metadata.json": _json(ro),
        "profile-validation.json": _json(report),
    }
    marker = _json(
        {
            "schema_version": VERSION,
            "payloads": {
                n: {"sha256": _sha(b), "bytes": len(b)} for n, b in sorted(data.items())
            },
            "input_manifest_sha256": report["input_manifest_sha256"],
            "full_conformance": "not_asserted",
            "release_readiness": "blocked",
        }
    )
    return data, marker


def export_profiles(
    values: tuple[GoldInput, ...], output: Path, *, write: bool = False
) -> dict[str, Any]:
    """Dry run verifies Gold; writing preserves exclusive output and partials."""
    data, marker = _payloads(values)
    for value in values:
        target, source = output.resolve(), value.root.resolve()
        _require(
            not target.is_relative_to(source) and not source.is_relative_to(target)
        )
    if write:
        output.mkdir(parents=True, exist_ok=False)
        for name, content in {**data, "MANIFEST.json": marker}.items():
            with (output / name).open("xb") as handle:
                handle.write(content)
    return {
        "schema_version": VERSION,
        "status": "written" if write else "dry_run",
        "manifest_sha256": _sha(marker),
        "release_readiness": "blocked",
        "full_conformance": "not_asserted",
    }


def verify_profiles(
    values: tuple[GoldInput, ...], output: Path, manifest_sha256: str
) -> dict[str, Any]:
    """Reverify Gold and reconstruct every candidate byte from its pinned inputs."""
    _require(output.is_dir() and not output.is_symlink())
    _require({p.name for p in islice(output.iterdir(), 5)} == FILES | {"MANIFEST.json"})
    _require(
        all(not (output / name).is_symlink() for name in FILES | {"MANIFEST.json"})
    )
    marker = verified_snapshot(
        output / "MANIFEST.json", manifest_sha256, max_bytes=MAX_BYTES
    )
    data, expected_marker = _payloads(values)
    _require(marker == expected_marker)
    manifest = json.loads(marker)
    for name, expected in data.items():
        binding = manifest["payloads"][name]
        actual = verified_snapshot(
            output / name, binding["sha256"], max_bytes=MAX_BYTES
        )
        _require(actual == expected and len(actual) == binding["bytes"])
    verified_snapshot(output / "MANIFEST.json", manifest_sha256, max_bytes=MAX_BYTES)
    return {
        "schema_version": VERSION,
        "status": "verified_local_candidates",
        "manifest_sha256": manifest_sha256,
        "release_readiness": "blocked",
        "full_conformance": "not_asserted",
    }
