"""Emit a bounded preservation-packaging evaluation receipt."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "evidence" / "preservation-packaging-evaluation.json"


def main() -> int:
    """Write machine-readable evidence for the three candidate standards."""
    evaluation = {
        "schema_version": "archive-govt-nz.preservation-evaluation/v1",
        "scope": "bounded Treasury vertical-slice fixtures",
        "decision": "evaluate-before-adopt",
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
                "status": "candidate",
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
                "status": "candidate",
                "benefits": [
                    "rich research provenance graph",
                    "human and machine-readable metadata",
                ],
                "gaps": ["does not replace content store or resumable ledger"],
            },
            {
                "name": "BagIt",
                "status": "candidate",
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
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(evaluation, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
