"""CLI tool to compute and emit catalogue drift reports between discovery manifests."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import json
from pathlib import Path

from archive_govt_nz.drift_engine import detect_catalogue_drift, serialize_drift_report


def main() -> int:
    """Read two discovery manifests and emit a structured drift report."""
    parser = argparse.ArgumentParser(
        description="Compute drift and deltas between CKAN discovery manifests."
    )
    parser.add_argument(
        "--previous",
        type=Path,
        required=True,
        help="Path to previous scope manifest JSON",
    )
    parser.add_argument(
        "--current",
        type=Path,
        required=True,
        help="Path to current scope manifest JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/catalogue-drift-report.json"),
        help="Output drift report JSON path",
    )
    args = parser.parse_args()

    if not args.previous.is_file():
        print(f"Previous manifest not found: {args.previous}")
        return 1
    if not args.current.is_file():
        print(f"Current manifest not found: {args.current}")
        return 1

    prev_data = json.loads(args.previous.read_text(encoding="utf-8"))
    curr_data = json.loads(args.current.read_text(encoding="utf-8"))

    report = detect_catalogue_drift(prev_data, curr_data)
    receipt = serialize_drift_report(report)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    status = "STABLE" if report.is_stable else "DRIFT_DETECTED"
    print(f"Catalogue drift analysis ({status}):")
    print(f"  Added datasets    : {len(report.added_dataset_ids)}")
    print(f"  Removed datasets  : {len(report.removed_dataset_ids)}")
    print(f"  Modified datasets : {len(report.modified_dataset_ids)}")
    print(f"  Report written to : {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
