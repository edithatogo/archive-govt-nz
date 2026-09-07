"""Bounded immutable child-manifest reconciliation, never raw restoration."""

from __future__ import annotations

import hashlib
import json
import re
import tempfile
from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

from jsonschema import Draft202012Validator, FormatChecker

from archive_govt_nz.foi_delivery import MAX_POINTER_BYTES, REVISION, TABLE_PATHS
from archive_govt_nz.foi_package import BASE_TABLES, canonical, safe_path

if TYPE_CHECKING:
    from archive_govt_nz.foi_delivery import Hub

MAX_CHILDREN = 23
MAX_MANIFEST_BYTES = 256 * 1024
CHILD_TABLES = {name: TABLE_PATHS[name] for name in (*BASE_TABLES, "attachments")}


def _fail() -> NoReturn:
    message = "child_manifest_reconciliation_failed"
    raise ValueError(message)


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value = dict(pairs)
    if len(value) != len(pairs):
        _fail()
    return value


def _read(hub: Hub, repo: str, revision: str, name: str, root: Path) -> bytes:
    limit = MAX_POINTER_BYTES if name == "current.json" else MAX_MANIFEST_BYTES
    sizes = hub.sizes(repo, revision, [name])
    size = sizes.get(name)
    if set(sizes) != {name} or type(size) is not int or not 0 < size <= limit:
        _fail()
    target = safe_path(root, "readback.json")
    hub.download(repo, revision, name, target, size)
    with target.open("rb") as stream:
        payload = stream.read(limit + 1)
    if len(payload) != size:
        _fail()
    return payload


def _document(payload: bytes, schema: str) -> dict[str, Any]:
    value = json.loads(payload, object_pairs_hook=_pairs)
    contract = json.loads(
        files("archive_govt_nz.schemas").joinpath(schema).read_bytes()
    )
    validator = Draft202012Validator(contract, format_checker=FormatChecker())
    if not validator.is_valid(value):
        _fail()
    return value


def reconcile_child_manifests(
    hub: Hub, sources: list[dict[str, Any]]
) -> dict[str, Any]:
    """Bind every named child at its catalogue-pinned pointer revision.

    Reads at most two bounded documents per child, never payloads or latest
    pointers. The Hub must honor its anonymous bounded-download contract.
    A missing/unsupported child is a hard failure, not a raw-completeness claim.
    """
    selected = [row for row in sources if row["hf_repo_id"] is not None]
    if (
        len(selected) > MAX_CHILDREN
        or len({row["id"] for row in sources}) != len(sources)
        or len({row["hf_repo_id"] for row in selected}) != len(selected)
    ):
        _fail()
    for row in selected:
        if (
            not isinstance(row.get("hf_revision"), str)
            or not REVISION.fullmatch(row["hf_revision"])
            or not re.fullmatch(r"[A-Za-z0-9._-]+/[A-Za-z0-9._-]+", row["hf_repo_id"])
        ):
            _fail()
    children = []
    try:
        with tempfile.TemporaryDirectory(prefix="foi-child-manifests-") as temporary:
            root = Path(temporary)
            for source in sorted(selected, key=lambda row: row["id"]):
                repo, revision = source["hf_repo_id"], source["hf_revision"]
                info = hub.info(repo)
                if (
                    info["id"] != repo
                    or info["private"] is not False
                    or info["gated"] is not False
                ):
                    _fail()
                pointer_bytes = _read(hub, repo, revision, "current.json", root)
                pointer = _document(pointer_bytes, "foi-current-v1.schema.json")
                if pointer["repo_id"] != repo or pointer.get("tables") != CHILD_TABLES:
                    _fail()
                digest = pointer["manifest_sha256"]
                name = f"snapshots/{digest}/manifest.json"
                payload = _read(
                    hub,
                    repo,
                    pointer["snapshot_revision"],
                    name,
                    root,
                )
                if hashlib.sha256(payload).hexdigest() != digest:
                    _fail()
                manifest = _document(payload, "foi-package-v2.schema.json")
                expected = {"raw.tar", "README.md"} | {
                    f"indexes/{table}.{extension}"
                    for table in CHILD_TABLES
                    for extension in ("jsonl", "parquet")
                }
                if (
                    manifest["source_id"] != source["id"]
                    or manifest["country"] != source["entity_id"]
                    or {row["path"] for row in manifest["files"]} != expected
                ):
                    _fail()
                children.append(
                    {
                        "source_id": source["id"],
                        "entity_id": source["entity_id"],
                        "repo_id": repo,
                        "pointer_revision": revision,
                        "pointer_sha256": hashlib.sha256(pointer_bytes).hexdigest(),
                        "snapshot_revision": pointer["snapshot_revision"],
                        "manifest_path": name,
                        "manifest_sha256": digest,
                        "manifest_bytes": len(payload),
                        "tables": pointer["tables"],
                        "manifest_schema_version": manifest["schema_version"],
                    }
                )
    except KeyError, TypeError, ValueError, RecursionError:
        _fail()
    return {
        "schema_version": "archive-govt-nz.foi-child-manifests/v1",
        "scope": "immutable_child_manifest_metadata_only",
        "children": children,
        "raw_objects_verified": False,
        "rights_approval": False,
    }


def bind_child_manifests(
    content: dict[str, bytes], receipt: dict[str, Any]
) -> dict[str, bytes]:
    """Add readback references without rewriting canonical registry/source rows."""
    result = dict(content)
    payload = canonical(receipt)
    result["child-manifests.json"] = payload
    manifest = json.loads(result["manifest.json"])
    manifest["files"].append(
        {
            "path": "child-manifests.json",
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    )
    manifest["files"].sort(key=lambda row: row["path"])
    result["manifest.json"] = canonical(manifest)
    return result
