"""Automated Wayback Machine CDX triangulation and historical snapshot recovery."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import httpx

from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url

if TYPE_CHECKING:
    from archive_govt_nz.object_store import ContentAddressedStore

CDX_API_ENDPOINT = "https://web.archive.org/cdx/search/cdx"
WAYBACK_RAW_PREFIX = "https://web.archive.org/web/{timestamp}id_/{original_url}"
_HTTP_OK = 200
_MIN_CDX_ROWS = 2


@dataclass(frozen=True, slots=True)
class WaybackSnapshot:
    """Historical snapshot location metadata discovered from CDX query."""

    original_url: str
    timestamp: str
    status_code: str
    mimetype: str
    playback_url: str


async def query_wayback_cdx(
    url: str,
    client: httpx.AsyncClient | None = None,
    timeout_seconds: float = 15.0,
) -> WaybackSnapshot | None:
    """Query Internet Archive CDX server for the latest 200 OK snapshot."""
    params = {
        "url": url,
        "output": "json",
        "limit": "1",
        "filter": "statuscode:200",
        "sort": "reverse",
    }
    headers = {
        "User-Agent": "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"
    }

    should_close = False
    if client is None:
        client = httpx.AsyncClient(timeout=timeout_seconds, headers=headers)
        should_close = True

    try:
        response = await client.get(CDX_API_ENDPOINT, params=params)
        if response.status_code != _HTTP_OK:
            return None

        rows = response.json()
        if not isinstance(rows, list) or len(rows) < _MIN_CDX_ROWS:
            return None

        header = rows[0]
        data = rows[1]
        if not isinstance(header, list) or not isinstance(data, list):
            return None

        row_dict = dict(zip(header, data, strict=False))
        timestamp = str(row_dict.get("timestamp", ""))
        orig_url = str(row_dict.get("original", url))
        status = str(row_dict.get("statuscode", "200"))
        mimetype = str(row_dict.get("mimetype", "application/octet-stream"))

        if not timestamp:
            return None

        playback_url = WAYBACK_RAW_PREFIX.format(
            timestamp=timestamp, original_url=orig_url
        )
        return WaybackSnapshot(
            original_url=orig_url,
            timestamp=timestamp,
            status_code=status,
            mimetype=mimetype,
            playback_url=playback_url,
        )
    except httpx.HTTPError, ValueError, KeyError:
        return None
    finally:
        if should_close:
            await client.aclose()


async def recover_broken_resource(
    item: dict[str, Any],
    store: ContentAddressedStore,
    client: httpx.AsyncClient | None = None,
    timeout_seconds: float = 30.0,
) -> dict[str, Any]:
    """Attempt Wayback recovery for one broken resource and ingest into CAS on hit."""
    url = str(item.get("url") or "")
    res_id = str(item.get("resource_id") or "")
    dataset_id = str(item.get("dataset_id") or "")

    should_close = False
    if client is None:
        headers = {
            "User-Agent": "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"
        }
        client = httpx.AsyncClient(timeout=timeout_seconds, headers=headers)
        should_close = True

    try:
        snapshot = await query_wayback_cdx(
            url, client=client, timeout_seconds=timeout_seconds
        )
        if snapshot is None:
            return {
                "resource_id": res_id,
                "dataset_id": dataset_id,
                "original_url": url,
                "recovery_status": "not_in_archive",
                "recovered": False,
            }

        config = CaptureConfig(
            max_bytes=512 * 1024 * 1024,
            timeout_seconds=timeout_seconds,
        )
        capture_res = await capture_url(client, snapshot.playback_url, store, config)
    except (httpx.HTTPError, OSError, CaptureError) as exc:
        return {
            "resource_id": res_id,
            "dataset_id": dataset_id,
            "original_url": url,
            "recovery_status": f"capture_failed: {exc}",
            "recovered": False,
        }
    else:
        return {
            "resource_id": res_id,
            "dataset_id": dataset_id,
            "original_url": url,
            "recovery_status": "recovered",
            "recovered": True,
            "source": "wayback_machine",
            "snapshot_timestamp": snapshot.timestamp,
            "snapshot_url": snapshot.playback_url,
            "object_id": capture_res.receipt.object_id,
            "sha256": capture_res.receipt.sha256,
            "blake3": capture_res.receipt.blake3,
            "byte_count": capture_res.receipt.byte_count,
        }
    finally:
        if should_close:
            await client.aclose()


async def run_wayback_triangulation(
    broken_urls: list[dict[str, Any]],
    store: ContentAddressedStore,
    concurrency: int = 4,
) -> dict[str, Any]:
    """Recover historical snapshots for broken URLs with bounded concurrency."""
    semaphore = asyncio.Semaphore(concurrency)

    async def _bounded_recover(
        item: dict[str, Any], client: httpx.AsyncClient
    ) -> dict[str, Any]:
        async with semaphore:
            return await recover_broken_resource(item, store, client=client)

    headers = {
        "User-Agent": "archive-govt-nz/0.1.0 (+https://github.com/edithatogo/archive-govt-nz)"
    }
    async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
        tasks = [_bounded_recover(item, client) for item in broken_urls]
        results = await asyncio.gather(*tasks)

    recovered_count = sum(1 for r in results if r.get("recovered"))
    return {
        "schema_version": "archive-govt-nz.wayback-recovery-receipt/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_broken_evaluated": len(broken_urls),
        "recovered_count": recovered_count,
        "unrecovered_count": len(broken_urls) - recovered_count,
        "records": results,
    }
