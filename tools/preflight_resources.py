"""Read-only bounded resource preflight without payload-body transfer."""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
from typing import Any, cast
from urllib.parse import urljoin

import httpx


async def _probe(
    client: httpx.AsyncClient, resource: dict[str, object], semaphore: asyncio.Semaphore
) -> dict[str, object]:
    """Probe one HTTPS URL with HEAD and bounded redirect handling."""
    async with semaphore:
        decision = cast(dict[str, Any], resource["decision"])
        url = decision.get("source_url")
        if not isinstance(url, str) or not url.startswith("https://"):
            return {"resource_id": resource.get("resource_id"), "state": "unsafe_url"}
        current = url
        redirects: list[str] = []
        try:
            for _ in range(4):
                response = await client.head(current, follow_redirects=False)
                if response.is_redirect:
                    location = response.headers.get("location")
                    if location is None:
                        return {
                            "resource_id": resource.get("resource_id"),
                            "state": "redirect_missing_location",
                        }
                    redirects.append(current)
                    current = urljoin(current, location)
                    continue
                return {
                    "resource_id": resource.get("resource_id"),
                    "state": "observed",
                    "status_code": response.status_code,
                    "final_url": current,
                    "redirect_count": len(redirects),
                    "content_length": response.headers.get("content-length"),
                    "content_type": response.headers.get("content-type"),
                    "etag": response.headers.get("etag"),
                    "last_modified": response.headers.get("last-modified"),
                }
            return {
                "resource_id": resource.get("resource_id"),
                "state": "redirect_limit",
            }
        except httpx.TimeoutException:
            return {"resource_id": resource.get("resource_id"), "state": "timeout"}
        except httpx.HTTPError:
            return {
                "resource_id": resource.get("resource_id"),
                "state": "transport_error",
            }


async def _run(plan: Path, output: Path, concurrency: int, timeout: float) -> int:
    """Probe all planned resources without transferring response bodies."""
    document = json.loads(plan.read_text(encoding="utf-8"))
    semaphore = asyncio.Semaphore(concurrency)
    limits = httpx.Limits(
        max_connections=concurrency, max_keepalive_connections=concurrency
    )
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        results = await asyncio.gather(
            *(_probe(client, item, semaphore) for item in document["outcomes"])
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "schema_version": "archive-govt-nz.preflight/v1",
                "body_transfer": False,
                "results": results,
            },
            indent=2,
        )
        + "\n"
    )
    print(
        json.dumps(
            {"status": "completed", "probed": len(results), "body_transfer": False}
        )
    )
    return 0


def main() -> int:
    """Parse bounded preflight controls."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--concurrency", type=int, default=4)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()
    return asyncio.run(_run(args.plan, args.output, args.concurrency, args.timeout))


if __name__ == "__main__":
    raise SystemExit(main())
