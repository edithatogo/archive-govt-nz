"""Build an evidence-bounded layout inventory from retained Bronze/Silver records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.domains.health_appropriations.source_layout_baseline import (
    build_source_layout_baseline_report,
)


def main() -> int:
    """Validate capture fixity, inventory available layouts and write JSON."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-census", type=Path, required=True)
    parser.add_argument("--capture-manifest", type=Path, required=True)
    parser.add_argument("--silver-root", type=Path, required=True)
    parser.add_argument("--cas-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = build_source_layout_baseline_report(
        args.source_census.read_bytes(),
        args.capture_manifest.read_bytes(),
        args.silver_root,
        args.cas_root,
    )
    payload = json.dumps(report, sort_keys=True, indent=2) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    print(json.dumps(report["summary"], sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
