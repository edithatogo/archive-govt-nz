"""Domain-throttled concurrent batch capture for global preservation."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import httpx

from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url

if TYPE_CHECKING:
    from archive_govt_nz.object_store import ContentAddressedStore


@dataclass(frozen=True, slots=True)
class GlobalBatchCaptureConfig:
    """Configuration for concurrency, domain rate-limiting, and transfer bounds."""

    max_workers: int = 8
    max_concurrency_per_host: int = 2
    requests_per_second_per_host: float = 4.0
    timeout_seconds: float = 45.0
    max_bytes_per_file: int = 512 * 1024 * 1024
    user_agent: str = "archive-govt-nz-preservation/1.0 (+https://github.com/edithatogo/archive-govt-nz)"


@dataclass(slots=True)
class GlobalCaptureOutcome:
    """Outcome for a single candidate processed during batch capture."""

    dataset_id: str
    resource_id: str
    url: str
    status: str
    reason: str
    http_status: int | None = None
    sha256: str | None = None
    blake3: str | None = None
    bytes_captured: int | None = None
    elapsed_seconds: float = 0.0


async def run_global_batch_capture(
    candidates: list[dict[str, Any]],
    store: ContentAddressedStore,
    config: GlobalBatchCaptureConfig | None = None,
) -> dict[str, Any]:
    """Process candidates concurrently with per-host throttling and CAS storage."""
    active_config = config or GlobalBatchCaptureConfig()
    capture_cfg = CaptureConfig(
        max_bytes=active_config.max_bytes_per_file,
        timeout_seconds=active_config.timeout_seconds,
    )

    host_semaphores: dict[str, asyncio.Semaphore] = {}
    worker_semaphore = asyncio.Semaphore(active_config.max_workers)

    def get_host_semaphore(url: str) -> asyncio.Semaphore:
        parsed = urlparse(url)
        host = parsed.netloc.lower() or "default"
        if host not in host_semaphores:
            host_semaphores[host] = asyncio.Semaphore(
                active_config.max_concurrency_per_host
            )
        return host_semaphores[host]

    headers = {"User-Agent": active_config.user_agent}
    successful: list[dict[str, Any]] = []
    broken_urls: list[dict[str, Any]] = []
    skipped_tombstones = 0

    async with httpx.AsyncClient(headers=headers, follow_redirects=False) as client:

        async def process_candidate(cand: dict[str, Any]) -> None:
            nonlocal skipped_tombstones
            dataset_id = str(cand.get("dataset_id") or "")
            resource_id = str(cand.get("resource_id") or "")
            url = str(cand.get("url") or "")
            authorized = bool(cand.get("download_authorized", False))

            if not authorized:
                skipped_tombstones += 1
                return

            host_sem = get_host_semaphore(url)
            async with worker_semaphore, host_sem:
                try:
                    result = await capture_url(client, url, store, config=capture_cfg)
                    successful.append(
                        {
                            "dataset_id": dataset_id,
                            "resource_id": resource_id,
                            "url": url,
                            "sha256": result.receipt.sha256,
                            "blake3": result.receipt.blake3,
                            "byte_count": result.receipt.byte_count,
                            "content_type": result.content_type,
                            "http_status": result.status_code,
                            "elapsed_seconds": result.elapsed_seconds,
                        }
                    )
                except CaptureError as exc:
                    broken_urls.append(
                        {
                            "dataset_id": dataset_id,
                            "resource_id": resource_id,
                            "url": url,
                            "error_class": exc.error_class,
                            "attempts": [
                                {
                                    "url": a.url,
                                    "status_code": a.status_code,
                                    "outcome": a.outcome,
                                }
                                for a in exc.attempts
                            ],
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    broken_urls.append(
                        {
                            "dataset_id": dataset_id,
                            "resource_id": resource_id,
                            "url": url,
                            "error_class": "unexpected_exception",
                            "error_detail": str(exc),
                        }
                    )

        tasks = [process_candidate(cand) for cand in candidates]
        await asyncio.gather(*tasks)

    return {
        "schema_version": "archive-govt-nz.global-batch-capture/v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "total_candidates": len(candidates),
        "admitted_for_capture": len(successful) + len(broken_urls),
        "skipped_tombstones": skipped_tombstones,
        "successful_count": len(successful),
        "broken_url_count": len(broken_urls),
        "successful_captures": successful,
        "broken_urls": broken_urls,
    }
