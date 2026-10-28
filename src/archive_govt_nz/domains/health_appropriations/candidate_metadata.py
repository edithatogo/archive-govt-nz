# SPDX-License-Identifier: Apache-2.0
"""Observed candidate schemas and inventory projections without release claims."""

# ruff: noqa: SLF001 -- reuse the existing candidate portable-path boundary.

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from itertools import islice
from typing import TYPE_CHECKING, Any, cast

import pyarrow.parquet as pq

from archive_govt_nz.domains.health_appropriations import candidate_inventory
from archive_govt_nz.domains.health_appropriations.gold_discovery_profiles import (
    project_inventory_candidates,
)
from archive_govt_nz.domains.health_appropriations.gold_metadata import (
    project_inventory_graphs,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    read_regular_snapshot,
    verified_snapshot,
)

if TYPE_CHECKING:
    from pathlib import Path

VERSION = "archive-govt-nz.health-candidate-inventory-metadata/v1"
MAX_MEMBERS = 128
MAX_PAYLOAD_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_FIELDS = 256
GENERATED_MEMBERS = frozenset(
    {
        "metadata/payload-inventory.json",
        "metadata/schemas.json",
        "metadata/croissant.json",
        "ro-crate-metadata.json",
        "metadata/dcat.json",
        "metadata/prov.json",
        "metadata/profile-validation.json",
    }
)
MAX_PACKAGE_BYTES = 128 * 1024 * 1024
MAX_NODES = (MAX_MEMBERS + len(GENERATED_MEMBERS)) * 8
EXTENDED_MEMBERS = frozenset(
    {
        "metadata/catalogue.json",
        "metadata/citations.json",
        "metadata/changelog.json",
        "metadata/source_drillthrough.json",
    }
)
_ERROR = "candidate_metadata_contract"


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()


def project_candidate_inventory(
    root: Path, *, reconstruct: bool = False
) -> dict[str, bytes]:
    """Observe bounded local payloads and describe their actual Arrow schemas.

    No files are written. The supplied root is operator-selected, not a sandbox
    against concurrent hostile changes. The caller must recheck payload hashes
    before saving a final candidate manifest. No rights, source authority,
    publication date, activities or standards conformance are inferred.
    """
    _require(type(reconstruct) is bool)
    _require(root.is_dir() and not root.is_symlink() and not root.is_junction())
    paths = []
    for count, path in enumerate(islice(root.rglob("*"), MAX_NODES + 1), 1):
        _require(count <= MAX_NODES)
        _require(not path.is_symlink() and not path.is_junction())
        if reconstruct and path.relative_to(root).as_posix() in (
            GENERATED_MEMBERS | EXTENDED_MEMBERS
        ):
            continue
        if path.is_file() and path != root / "MANIFEST.json":
            paths.append(path)
            _require(len(paths) <= MAX_MEMBERS)
    names = [path.relative_to(root).as_posix() for path in paths]
    candidate_inventory._unique(names)
    _require(bool(names))
    inventory, tables, total, snapshots = [], [], 0, {}
    for path in sorted(paths):
        name = path.relative_to(root).as_posix()
        payload = read_regular_snapshot(path, max_bytes=MAX_PAYLOAD_BYTES)
        total += len(payload)
        _require(total <= MAX_TOTAL_BYTES)
        pin = hashlib.sha256(payload).hexdigest()
        entry = {
            "path": name,
            "bytes": len(payload),
            "sha256": pin,
            "media_type": "application/octet-stream",
        }
        if name.endswith(".parquet"):
            with pq.ParquetFile(
                BytesIO(payload),
                thrift_string_size_limit=MAX_PAYLOAD_BYTES,
                thrift_container_size_limit=100_000,
            ) as parquet:
                schema = parquet.schema_arrow
                _require(0 < len(schema) <= MAX_FIELDS)
                _require(len(set(schema.names)) == len(schema.names))
                schema_bytes = schema.serialize().to_pybytes()
                tables.append(
                    {
                        "path": name,
                        "rows": parquet.metadata.num_rows,
                        "schema_sha256": hashlib.sha256(schema_bytes).hexdigest(),
                        "schema_ipc_hex": schema_bytes.hex(),
                        "fields": [
                            {
                                "name": field.name,
                                "type": str(field.type),
                                "nullable": field.nullable,
                            }
                            for field in schema
                        ],
                    }
                )
            entry["media_type"] = "application/vnd.apache.parquet"
        inventory.append(entry)
        if name == "metadata/rights.json":
            snapshots[name] = payload
    _require(bool(tables))
    originals = {
        item["path"]: item["sha256"]
        for item in inventory
        if item["path"].startswith("original/")
    }
    if originals:
        _require("metadata/rights.json" in snapshots)
        assertions = json.loads(snapshots["metadata/rights.json"])["resources"]
        _require(isinstance(assertions, list) and len(assertions) == len(originals))
        _require(all(isinstance(row, dict) for row in assertions))
        _require({row["path"] for row in assertions} == set(originals))
        _require(
            all(originals[row["path"]] == row["source_sha256"] for row in assertions)
        )
    payload_manifest = _json({"schema_version": VERSION, "inventory": inventory})
    inventory_pin = hashlib.sha256(payload_manifest).hexdigest()
    identifier = (
        "urn:archive-govt-nz:health:candidate-payload-inventory:" + inventory_pin
    )
    for table in tables:
        table["id"] = identifier + ":" + table["path"]
    package = {
        "id": identifier,
        "profile": "local_candidate_inventory",
        "manifest_sha256": inventory_pin,
        "inventory": inventory,
        "tables": tables,
    }
    croissant, crate, report = project_inventory_candidates(
        {"packages": [package]},
        name="Local Health candidate inventory",
        description=(
            "Observed local payloads and exact Arrow schemas. "
            "Rights and release eligibility are unassessed."
        ),
    )
    dcat, prov = project_inventory_graphs([package], inventory_pin)
    report.update(
        {
            "candidate_profile": VERSION,
            "inventory_scope": "payloads_before_generated_metadata_excluding_manifest",
            "payload_staging": "outside_projection_scope",
            "original_rights_assertions_bound_to_bytes": len(originals),
            "derivative_rights": "not_evaluated",
        }
    )
    return {
        "metadata/payload-inventory.json": payload_manifest,
        "metadata/schemas.json": _json({"schema_version": VERSION, "tables": tables}),
        "metadata/croissant.json": _json(croissant),
        "ro-crate-metadata.json": _json(crate),
        "metadata/dcat.json": _json(dcat),
        "metadata/prov.json": _json(prov),
        "metadata/profile-validation.json": _json(report),
    }


def verify_candidate_inventory(
    root: Path, *, expected_manifest_sha256: str
) -> dict[str, object]:
    """Reconstruct current inventory metadata; never qualify release or rights.

    The generated metadata members are excluded from their own input inventory,
    exactly as during the original build. Every other member is hash-bound by
    the caller-pinned candidate manifest. Historical bytes are never rewritten.
    """
    _require(not any(p.is_symlink() or p.is_junction() for p in (root, *root.parents)))
    _require(
        not (root / "MANIFEST.json").is_symlink()
        and not (root / "MANIFEST.json").is_junction()
    )
    original = verified_snapshot(
        root / "MANIFEST.json", expected_manifest_sha256, max_bytes=MAX_PAYLOAD_BYTES
    )
    manifest = candidate_inventory._json(original)
    _require(manifest.get("schema_version") == "archive-govt-nz.health-hf-candidate/v1")
    _require(manifest.get("dataset") == "edithatogo/nz-health-appropriations")
    records = manifest.get("files")
    _require(
        type(records) is list
        and 0 < len(records) <= MAX_MEMBERS + len(GENERATED_MEMBERS)
    )
    records = cast("list[Any]", records)
    _require(
        all(
            type(row) is dict and set(row) == {"path", "bytes", "sha256"}
            for row in records
        )
    )
    records = cast("list[dict[str, Any]]", records)
    names = [row["path"] for row in records]
    candidate_inventory._unique([*names, "MANIFEST.json"])
    _require("MANIFEST.json" not in names and set(names) >= GENERATED_MEMBERS)
    total = 0
    for row in records:
        _require(type(row["bytes"]) is int and 0 <= row["bytes"] <= MAX_PAYLOAD_BYTES)
        payload = verified_snapshot(
            root / row["path"], row["sha256"], max_bytes=MAX_PAYLOAD_BYTES
        )
        _require(len(payload) == row["bytes"])
        total += len(payload)
        _require(total <= MAX_PACKAGE_BYTES)
    actual = list(islice(root.rglob("*"), MAX_NODES + 1))
    _require(len(actual) <= MAX_NODES)
    _require(all(not p.is_symlink() and not p.is_junction() for p in actual))
    _require(
        {p.relative_to(root).as_posix() for p in actual if p.is_file()}
        == set(names) | {"MANIFEST.json"}
    )
    expected = project_candidate_inventory(root, reconstruct=True)
    for name, payload in expected.items():
        _require(
            read_regular_snapshot(root / name, max_bytes=MAX_PAYLOAD_BYTES) == payload
        )
    _require(
        verified_snapshot(
            root / "MANIFEST.json",
            expected_manifest_sha256,
            max_bytes=MAX_PAYLOAD_BYTES,
        )
        == original
    )
    report = json.loads(expected["metadata/profile-validation.json"])
    return {
        "schema_version": "archive-govt-nz.health-candidate-metadata-verification/v1",
        "status": "verified_inventory_metadata",
        "manifest_sha256": expected_manifest_sha256,
        "metadata_files_verified": len(expected),
        "payload_members_verified": len(records),
        "recordsets": report["recordsets"],
        "fields": report["fields"],
        "release_readiness": report["release_readiness"],
        "derivative_rights": report["derivative_rights"],
        "publication_approval": "not_granted",
        "full_conformance": report["full_conformance"],
    }
