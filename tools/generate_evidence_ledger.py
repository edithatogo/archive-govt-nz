"""Generate paired stage-based evidence ledger artefacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "evidence" / "archive-evidence-ledger.json"
MD_PATH = ROOT / "evidence" / "archive-evidence-ledger.md"


def main() -> int:
    """Write a bounded ledger describing current evidence, not intent."""
    now = datetime.now(UTC).isoformat()
    stages: list[dict[str, Any]] = [
        {
            "stage": "discovered",
            "state": "observed",
            "evidence": ["evidence/phase-2-live-observation.json"],
        },
        {
            "stage": "eligible",
            "state": "policy-implemented",
            "evidence": ["src/archive_govt_nz/resource_policy.py"],
        },
        {"stage": "captured", "state": "not-yet-complete", "evidence": []},
        {
            "stage": "validated",
            "state": "software-gates-passed",
            "evidence": ["build/pip-audit.json", "build/sbom.cdx.json"],
        },
        {
            "stage": "transformed",
            "state": "derivative-foundation",
            "evidence": ["src/archive_govt_nz/derivatives.py"],
        },
        {"stage": "uploaded", "state": "not-authorized", "evidence": []},
        {"stage": "remotely-verified", "state": "not-run", "evidence": []},
        {"stage": "released", "state": "not-released", "evidence": []},
        {"stage": "unavailable", "state": "recorded-per-attempt", "evidence": []},
        {
            "stage": "restricted",
            "state": "policy-controlled",
            "evidence": ["src/archive_govt_nz/resource_policy.py"],
        },
    ]
    document = {
        "schema_version": "archive-govt-nz.evidence-ledger/v1",
        "generated_at": now,
        "stages": stages,
    }
    JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(
        json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Archive evidence ledger",
        "",
        f"Generated: `{now}`",
        "",
        "| Stage | State | Evidence |",
        "| --- | --- | --- |",
    ]
    lines.extend(
        f"| {item['stage']} | {item['state']} | {', '.join(item['evidence']) or '—'} |"
        for item in stages
    )
    MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {JSON_PATH.relative_to(ROOT)} and {MD_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
