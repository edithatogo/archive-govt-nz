"""Generate RO-Crate and BagIt preservation packages for catalogue archives."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def build_ro_crate_metadata(
    scope: dict[str, Any],
    capture_receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate a standard RO-Crate JSON-LD provenance and dataset graph."""
    now = datetime.now(UTC).isoformat()
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
            "datePublished": now,
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
    (bag_dir / "bagit.txt").write_text(
        "BagIt-Version: 1.0\nTag-File-Character-Encoding: UTF-8\n",
        encoding="utf-8",
    )

    manifest_lines: list[str] = []
    for file_path in payload_files:
        if not file_path.is_file():
            continue
        rel_path = file_path.relative_to(bag_dir)
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        manifest_lines.append(f"{digest}  {rel_path.as_posix()}")

    manifest_lines.sort()
    (bag_dir / "manifest-sha256.txt").write_text(
        "\n".join(manifest_lines) + "\n" if manifest_lines else "",
        encoding="utf-8",
    )


def main() -> int:
    """Generate RO-Crate and BagIt preservation manifests from capture evidence."""
    parser = argparse.ArgumentParser(
        description="Generate RO-Crate and BagIt packages."
    )
    parser.add_argument(
        "--scope",
        type=Path,
        default=Path("evidence/global-ckan-scope.json"),
        help="Global scope manifest",
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("evidence/global-capture-receipt.json"),
        help="Capture receipt",
    )
    parser.add_argument(
        "--ro-crate-output",
        type=Path,
        default=Path("evidence/ro-crate-metadata.jsonld"),
        help="Output RO-Crate JSON-LD",
    )
    args = parser.parse_args()

    scope = (
        json.loads(args.scope.read_text(encoding="utf-8"))
        if args.scope.is_file()
        else {}
    )
    receipt = (
        json.loads(args.receipt.read_text(encoding="utf-8"))
        if args.receipt.is_file()
        else {}
    )

    ro_crate = build_ro_crate_metadata(scope, receipt)
    args.ro_crate_output.parent.mkdir(parents=True, exist_ok=True)
    args.ro_crate_output.write_text(
        json.dumps(ro_crate, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Generated RO-Crate metadata: {args.ro_crate_output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
