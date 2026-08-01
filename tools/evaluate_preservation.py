"""Emit a bounded preservation-packaging evaluation receipt."""

from __future__ import annotations

import json
from pathlib import Path

from archive_govt_nz.preservation import validate_fixture

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence" / "preservation-packaging-evaluation.json"


def main() -> int:
    """Write machine-readable evidence for the three candidate standards."""
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
            ROOT / "conductor" / "tracks" / "preservation_conformance_20260801" / "fixtures"
        ),
        "conformance_claim": "bounded-structural-evaluation-only",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(evaluation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
