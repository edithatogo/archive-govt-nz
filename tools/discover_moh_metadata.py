"""Bounded, metadata-only Ministry of Health CKAN discovery."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from archive_govt_nz.ckan.client import BoundedCkanClient, CkanClientConfig

DEFAULT_BASE_URL = "https://catalogue.data.govt.nz"
ORG = "ministry-of-health"
USER_AGENT = "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"
MAX_PAGE_SIZE = 1000


async def _discover(base_url: str, page_size: int) -> dict[str, object]:
    config = CkanClientConfig(
        base_url=base_url,
        user_agent=USER_AGENT,
        timeout_seconds=20,
        max_attempts=3,
        base_backoff_seconds=1,
        jitter_seconds=0,
        max_response_bytes=8 * 1024 * 1024,
    )
    async with BoundedCkanClient(config) as client:
        org = await client.action(
            "organization_show", {"id": ORG, "include_datasets": False}
        )
        datasets: list[dict[str, object]] = []
        start = 0
        pages: list[dict[str, object]] = []
        while True:
            page = await client.action(
                "package_search",
                {"fq": f"organization:{ORG}", "rows": page_size, "start": start},
            )
            results = cast("dict[str, Any]", page.response.result)
            rows = cast("list[dict[str, Any]]", results.get("results", []))
            count = cast("int", results.get("count", 0))
            for item in rows:
                if isinstance(item.get("id"), str):
                    resources = cast("list[Any] | None", item.get("resources"))
                    datasets.append(
                        {
                            "id": item["id"],
                            "name": item.get("name"),
                            "title": item.get("title"),
                            "metadata_modified": item.get("metadata_modified"),
                            "resource_count": len(resources)
                            if isinstance(resources, list)
                            else 0,
                        }
                    )
            pages.append(
                {
                    "start": start,
                    "count": count,
                    "returned": len(rows),
                    "sha256": page.raw_sha256,
                    "observed_at": page.observed_at.isoformat(),
                }
            )
            if start + len(rows) >= count or not rows:
                break
            start += page_size
        observed = datetime.now(tz=UTC).isoformat()
        return {
            "schema": "archive-govt-nz.moh-discovery/v1",
            "observed_at": observed,
            "catalogue_url": base_url,
            "scope": {
                "organization": ORG,
                "organization_sha256": org.raw_sha256,
                "dataset_count": len(datasets),
                "resource_count": sum(
                    int(cast("int", x["resource_count"])) for x in datasets
                ),
                "datasets": datasets,
                "pages": pages,
            },
            "policy": {
                "metadata_only": True,
                "payload_capture": False,
                "publication": False,
                "max_page_size": page_size,
            },
        }


def main() -> int:
    """Run bounded discovery and write one metadata-only receipt."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--page-size", type=int, default=100)
    args = parser.parse_args()
    if args.page_size < 1 or args.page_size > MAX_PAGE_SIZE:
        raise SystemExit(2)
    document = asyncio.run(_discover(args.base_url, args.page_size))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    scope = document["scope"]
    count = (
        cast("dict[str, object]", scope).get("dataset_count")
        if isinstance(scope, dict)
        else None
    )
    print(
        json.dumps({"output": str(args.output), "dataset_count": count}, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
