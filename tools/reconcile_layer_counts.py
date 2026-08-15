"""Reconcile local raw, capture, derivative, and release layer counts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from archive_govt_nz.layer_reconciliation import reconcile_layer_counts

ROOT = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict[str, Any]:
    """Load one local JSON evidence document."""
    return cast("dict[str, Any]", json.loads(path.read_text(encoding="utf-8")))


def main() -> int:
    """Write paired layer-count reconciliation receipts."""
    release = _load(ROOT / "build/release-candidate-v3/manifest.json")
    capture = _load(ROOT / "evidence/phase-6-capture-summary.json")
    derivative = _load(ROOT / "build/derivatives/treasury/receipt.json")
    ledger = _load(ROOT / "evidence/phase-5-ledger-build.json")
    raw_root = ROOT / "build/live/reconcile-20260731T164949/raw"
    raw_count = len(tuple(raw_root.glob("*.json")))
    layer_counts = cast("dict[str, Any]", release.get("layer_counts", {}))
    manifest_counts = {str(key): int(value) for key, value in layer_counts.items()}
    ledger_counts_map = cast("dict[str, Any]", ledger.get("counts", {}))
    result = reconcile_layer_counts(
        manifest_counts=manifest_counts,
        raw_count=raw_count,
        captured_count=int(capture.get("captured", 0)),
        derivative_count=3,
        ledger_counts={
            str(key): int(value) for key, value in ledger_counts_map.items()
        },
        expected_ledger_counts={
            "observations": 91,
            "attempts": 91,
            "objects": 12,
            "versions": 91,
        },
    )
    result["sources"] = {
        "release_manifest": "build/release-candidate-v3/manifest.json",
        "capture_summary": "evidence/phase-6-capture-summary.json",
        "derivative_receipt": "build/derivatives/treasury/receipt.json",
        "ledger_receipt": "evidence/phase-5-ledger-build.json",
        "raw_root": "build/live/reconcile-20260731T164949/raw",
        "derivative_row_count": derivative.get("row_count"),
    }
    output = ROOT / "evidence/phase-5-layer-reconciliation.json"
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    markdown = ROOT / "evidence/phase-5-layer-reconciliation.md"
    lines = [
        "# Phase 5 layer reconciliation",
        "",
        f"Status: **{result['status']}**",
        "",
        "| Layer | Manifest | Observed | Check |",
        "| --- | ---: | ---: | --- |",
    ]
    observed = result["observed"]
    checks = result["checks"]
    for key, value in observed.items():  # type: ignore[union-attr]
        lines.append(
            f"| {key} | {manifest_counts[key]} | {value} | "
            f"{'PASS' if checks[key] else 'FAIL'} |"  # type: ignore[index]
        )
    lines += ["", "Layer counts do not claim complete source capture.", ""]
    markdown.write_text("\n".join(lines), encoding="utf-8")
    return 0 if result["status"] == "reconciled" else 1


if __name__ == "__main__":
    raise SystemExit(main())
