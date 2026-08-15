"""Bounded validators for preservation packaging evaluation fixtures.

These validators deliberately assess structural closure only.  A passing result
is not a claim of full standard conformance or production readiness.
"""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import hashlib
import json
from pathlib import Path  # noqa: TC003
from typing import Any, cast


def _sha256(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix in {".json", ".txt"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


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
    head = document.get("head")
    result["versions_present"] = isinstance(versions, dict) and bool(
        cast("dict[str, object]", versions)
    )
    result["head_linked"] = bool(
        isinstance(head, str)
        and isinstance(versions, dict)
        and head in cast("dict[str, object]", versions)
    )
    content = (
        root / str(head) / "content" if isinstance(head, str) else root / "missing"
    )
    result["content_present"] = content.is_dir() and any(content.iterdir())
    result["valid"] = bool(
        result["versions_present"]
        and result["head_linked"]
        and result["content_present"]
        and document.get("id")
    )
    return result


def build_ro_crate_metadata(
    scope: dict[str, Any],
    capture_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a standard RO-Crate JSON-LD provenance and dataset graph."""
    captures_by_res = {}
    if capture_receipt:
        for cap in capture_receipt.get("successful_captures", []):
            if isinstance(cap, dict) and "resource_id" in cap:
                captures_by_res[str(cap["resource_id"])] = cap

    graph: list[dict[str, Any]] = [
        {
            "@id": "ro-crate-metadata.jsonld",
            "@type": "CreativeWork",
            "conformsTo": {"@id": "https://w3id.org/ro/crate/1.1"},
            "about": {"@id": "./"},
        },
        {
            "@id": "./",
            "@type": "CreativeWork",
            "name": "Archive Govt NZ - Global Catalogue Snapshot",
            "description": "Preservation archive of New Zealand government open data.",
            "license": "https://creativecommons.org/licenses/by/4.0/",
            "hasPart": [],
        },
    ]

    root_parts: list[dict[str, str]] = []
    datasets = scope.get("datasets", [])
    for ds in datasets:
        if not isinstance(ds, dict):
            continue
        ds_id = str(ds.get("id") or "")
        node_id = f"#dataset-{ds_id}"
        root_parts.append({"@id": node_id})

        distributions: list[dict[str, Any]] = []
        for res in ds.get("resources", []):
            if not isinstance(res, dict):
                continue
            r_id = str(res.get("id"))
            dist: dict[str, Any] = {
                "@type": "DataDownload",
                "identifier": r_id,
                "name": res.get("name"),
                "contentUrl": res.get("url"),
                "encodingFormat": res.get("format"),
            }
            if r_id in captures_by_res:
                dist["sha256"] = captures_by_res[r_id].get("sha256")
                dist["contentSize"] = captures_by_res[r_id].get("byte_count")
            distributions.append(dist)

        graph.append(
            {
                "@id": node_id,
                "@type": "Dataset",
                "identifier": ds_id,
                "name": ds.get("title") or ds.get("name"),
                "publisher": {
                    "@type": "Organization",
                    "name": ds.get("organization_title"),
                },
                "license": ds.get("license_title"),
                "distribution": distributions,
            }
        )

    graph[1]["hasPart"] = root_parts
    return {
        "@context": "https://w3id.org/ro/crate/1.1/context",
        "@graph": graph,
    }


def build_bagit_package(
    bag_dir: Path,
    payload_files: list[Path],
) -> None:
    """Build a deterministic BagIt 1.0 package structure with SHA-256 manifest."""
    bag_dir.mkdir(parents=True, exist_ok=True)
    data_dir = bag_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    (bag_dir / "bagit.txt").write_text(
        "BagIt-Version: 1.0\nTag-File-Character-Encoding: UTF-8\n",
        encoding="utf-8",
    )

    manifest_lines: list[str] = []
    for file_path in payload_files:
        if not file_path.is_file():
            continue
        if file_path.is_relative_to(bag_dir):
            rel_path = file_path.relative_to(bag_dir)
            digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        else:
            dest = data_dir / file_path.name
            dest.write_bytes(file_path.read_bytes())
            rel_path = dest.relative_to(bag_dir)
            digest = hashlib.sha256(dest.read_bytes()).hexdigest()
        manifest_lines.append(f"{digest}  {rel_path.as_posix()}")

    manifest_lines.sort()
    (bag_dir / "manifest-sha256.txt").write_text(
        "\n".join(manifest_lines) + "\n" if manifest_lines else "",
        encoding="utf-8",
    )
