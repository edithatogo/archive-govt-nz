"""Create fail-closed tombstone and re-probe receipts from a source probe."""

# pyright: reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import json
from datetime import timedelta
from pathlib import Path

from archive_govt_nz.source_policy import schedule_tombstone_reprobe, utc_now


def main() -> int:
    """Write a tombstone re-probe receipt."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--interval-days", type=int, default=7)
    args = parser.parse_args()
    probe = json.loads(args.probe.read_text(encoding="utf-8"))
    receipt = schedule_tombstone_reprobe(
        probe, now=utc_now(), interval=timedelta(days=args.interval_days)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    tombstones = receipt["tombstones"]
    count = len(tombstones) if isinstance(tombstones, list) else 0
    print(json.dumps({"status": "completed", "tombstones": count}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
