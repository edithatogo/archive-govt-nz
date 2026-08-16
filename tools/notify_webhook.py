"""CLI tool to dispatch harvest completion webhook alerts."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from archive_govt_nz.notifications import (
    HarvestNotificationPayload,
    dispatch_webhook,
)

DEFAULT_REPO_URL = "https://huggingface.co/datasets/edithatogo/archive-govt-nz-global"


def main() -> int:
    """Read summary receipt and dispatch webhook notification."""
    parser = argparse.ArgumentParser(
        description="Dispatch harvest completion webhook notification."
    )
    parser.add_argument(
        "--summary-receipt",
        type=Path,
        default=Path("evidence/global-harvest-summary.json"),
        help="Path to harvest summary receipt JSON",
    )
    parser.add_argument(
        "--webhook-url",
        default=os.environ.get("HARVEST_WEBHOOK_URL"),
        help="Target webhook URL (or HARVEST_WEBHOOK_URL env var)",
    )
    parser.add_argument(
        "--hf-repo-url",
        default=os.environ.get("HF_REPO_URL", DEFAULT_REPO_URL),
        help="Published Hugging Face repository URL",
    )
    parser.add_argument(
        "--service",
        choices=["auto", "slack", "discord", "generic"],
        default="auto",
        help="Webhook format service type",
    )
    args = parser.parse_args()

    if not args.webhook_url:
        print(
            "INFO: No webhook URL configured (--webhook-url or "
            "HARVEST_WEBHOOK_URL). Skipping notification."
        )
        return 0

    summary_data: dict[str, Any] = {}
    if args.summary_receipt.is_file():
        try:
            summary_data = json.loads(args.summary_receipt.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"WARNING: Could not parse summary receipt: {e}")

    now = datetime.now(UTC).isoformat()
    payload = HarvestNotificationPayload(
        status=str(summary_data.get("status", "success")),
        discovered_datasets=int(summary_data.get("discovered_datasets", 0)),
        evaluated_resources=int(summary_data.get("evaluated_resources", 0)),
        successful_captures=int(summary_data.get("successful_captures", 0)),
        broken_urls_count=int(summary_data.get("broken_urls_count", 0)),
        parquet_derivatives_count=int(summary_data.get("parquet_derivatives_count", 0)),
        hf_repo_url=args.hf_repo_url,
        completed_at=str(summary_data.get("completed_at", now)),
        duration_seconds=float(summary_data.get("duration_seconds", 0.0)),
    )

    print(f"Dispatching harvest alert to webhook: {args.webhook_url[:30]}...")
    try:
        success = asyncio.run(
            dispatch_webhook(
                webhook_url=args.webhook_url,
                payload=payload,
                service=args.service,
            )
        )
    except (TimeoutError, httpx.HTTPError, OSError) as e:
        print(f"ERROR: Failed to dispatch webhook: {e}")
        return 1

    if success:
        print("Successfully delivered webhook notification.")
        return 0

    print("WARNING: Webhook endpoint returned non-2xx status.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
