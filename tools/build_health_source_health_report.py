"""Build the pinned whole-census health source-health/vintage-state report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.source_health_report import (
    CaptureEvidence,
    LayoutEvidence,
    build_report,
    render_markdown,
)

TRACK = Path("conductor/tracks/health_appropriations_medallion_assimilation_20260829")


def main() -> int:
    """Read the two pinned censuses and write deterministic report products."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-census", type=Path, default=TRACK / "source-census.json"
    )
    parser.add_argument(
        "--context-census", type=Path, default=TRACK / "context-census.json"
    )
    parser.add_argument("--capture-manifest", type=Path)
    parser.add_argument("--bronze-cas-root", type=Path)
    parser.add_argument("--pdf-layout-baseline", type=Path)
    parser.add_argument(
        "--recorded-report",
        type=Path,
        help=(
            "Prior report used to retain pinned evidence when its source is "
            "unavailable."
        ),
    )
    parser.add_argument(
        "--json-output", type=Path, default=TRACK / "source-health-report.json"
    )
    parser.add_argument(
        "--markdown-output", type=Path, default=TRACK / "source-health-report.md"
    )
    args = parser.parse_args()
    source_bytes = args.source_census.read_bytes()
    context_bytes = args.context_census.read_bytes()
    capture_evidence = None
    if args.capture_manifest is not None:
        if args.bronze_cas_root is None:
            parser.error("--bronze-cas-root is required with --capture-manifest")
        capture_bytes = args.capture_manifest.read_bytes()
        capture_evidence = CaptureEvidence(
            manifest=json.loads(capture_bytes),
            manifest_bytes=capture_bytes,
            manifest_name=args.capture_manifest.name,
            cas_root=args.bronze_cas_root,
        )
    layout_bytes = (
        args.pdf_layout_baseline.read_bytes()
        if args.pdf_layout_baseline is not None
        else None
    )
    recorded_path = args.recorded_report or args.json_output
    if args.recorded_report is None and not recorded_path.exists():
        recorded_path = TRACK / "source-health-report.json"
    report = build_report(
        json.loads(source_bytes),
        source_bytes,
        json.loads(context_bytes),
        context_bytes,
        capture_evidence,
        layout_evidence=LayoutEvidence(json.loads(layout_bytes), layout_bytes)
        if layout_bytes is not None
        else None,
        recorded_report=json.loads(recorded_path.read_bytes()),
    )
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    args.markdown_output.write_text(render_markdown(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "passed",
                "resources": report["summary"]["resource_count"],
                "context_series_vintages": report["summary"][
                    "context_series_vintage_count"
                ],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
