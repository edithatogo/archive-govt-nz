"""Prepare a local Treasury release candidate from verified evidence only."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from archive_govt_nz.release_package import build_release_package


def main() -> int:
    """Build a checksum-pinned candidate without publication side effects."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    files = [
        root / "evidence/phase-2-live-observation.json",
        root / "evidence/phase-6-pre-capture-reconciliation.json",
        root / "evidence/phase-6-treasury-capture-plan.json",
        root / "evidence/archive-evidence-ledger.json",
        root / "evidence/release-attestation.json",
        root / "evidence/preservation-packaging-evaluation.json",
        root / "evidence/phase-6-capture-summary.json",
        root / "evidence/publication-metadata/README.md",
        root / "evidence/publication-metadata/zenodo.json",
        root / "evidence/publication-metadata/taxonomy.json",
        root / "evidence/publication-metadata/hf-estate-observation.json",
        root / "build/sbom.cdx.json",
    ]
    if any(not file.is_file() for file in files):
        missing = [str(file) for file in files if not file.is_file()]
        print(json.dumps({"status": "incomplete", "missing": missing}))
        return 1
    args.output_dir.mkdir(parents=True, exist_ok=True)
    package = build_release_package(
        files, args.output_dir / "treasury-release-candidate.tar", root
    )
    manifest = {
        "schema_version": "archive-govt-nz.treasury-release-candidate/v1",
        "status": "prepared-not-published",
        "publication_authorized": False,
        "package": {
            "path": str(package.path),
            "sha256": package.sha256,
            "files": package.files,
        },
        "file_checksums": [
            {
                "path": str(file.relative_to(root)),
                "sha256": hashlib.sha256(file.read_bytes()).hexdigest(),
            }
            for file in files
        ],
        "limitations": [
            "payload_capture_not_complete",
            "captured_objects_remain_in_local_content_addressed_store",
            "rights_review_incomplete",
            "no_doi",
            "no_remote_upload",
        ],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({"status": manifest["status"], "package_sha256": package.sha256}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
