"""CLI tool to recover broken URLs via Internet Archive / Wayback triangulation."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.wayback_triangulation import run_wayback_triangulation


def main() -> int:
    """Read broken URLs ledger and recover historical snapshots into CAS objects."""
    parser = argparse.ArgumentParser(
        description="Recover 404/broken CKAN resources using Wayback Machine CDX API."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("evidence/global-broken-urls.json"),
        help="Input broken URLs ledger",
    )
    parser.add_argument(
        "--objects-dir",
        type=Path,
        default=Path("objects"),
        help="Object store root directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/wayback-recovery-receipt.json"),
        help="Output recovery receipt JSON",
    )
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Broken URLs file not found: {args.input}")
        return 1

    data = json.loads(args.input.read_text(encoding="utf-8"))
    broken_urls = data.get("broken_urls", [])

    store = ContentAddressedStore(args.objects_dir)
    receipt = asyncio.run(
        run_wayback_triangulation(
            broken_urls,
            store,
            concurrency=args.concurrency,
        )
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    rec = receipt.get("recovered_count", 0)
    tot = receipt.get("total_broken_evaluated", 0)
    print(f"Wayback triangulation finished: {rec} recovered out of {tot} broken URLs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
