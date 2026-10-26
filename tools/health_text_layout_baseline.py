# SPDX-License-Identifier: Apache-2.0
"""Record reviewed CSV/HTML layouts and common dispatch drift from retained Bronze."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.text_layout_baseline import (
    build_text_layout_baseline_report,
    compare_text_layout_reports,
)


def main() -> int:
    """Inspect the exact captured text cohort without acquisition or mutation."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-census", type=Path, required=True)
    parser.add_argument("--capture-manifest", type=Path, required=True)
    parser.add_argument("--cas-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--drift-output", type=Path)
    args = parser.parse_args()
    if (args.baseline is None) != (args.drift_output is None):
        parser.error("--baseline and --drift-output must be supplied together")
    targets = [args.output] + ([] if args.drift_output is None else [args.drift_output])
    if len({path.resolve() for path in targets}) != len(targets) or any(
        path.exists() for path in targets
    ):
        parser.error("output paths must be distinct and must not already exist")
    report = build_text_layout_baseline_report(
        args.source_census.read_bytes(),
        args.capture_manifest.read_bytes(),
        args.cas_root,
    )
    drift = (
        None
        if args.baseline is None
        else compare_text_layout_reports(json.loads(args.baseline.read_bytes()), report)
    )
    with args.output.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(report, sort_keys=True, indent=2) + "\n")
    print(json.dumps(report["summary"], sort_keys=True))
    if drift is not None and args.drift_output is not None:
        with args.drift_output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(drift, sort_keys=True, indent=2) + "\n")
        return 0 if drift["status"] == "matching" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
