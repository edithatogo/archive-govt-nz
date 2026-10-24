"""Build a hash-verified structural inventory of captured Bronze workbooks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.bronze_workbook_layout import (
    build_bronze_workbook_layout_report,
)


def main() -> int:
    """Verify the pinned cohort, then write its structural workbook report."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-census", type=Path, required=True)
    parser.add_argument("--capture-manifest", type=Path, required=True)
    parser.add_argument("--cas-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_bronze_workbook_layout_report(
        args.source_census.read_bytes(),
        args.capture_manifest.read_bytes(),
        args.cas_root,
    )
    payload = json.dumps(report, sort_keys=True, indent=2) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
