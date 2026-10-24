# SPDX-License-Identifier: Apache-2.0
"""Rebuild and reconcile pinned Health source-layout baseline reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.pdf_layout_baseline import (
    build_pdf_layout_baseline_report,
)
from archive_govt_nz.domains.health_appropriations.source_layout_baseline import (
    build_source_layout_baseline_report,
)
from archive_govt_nz.domains.health_appropriations.source_layout_reconciliation import (
    reconcile_source_layout_reports,
)


def main() -> int:
    """Verify source fixity, rebuild both baselines and write the reconciliation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-census", type=Path, required=True)
    parser.add_argument("--capture-manifest", type=Path, required=True)
    parser.add_argument("--silver-root", type=Path, required=True)
    parser.add_argument("--cas-root", type=Path, required=True)
    parser.add_argument("--workbook-baseline", type=Path, required=True)
    parser.add_argument("--pdf-baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    census_bytes = args.source_census.read_bytes()
    capture_bytes = args.capture_manifest.read_bytes()
    workbook_bytes = args.workbook_baseline.read_bytes()
    pdf_bytes = args.pdf_baseline.read_bytes()
    workbook_recheck = build_source_layout_baseline_report(
        census_bytes, capture_bytes, args.silver_root, args.cas_root
    )
    pdf_recheck = build_pdf_layout_baseline_report(
        census_bytes, capture_bytes, args.cas_root
    )
    report = reconcile_source_layout_reports(
        census_bytes,
        workbook_bytes,
        pdf_bytes,
        (json.dumps(workbook_recheck, sort_keys=True, indent=2) + "\n").encode(),
        (json.dumps(pdf_recheck, sort_keys=True, indent=2) + "\n").encode(),
    )
    payload = json.dumps(report, sort_keys=True, indent=2) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
