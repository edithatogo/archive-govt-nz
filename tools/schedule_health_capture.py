"""Run a hash-pinned Health capture plan with an explicit execution switch."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.health_appropriations.source_layout_operations import (
    _read_pinned,
)
from capture_health_resources import _capture, _select_sources

MAX_RESOURCE_BYTES = 256 * 1024 * 1024
MAX_SOURCES = 1000


async def run_plan(
    plan: Path, plan_sha256: str, output: Path, *, execute: bool = False
) -> dict[str, Any]:
    """Preflight a pinned plan or explicitly capture into its durable output root."""
    if type(execute) is not bool:
        msg = "capture_schedule_invalid"
        raise ValueError(msg)
    payload, digest = _read_pinned(str(plan), plan_sha256)
    try:
        config = json.loads(payload)
        if (
            not isinstance(config, dict)
            or set(config)
            != {"schema_version", "census", "census_sha256", "max_resource_bytes"}
            or config["schema_version"] != "archive-govt-nz.health-capture-schedule/v1"
            or not isinstance(config["census"], str)
            or not config["census"]
            or not isinstance(config["census_sha256"], str)
            or type(config["max_resource_bytes"]) is not int
            or not 0 < config["max_resource_bytes"] <= MAX_RESOURCE_BYTES
        ):
            msg = "capture_schedule_invalid"
            raise ValueError(msg)
        census_bytes, census_digest = _read_pinned(
            config["census"], config["census_sha256"]
        )
        census = json.loads(census_bytes)
        selected = _select_sources(census, preservation_only=True)
        if not 0 < len(selected) <= MAX_SOURCES:
            msg = "capture_schedule_source_count_invalid"
            raise ValueError(msg)
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as error:
        msg = "capture_schedule_invalid"
        raise ValueError(msg) from error
    receipt: dict[str, Any] = {
        "schema_version": "archive-govt-nz.health-capture-schedule-receipt/v1",
        "plan_sha256": digest,
        "census_sha256": census_digest,
        "selected": len(selected),
        "status": "planned",
    }
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
