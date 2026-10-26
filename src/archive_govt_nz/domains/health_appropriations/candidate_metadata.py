# SPDX-License-Identifier: Apache-2.0
"""Observed candidate schemas and inventory projections without release claims."""

# ruff: noqa: SLF001 -- reuse the existing candidate portable-path boundary.

from __future__ import annotations

import hashlib
import json
from io import BytesIO
from typing import TYPE_CHECKING

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
)

if TYPE_CHECKING:
    from pathlib import Path

VERSION = "archive-govt-nz.health-candidate-inventory-metadata/v1"
MAX_MEMBERS = 128
MAX_PAYLOAD_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_FIELDS = 256
_ERROR = "candidate_metadata_contract"


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2)
        + "\n"
    ).encode()


def project_candidate_inventory(root: Path) -> dict[str, bytes]:
    """Observe bounded local payloads and describe their actual Arrow schemas.

    No files are written. The supplied root is operator-selected, not a sandbox
    against concurrent hostile changes. The caller must recheck payload hashes
    before saving a final candidate manifest. No rights, source authority,
    publication date, activities or standards conformance are inferred.
    """
    _require(root.is_dir() and not root.is_symlink() and not root.is_junction())
    paths = []
    for path in root.rglob("*"):
        _require(not path.is_symlink() and not path.is_junction())
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
