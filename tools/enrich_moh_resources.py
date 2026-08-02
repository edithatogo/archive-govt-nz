"""Collect resource-level CKAN metadata without downloading payloads."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from archive_govt_nz.ckan.client import BoundedCkanClient, CkanClientConfig


async def _run(source: dict[str, Any]) -> dict[str, object]:
    datasets = cast("dict[str, Any]", source["scope"])["datasets"]
    config = CkanClientConfig(
        base_url="https://catalogue.data.govt.nz",
        user_agent="archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)",
        timeout_seconds=20,
        max_attempts=3,
        base_backoff_seconds=1,
        jitter_seconds=0,
        max_response_bytes=8 * 1024 * 1024,
    )
    records: list[dict[str, object]] = []
    async with BoundedCkanClient(config) as client:
        for dataset in cast("list[dict[str, Any]]", datasets):
            package = await client.action("package_show", {"id": dataset["id"]})
            result = cast("dict[str, Any]", package.response.result)
            for resource in cast("list[dict[str, Any]]", result.get("resources", [])):
                records.append(  # noqa: PERF401
                    {
                        "dataset_id": dataset["id"],
                        "dataset_title": dataset.get("title"),
                        "resource_id": resource.get("id"),
                        "name": resource.get("name"),
                        "url": resource.get("url"),
                        "format": resource.get("format"),
                        "mimetype": resource.get("mimetype"),
                        "rights": resource.get("rights"),
                        "metadata_sha256": package.raw_sha256,
                    }
                )
    return {
        "schema": "archive-govt-nz.moh-resource-metadata/v1",
        "observed_at": datetime.now(tz=UTC).isoformat(),
        "source_observed_at": source.get("observed_at"),
        "metadata_only": True,
        "payload_capture": False,
        "publication": False,
        "resource_count": len(records),
        "resources": records,
    }


def main() -> int:
    """Write resource metadata enrichment evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = cast("dict[str, Any]", json.loads(args.input.read_text(encoding="utf-8")))
    result = asyncio.run(_run(source))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"output": str(args.output), "resource_count": result["resource_count"]}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
