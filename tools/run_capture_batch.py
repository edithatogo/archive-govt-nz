"""Run explicitly enabled bounded resource capture with resumable outcomes."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from time import monotonic
from typing import Any, cast

import httpx

from archive_govt_nz.batch_capture import (
    BatchBudget,
    admit_batch,
    select_eligible_outcomes,
)
from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
from archive_govt_nz.object_store import ContentAddressedStore

HTTP_OK = 200
ELIGIBLE_STATUS_BOUNDARY = 400


RELEASE_AUTHORIZATION_ENV = "ARCHIVE_GOVT_NZ_RELEASE_GATE_APPROVED"


def _authorization_granted() -> bool:
    value = os.environ.get(RELEASE_AUTHORIZATION_ENV, "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _preflight_observed_ids(results: list[dict[str, Any]]) -> set[object]:
    """Extract successful secure probes from both receipt layouts."""
    observed: set[object] = set()
    for item in results:
        if item.get("state") == "observed" and item.get("status_code") == HTTP_OK:
            observed.add(item.get("resource_id"))
        if item.get("state") != "secure-source-observed":
            continue
        attempts = item.get("attempts", [])
        typed_attempts = (
            cast("list[dict[str, Any]]", attempts) if isinstance(attempts, list) else []
        )
        if any(
            attempt.get("state") == "observed"
            and isinstance(attempt.get("status_code"), int)
            and cast("int", attempt["status_code"]) < ELIGIBLE_STATUS_BOUNDARY
            for attempt in typed_attempts
        ):
            observed.add(item.get("resource_id"))
    return observed


async def _run(args: argparse.Namespace) -> int:  # noqa: C901, PLR0915
    """Capture eligible URLs under one bounded budget."""
    if not args.enable:
        print(json.dumps({"status": "not-enabled", "payload_transfer": False}))
        return 0
    if args.require_release_authorization and not _authorization_granted():
        print(
            json.dumps(
                {
                    "status": "not-authorized",
                    "error_class": "release_gate_approval_missing",
                    "payload_transfer": False,
                }
            )
        )
        return 2
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
    observed = _preflight_observed_ids(preflight_results)
    eligible = select_eligible_outcomes(
        outcomes,
        securely_observed_ids=observed if preflight is not None else None,
    )
    decision = admit_batch(
        BatchBudget(
            max_total_bytes=args.max_total_bytes,
            max_resources=args.max_resources,
            concurrency=args.concurrency,
            max_requests_per_second=args.max_requests_per_second,
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
    started = monotonic()
    checkpoint_path = args.checkpoint
    if checkpoint_path and checkpoint_path.exists():
        try:
            previous = json.loads(checkpoint_path.read_text(encoding="utf-8"))
            results.extend(previous.get("results", []))
        except OSError, ValueError, TypeError:
            print(
                json.dumps({"status": "checkpoint-invalid", "payload_transfer": False})
            )
            return 2
    completed = {item.get("resource_id") for item in results}
    checkpoint_lock = asyncio.Lock()
    rate_lock = asyncio.Lock()
    last_request = 0.0
    request_interval = 1.0 / args.max_requests_per_second

    async def acquire_rate_slot() -> None:
        """Enforce a process-wide minimum interval between source requests."""
        nonlocal last_request
        async with rate_lock:
            now = monotonic()
            delay = request_interval - (now - last_request)
            if delay > 0:
                await asyncio.sleep(delay)
            last_request = monotonic()

    async def persist() -> None:
        if checkpoint_path is None:
            return
        checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = checkpoint_path.with_suffix(checkpoint_path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                {
                    "schema_version": "archive-govt-nz.capture-checkpoint/v1",
                    "results": results,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        temporary.replace(checkpoint_path)

    async def one(item: dict[str, object]) -> None:
        async with semaphore:
            if item["resource_id"] in completed:
                return
            if monotonic() - started >= args.max_duration_seconds:
                results.append(
                    {
                        "resource_id": item["resource_id"],
                        "state": "deferred",
                        "error_class": "duration_budget",
                    }
                )
                async with checkpoint_lock:
                    await persist()
                return
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
                async with checkpoint_lock:
                    await persist()
                return
            try:
                await acquire_rate_slot()
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
            async with checkpoint_lock:
                await persist()

    await asyncio.gather(*(one(item) for item in eligible))
    counts: dict[str, int] = {}
    for item in results:
        state = str(item.get("state", "unknown"))
        counts[state] = counts.get(state, 0) + 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.capture-run/v1",
                "results": results,
                "counts": counts,
                "budget": {
                    "max_total_bytes": args.max_total_bytes,
                    "max_resources": args.max_resources,
                    "concurrency": args.concurrency,
                    "max_requests_per_second": args.max_requests_per_second,
                    "max_duration_seconds": args.max_duration_seconds,
                },
                "payload_transfer": bool(eligible),
            },
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
    parser.add_argument("--max-requests-per-second", type=float, default=4.0)
    parser.add_argument("--max-resource-bytes", type=int, default=512 * 1024 * 1024)
    parser.add_argument("--timeout-seconds", type=float, default=60.0)
    parser.add_argument("--max-duration-seconds", type=float, default=3600.0)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument(
        "--require-release-authorization",
        action="store_true",
        help="Require an explicit release-gate approval environment variable.",
    )
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
