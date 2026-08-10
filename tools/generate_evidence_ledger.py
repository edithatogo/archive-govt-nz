"""Generate paired stage-based evidence ledger artefacts."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "evidence" / "archive-evidence-ledger.json"
MD_PATH = ROOT / "evidence" / "archive-evidence-ledger.md"


def _load_optional(path: Path) -> dict[str, Any]:
    """Load an optional evidence document without widening disclosure."""
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return cast("dict[str, Any]", value) if isinstance(value, dict) else {}


def main() -> int:
    """Write a bounded ledger describing current evidence, not intent."""
    now = datetime.now(UTC).isoformat()
    capture_path = ROOT / "evidence" / "phase-6-capture-summary.json"
    release_path = (
        ROOT
        / "conductor/tracks/treasury_archive_mvp_20260731/evidence"
        / "phase-9-release-reconciliation.json"
    )
    capture = _load_optional(capture_path)
    release = _load_optional(release_path)
    capture_ref = capture_path.relative_to(ROOT).as_posix()
    release_ref = release_path.relative_to(ROOT).as_posix()
    captured = int(capture.get("captured", 0) or 0)
    release_reconciled = release.get("state") == "reconciled"
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
        {
            "stage": "captured",
            "state": "partially-captured" if captured else "not-yet-complete",
            "evidence": [capture_ref] if captured else [],
        },
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
        {
            "stage": "uploaded",
            "state": (
                "uploaded-remotely-verified" if release_reconciled else "not-authorized"
            ),
            "evidence": ([release_ref] if release_reconciled else []),
        },
        {
            "stage": "remotely-verified",
            "state": "remote-readback-verified" if release_reconciled else "not-run",
            "evidence": ([release_ref] if release_reconciled else []),
        },
        {
            "stage": "released",
            "state": "reconciled-release" if release_reconciled else "not-released",
            "evidence": ([release_ref] if release_reconciled else []),
        },
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
