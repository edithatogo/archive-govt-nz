"""Emit a bounded preservation-packaging evaluation receipt."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.preservation import (
    validate_bagit,
    validate_fixture,
    validate_ocfl,
    validate_ro_crate,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence" / "preservation-packaging-evaluation.json"


def main(argv: list[str] | None = None) -> int:
    """Write machine-readable evidence for the three candidate standards."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    output = parser.parse_args(argv).output
    evaluation = {
        "schema_version": "archive-govt-nz.preservation-evaluation/v1",
        "scope": "bounded Treasury vertical-slice fixtures",
        "decision": "bounded-profile-adoption",
        "decision_rationale": (
            "Adopt RO-Crate metadata as the provenance envelope now; emit BagIt "
            "packages only at release boundaries; defer OCFL as a storage profile "
            "until a production object corpus and conformance fixture exist."
        ),
        "criteria": [
            "content-addressed integrity",
            "manifest closure and provenance",
            "streaming/resumable operation",
            "portable analysis derivatives",
            "tooling and security maintenance",
        ],
        "standards": [
            {
                "name": "OCFL",
                "status": "deferred",
                "decision": "revisit-after-production-corpus",
                "benefits": [
                    "immutable versioned object layout",
                    "strong fixity semantics",
                ],
                "gaps": [
                    (
                        "additional profile and tooling work for operational ledger "
                        "integration"
                    )
                ],
            },
            {
                "name": "RO-Crate",
                "status": "adopted-profile",
                "decision": "use-for-provenance-metadata",
                "benefits": [
                    "rich research provenance graph",
                    "human and machine-readable metadata",
                ],
                "gaps": ["does not replace content store or resumable ledger"],
            },
            {
                "name": "BagIt",
                "status": "adopted-at-release",
                "decision": "use-for-transfer-and-zenodo-staging",
                "benefits": [
                    "widely understood transfer package",
                    "simple payload/tag manifests",
                ],
                "gaps": [
                    "snapshot-oriented; requires external change-driven version ledger"
                ],
            },
        ],
        "release_requirement": False,
        "adoption_gates": [
            "RO-Crate metadata must reference immutable object IDs and manifests",
            "BagIt payload manifests must verify before any Zenodo upload",
            "OCFL remains non-blocking until conformance fixtures are available",
        ],
        "fixture_validation": validate_fixture(
            ROOT
            / "conductor"
            / "tracks"
            / "preservation_conformance_20260801"
            / "fixtures"
        ),
        "ro_crate_validation": validate_ro_crate(
            ROOT
            / "conductor"
            / "tracks"
            / "preservation_conformance_20260801"
            / "fixtures"
        ),
        "bagit_validation": validate_bagit(
            ROOT
            / "conductor"
            / "tracks"
            / "preservation_conformance_20260801"
            / "fixtures"
            / "bagit"
        ),
        "ocfl_validation": validate_ocfl(
            ROOT
            / "conductor"
            / "tracks"
            / "preservation_conformance_20260801"
            / "fixtures"
            / "ocfl"
        ),
        "conformance_claim": "bounded-structural-evaluation-only",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(evaluation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    display = output.relative_to(ROOT) if output.is_relative_to(ROOT) else output
    print(f"wrote {display}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
