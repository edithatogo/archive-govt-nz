"""Run explicitly enabled bounded resource capture with resumable outcomes."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, cast

import httpx

from archive_govt_nz.batch_capture import BatchBudget, admit_batch
from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
from archive_govt_nz.object_store import ContentAddressedStore

HTTP_OK = 200


async def _run(args: argparse.Namespace) -> int:
    """Capture eligible URLs under one bounded budget."""
    if not args.enable:
        print(json.dumps({"status": "not-enabled", "payload_transfer": False}))
        return 0
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    outcomes = plan.get("outcomes", [])
    preflight: dict[str, Any] | None = None
    if args.preflight:
        preflight = cast(
            "dict[str, Any]",
            json.loads(args.preflight.read_text(encoding="utf-8")),
        )
    preflight_results = cast(
        "list[dict[str, Any]]", (preflight or {}).get("results", [])
    )
    observed: set[object] = {
        item.get("resource_id")
        for item in preflight_results
        if item.get("state") == "observed"
        and item.get("status_code") == HTTP_OK
    }
    eligible = [
        item
        for item in outcomes
        if (
            item["decision"]["disposition"] == "eligible"
            or (preflight is not None and item.get("resource_id") in observed)
        )
    ]
    decision = admit_batch(
        BatchBudget(
            max_total_bytes=args.max_total_bytes,
            max_resources=args.max_resources,
            concurrency=args.concurrency,
        ),
        planned_resources=len(eligible),
        planned_bytes=sum(
            int(item["decision"].get("declared_size") or 0) for item in eligible
        ),
    )
    if not decision.allowed:
        print(json.dumps({"status": "budget-denied", "reason": decision.reason}))
        return 2
    semaphore = asyncio.Semaphore(args.concurrency)
    store = ContentAddressedStore(args.object_root)
    results: list[dict[str, object]] = []

    async def one(item: dict[str, object]) -> None:
        async with semaphore:
            resource = item["resource_id"]
            decision_record = cast("dict[str, Any]", item["decision"])
            url = item.get("source_url") or decision_record.get("source_url")
            if not isinstance(url, str) or not url.startswith("https://"):
                results.append(
                    {
                        "resource_id": resource,
                        "state": "unavailable",
                        "error_class": "unsafe_url",
                    }
                )
                return
            try:
                async with httpx.AsyncClient(timeout=args.timeout_seconds) as client:
                    result = await capture_url(
                        client,
                        url,
                        store,
                        CaptureConfig(max_bytes=args.max_resource_bytes),
                    )
                results.append(
                    {
                        "resource_id": resource,
                        "state": "captured",
                        "object_id": result.receipt.object_id,
                    }
                )
            except CaptureError as error:
                results.append(
                    {
                        "resource_id": resource,
                        "state": "failed",
                        "error_class": error.error_class,
                    }
                )

    await asyncio.gather(*(one(item) for item in eligible))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {"schema_version": "archive-govt-nz.capture-run/v1", "results": results},
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "attempted": len(results),
                "output": str(args.output),
            }
        )
    )
    return 0


def main() -> int:
    """Parse explicit capture controls."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--object-root", type=Path, required=True)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--enable", action="store_true")
    parser.add_argument("--max-total-bytes", type=int, default=10 * 1024 * 1024 * 1024)
    parser.add_argument("--max-resources", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--max-resource-bytes", type=int, default=512 * 1024 * 1024)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
