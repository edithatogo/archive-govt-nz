"""Bounded validators for preservation packaging evaluation fixtures.

These validators deliberately assess structural closure only.  A passing result
is not a claim of full standard conformance or production readiness.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path  # noqa: TC003
from typing import Any, cast


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_fixture(root: Path) -> dict[str, Any]:
    """Validate fixture manifest hashes without asserting a standard profile."""
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    checks: list[dict[str, Any]] = []
    for item in manifest.get("files", []):
        path = root / str(item["path"])
        exists = path.is_file()
        checks.append(
            {
                "path": item["path"],
                "exists": exists,
                "sha256": _sha256(path) if exists else None,
                "expected_sha256": item.get("sha256"),
                "valid": exists and _sha256(path) == item.get("sha256"),
            }
        )
    return {
        "fixture_id": manifest.get("fixture_id"),
        "checks": checks,
        "valid": all(item["valid"] for item in checks),
        "synthetic": True,
    }


def validate_ro_crate(root: Path) -> dict[str, Any]:
    """Perform bounded RO-Crate JSON-LD envelope checks."""
    metadata = root / "ro-crate-metadata.jsonld"
    result: dict[str, Any] = {
        "standard": "RO-Crate",
        "profile": "bounded",
        "metadata_present": metadata.is_file(),
        "valid": False,
    }
    if not metadata.is_file():
        return result
    document = json.loads(metadata.read_text(encoding="utf-8"))
    graph = document.get("@graph")
    result["jsonld_graph"] = isinstance(graph, list)
    graph_items = cast("list[object]", graph) if isinstance(graph, list) else []
    result["root_declared"] = any(
        isinstance(item, dict)
        and cast("dict[str, object]", item).get("@type") == "CreativeWork"
        for item in graph_items
    )
    result["valid"] = bool(result["jsonld_graph"] and result["root_declared"])
    return result


def validate_bagit(root: Path) -> dict[str, Any]:
    """Perform bounded BagIt manifest and payload closure checks."""
    payload = root / "data"
    manifest = root / "manifest-sha256.txt"
    result: dict[str, Any] = {
        "standard": "BagIt",
        "profile": "bounded",
        "bagit_txt": (root / "bagit.txt").is_file(),
        "manifest_present": manifest.is_file(),
        "valid": False,
    }
    if not manifest.is_file() or not payload.is_dir():
        return result
    checks: list[bool] = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        digest, _, relative = line.partition("  ")
        path = root / relative
        checks.append(path.is_file() and _sha256(path) == digest)
    result["entries"] = len(checks)
    result["valid"] = bool(result["bagit_txt"] and checks and all(checks))
    return result


def validate_ocfl(root: Path) -> dict[str, Any]:
    """Perform bounded OCFL inventory/version-link checks (not full conformance)."""
    inventory = root / "inventory.json"
    result: dict[str, Any] = {
        "standard": "OCFL",
        "profile": "bounded",
        "inventory_present": inventory.is_file(),
        "valid": False,
        "conformance_claim": "none",
    }
    if not inventory.is_file():
        return result
    document = cast("dict[str, Any]", json.loads(inventory.read_text(encoding="utf-8")))
    versions = document.get("versions")
    result["versions_present"] = isinstance(versions, dict) and bool(
        cast("dict[str, object]", versions)
    )
    result["valid"] = bool(result["versions_present"] and document.get("id"))
    return result
