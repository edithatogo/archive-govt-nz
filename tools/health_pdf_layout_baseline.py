"""Build a page-level layout inventory from retained official PDF sources."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.pdf_layout_baseline import (
    build_pdf_layout_baseline_report,
)


def main() -> int:
    """Verify captured PDF bytes, fingerprint page structure, and write JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-census", type=Path, required=True)
    parser.add_argument("--capture-manifest", type=Path, required=True)
    parser.add_argument("--cas-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_pdf_layout_baseline_report(
        args.source_census.read_bytes(),
        args.capture_manifest.read_bytes(),
        args.cas_root,
    )
    args.output.write_text(
        json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report["summary"], sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
