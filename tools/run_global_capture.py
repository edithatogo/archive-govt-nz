"""Domain-throttled batch capture into content-addressed object store."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from archive_govt_nz.global_capture import (
    GlobalBatchCaptureConfig,
    run_global_batch_capture,
)
from archive_govt_nz.object_store import ContentAddressedStore


def main() -> int:
    """Read rights classification and ingest eligible payloads into CAS objects."""
    parser = argparse.ArgumentParser(
        description="Stream eligible CKAN resources into immutable CAS object store."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("evidence/global-rights-classification.json"),
        help="Input rights classification JSON",
    )
    parser.add_argument(
        "--objects-dir",
        type=Path,
        default=Path("objects"),
        help="Root directory for content-addressed store",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("evidence/global-capture-receipt.json"),
        help="Output capture receipt JSON",
    )
    parser.add_argument(
        "--broken-urls-output",
        type=Path,
        default=Path("evidence/global-broken-urls.json"),
        help="Output broken URLs ledger JSON",
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--concurrency-per-host", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    candidates = data.get("records", [])

    store = ContentAddressedStore(args.objects_dir)
    config = GlobalBatchCaptureConfig(
        max_workers=args.workers,
        max_concurrency_per_host=args.concurrency_per_host,
        timeout_seconds=args.timeout,
    )

    receipt = asyncio.run(run_global_batch_capture(candidates, store, config))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    if args.broken_urls_output:
        broken_ledger = {
            "schema_version": "archive-govt-nz.broken-urls-ledger/v1",
            "generated_at": receipt.get("generated_at"),
            "total_broken_urls": receipt.get("broken_url_count", 0),
            "broken_urls": receipt.get("broken_urls", []),
        }
        args.broken_urls_output.parent.mkdir(parents=True, exist_ok=True)
        args.broken_urls_output.write_text(
            json.dumps(broken_ledger, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )

    succ = receipt.get("successful_count")
    broken = receipt.get("broken_url_count")
    print(f"Batch capture complete: {succ} succeeded, {broken} broken URLs recorded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
