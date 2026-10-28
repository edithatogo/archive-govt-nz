"""Run a hash-pinned Health capture plan with an explicit execution switch."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.health_appropriations.capture_schedule import (
    preflight_plan,
)
from capture_health_resources import _capture


async def run_plan(
    plan: Path, plan_sha256: str, output: Path, *, execute: bool = False
) -> dict[str, Any]:
    """Preflight a pinned plan or explicitly capture into its durable output root."""
    if type(execute) is not bool:
        msg = "capture_schedule_invalid"
        raise ValueError(msg)
    config, receipt = preflight_plan(plan, plan_sha256)
    census_digest = receipt["census_sha256"]
    if not execute:
        return receipt
    args = argparse.Namespace(
        census=Path(config["census"]),
        census_sha256=census_digest,
        store_root=output / "objects",
        warc_dir=output / "warcs",
        manifest=output / "manifest.json",
        max_resource_bytes=config["max_resource_bytes"],
        preservation_only=True,
        resume=True,
    )
    result = await _capture(args)
    receipt["captured"] = result["captured"]
    receipt["status"] = (
        "completed" if result["captured"] == result["selected"] else "partial"
    )
    return receipt


def main() -> int:
    """Run the scheduler command and emit a compact receipt."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    result = asyncio.run(
        run_plan(args.plan, args.plan_sha256, args.output, execute=args.execute)
    )
    print(json.dumps(result, sort_keys=True))
    return 2 if result["status"] == "partial" else 0


if __name__ == "__main__":
    raise SystemExit(main())
