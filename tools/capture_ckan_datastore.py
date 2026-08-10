"""Capture bounded CKAN DataStore pages as raw JSON with integrity receipts."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import httpx

DEFAULT_PAGE_SIZE = 100
DEFAULT_MAX_PAGES = 10_000
DEFAULT_MAX_ROWS = 1_000_000


def _page_url(candidate: str, *, limit: int, offset: int) -> str:
    parsed = urlsplit(candidate)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["limit"] = [str(limit)]
    query["offset"] = [str(offset)]
    return urlunsplit(parsed._replace(query=urlencode(query, doseq=True)))


def _canonical_bytes(document: object) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


async def _capture_one(  # noqa: C901, PLR0911, PLR0913
    client: httpx.AsyncClient,
    resource: dict[str, Any],
    root: Path,
    *,
    page_size: int,
    max_pages: int,
    max_rows: int,
) -> dict[str, Any]:
    candidates = resource.get("datastore_candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return {"resource_id": resource.get("resource_id"), "state": "no_candidate"}
    candidate = str(cast("object", candidates[0]))
    resource_id = str(resource.get("resource_id", ""))
    resource_root = root / resource_id
    pages: list[dict[str, Any]] = []
    rows = 0
    total: int | None = None
    try:
        for page_number in range(max_pages):
            response = await client.get(
                _page_url(candidate, limit=page_size, offset=rows)
            )
            response.raise_for_status()
            document = response.json()
            if not isinstance(document, dict):
                return {"resource_id": resource_id, "state": "protocol_error"}
            typed_document = cast("dict[str, Any]", document)
            if typed_document.get("success") is not True:
                return {"resource_id": resource_id, "state": "protocol_error"}
            raw_result = typed_document.get("result")
            if not isinstance(raw_result, dict):
                return {"resource_id": resource_id, "state": "protocol_error"}
            result = cast("dict[str, Any]", raw_result)
            if not isinstance(result.get("records"), list):
                return {"resource_id": resource_id, "state": "protocol_error"}
            records = cast("list[object]", result["records"])
            if total is None and isinstance(result.get("total"), int):
                total = result["total"]
            encoded = _canonical_bytes(typed_document)
            page_path = resource_root / f"page-{page_number:06d}.json"
            page_path.parent.mkdir(parents=True, exist_ok=True)
            page_path.write_bytes(encoded)
            pages.append(
                {
                    "page": page_number,
                    "offset": rows,
                    "row_count": len(records),
                    "path": str(page_path),
                    "sha256": hashlib.sha256(encoded).hexdigest(),
                    "byte_count": len(encoded),
                }
            )
            rows += len(records)
            if rows > max_rows:
                return {
                    "resource_id": resource_id,
                    "state": "row_limit",
                    "rows": rows,
                    "pages": pages,
                }
            if (
                not records
                or len(records) < page_size
                or (total is not None and rows >= total)
            ):
                return {
                    "resource_id": resource_id,
                    "state": "captured",
                    "rows": rows,
                    "total": total,
                    "pages": pages,
                    "source_url": candidate,
                }
        return {  # noqa: TRY300
            "resource_id": resource_id,
            "state": "page_limit",
            "rows": rows,
            "pages": pages,
        }
    except httpx.HTTPError, OSError, ValueError, TypeError:
        return {"resource_id": resource_id, "state": "capture_failed", "pages": pages}


async def _run(args: argparse.Namespace) -> int:
    recovery = json.loads(args.recovery.read_text(encoding="utf-8"))
    limits = httpx.Limits(
        max_connections=args.concurrency, max_keepalive_connections=args.concurrency
    )
    timeout = httpx.Timeout(args.timeout)
    async with httpx.AsyncClient(
        timeout=timeout, limits=limits, headers={"Accept-Encoding": "identity"}
    ) as client:
        semaphore = asyncio.Semaphore(args.concurrency)

        async def bounded(resource: dict[str, Any]) -> dict[str, Any]:
            async with semaphore:
                return await _capture_one(
                    client,
                    resource,
                    args.output / "raw",
                    page_size=args.page_size,
                    max_pages=args.max_pages,
                    max_rows=args.max_rows,
                )

        results = await asyncio.gather(
            *(bounded(item) for item in recovery.get("resources", []))
        )
    receipt = {
        "schema_version": "archive-govt-nz.ckan-datastore-capture/v1",
        "source_receipt": str(args.recovery),
        "payload_transfer": True,
        "limits": {
            "page_size": args.page_size,
            "max_pages": args.max_pages,
            "max_rows": args.max_rows,
            "concurrency": args.concurrency,
        },
        "results": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "receipt.json").write_text(
        json.dumps(receipt, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": "completed",
                "resources": len(results),
                "output": str(args.output),
            }
        )
    )
    return 0


def main() -> int:
    """Run bounded paginated DataStore capture."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--recovery", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--page-size", type=int, default=DEFAULT_PAGE_SIZE)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--max-rows", type=int, default=DEFAULT_MAX_ROWS)
    parser.add_argument("--concurrency", type=int, default=2)
    parser.add_argument("--timeout", type=float, default=30.0)
    return asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    raise SystemExit(main())
