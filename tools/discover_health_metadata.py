"""Bounded metadata-only discovery for health-related CKAN datasets."""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from archive_govt_nz.ckan.client import BoundedCkanClient, CkanClientConfig
from archive_govt_nz.ckan.envelope import CkanTransportError
from archive_govt_nz.health_scope import DEFAULT_SCOPES

DEFAULT_BASE_URL = "https://catalogue.data.govt.nz"
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
        scopes: dict[str, Any] = {}
        receipts: list[dict[str, object]] = []
        for scope in DEFAULT_SCOPES:
            params = {key: value for key, value in scope.items() if key != "id"}
            start = 0
            ids: list[str] = []
            count = 0
            attempt_rows = tuple(dict.fromkeys((page_size, min(page_size, 25), 1)))
            while True:
                page = None
                last_error: CkanTransportError | None = None
                for rows_limit in attempt_rows:
                    try:
                        page = await client.action(
                            "package_search",
                            {**params, "rows": rows_limit, "start": start},
                        )
                        break
                    except CkanTransportError as error:
                        last_error = error
                        receipts.append(
                            {
                                "scope": scope["id"],
                                "start": start,
                                "rows": rows_limit,
                                "status": "unavailable",
                                "status_code": error.status_code,
                                "error_class": error.__class__.__name__,
                            }
                        )
                if page is None and last_error is not None:
                    return {
                        "schema": "archive-govt-nz.health-discovery/v1",
                        "observed_at": datetime.now(tz=UTC).isoformat(),
                        "catalogue_url": base_url,
                        "status": "unavailable",
                        "error_class": last_error.__class__.__name__,
                        "status_code": last_error.status_code,
                        "scopes_attempted": list(scopes),
                        "policy": {
                            "metadata_only": True,
                            "payload_capture": False,
                            "publication": False,
                            "max_page_size": page_size,
                        },
                    }
                page_value = cast("Any", page)
                result = cast("dict[str, Any]", page_value.response.result)
                rows = cast("list[dict[str, Any]]", result.get("results", []))
                count = int(result.get("count", 0))
                ids.extend(
                    str(item["id"])
                    for item in rows
                    if isinstance(item.get("id"), str) and item["id"]
                )
                receipts.append(
                    {
                        "scope": scope["id"],
                        "start": start,
                        "count": count,
                        "returned": len(rows),
                        "sha256": page_value.raw_sha256,
                        "observed_at": page_value.observed_at.isoformat(),
                    }
                )
                if start + len(rows) >= count or not rows:
                    break
                start += page_size
            scopes[str(scope["id"])] = ids
        ordered: list[str] = []
        seen: set[str] = set()
        for ids in scopes.values():
            for identifier in ids:
                if identifier not in seen:
                    seen.add(identifier)
                    ordered.append(identifier)
        return {
            "schema": "archive-govt-nz.health-discovery/v1",
            "observed_at": datetime.now(tz=UTC).isoformat(),
            "catalogue_url": base_url,
            "scopes": scopes,
            "dataset_ids": ordered,
            "dataset_count": len(ordered),
            "pages": receipts,
            "policy": {
                "metadata_only": True,
                "payload_capture": False,
                "publication": False,
                "max_page_size": page_size,
            },
        }


def main() -> int:
    """Run bounded discovery and write a JSON receipt."""
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
    print(
        json.dumps(
            {
                "output": str(args.output),
                "status": document.get("status", "captured"),
                "dataset_count": document.get("dataset_count", 0),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
