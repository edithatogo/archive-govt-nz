"""One bounded report work stream using the qualified existing archive components."""

from __future__ import annotations

import asyncio
import time
from dataclasses import replace
from typing import TYPE_CHECKING, Literal

import httpx

from archive_govt_nz.parliament.hosted_transport import legacy_source_guard
from archive_govt_nz.parliament.pipeline import USER_AGENT, Bounds, ParliamentArchive
from archive_govt_nz.parliament.publication import publish_batch
from archive_govt_nz.parliament.reports import DEFAULT_PAGE_SIZE, ReportQuery

REPORT_PAGE_SIZE = DEFAULT_PAGE_SIZE

if TYPE_CHECKING:
    from pathlib import Path


async def collect_reports(
    archive: ParliamentArchive, mode: Literal["historical", "recent"], bounds: Bounds
) -> dict[str, object]:
    """Run bounded discovery then capture, keeping their checkpoints separate."""
    if bounds.max_records < REPORT_PAGE_SIZE or bounds.max_records % REPORT_PAGE_SIZE:
        message = "worker_record_bound_requires_complete_pages"
        raise ValueError(message)
    discovered = 0
    discovery_bytes = 0
    page = 1
    started = time.monotonic()
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as client:
        async with asyncio.timeout(bounds.max_seconds):
            while (
                discovered < bounds.max_records and discovery_bytes < bounds.max_bytes
            ):
                query = (
                    ReportQuery(page=page, page_size=REPORT_PAGE_SIZE)
                    if mode == "recent"
                    else None
                )
                result = await archive.reports(
                    client,
                    partition=mode,
                    query=query,
                    require_unfiltered=True,
                    bounds=replace(
                        bounds, max_bytes=bounds.max_bytes - discovery_bytes
                    ),
                )
                discovered += int(str(result["discovered"]))
                discovery_bytes += int(str(result.get("bytes", 0)))
                if result.get("status") == "spool_bound_reached":
                    return {
                        "discovered": discovered,
                        "bytes": discovery_bytes,
                        "status": "spool_bound_reached",
                    }
                if result.get("next_page") is None:
                    break
                page += 1
            remaining = bounds.max_seconds - (time.monotonic() - started)
            if remaining <= 0 or discovery_bytes >= bounds.max_bytes:
                return {
                    "discovered": discovered,
                    "bytes": discovery_bytes,
                    "status": "run_bound_reached",
                }
            capture = await archive.capture(
                client,
                Bounds(
                    max_records=bounds.max_records,
                    max_bytes=bounds.max_bytes - discovery_bytes,
                    max_seconds=remaining,
                    max_file_bytes=bounds.max_file_bytes,
                    max_spool_bytes=bounds.max_spool_bytes,
                ),
            )
    return {
        "discovered": discovered,
        **capture,
        "discovery_bytes": discovery_bytes,
        "bytes": discovery_bytes + int(str(capture["bytes"])),
    }


def run_reports(
    state_dir: Path,
    *,
    mode: Literal["historical", "recent"] = "historical",
    bounds: Bounds | None = None,
) -> dict[str, object]:
    """Capture and publish one bounded batch without claiming full coverage."""
    archive = ParliamentArchive(state_dir)
    archive.source_guard = legacy_source_guard
    pending = archive.pending_report_batch()
    if pending:
        return {
            "recovered_publication": publish_batch(archive, pending),
            "summary": archive.summary(),
        }
    result = asyncio.run(collect_reports(archive, mode, bounds or Bounds()))
    if result.get("status") == "spool_bound_reached":
        return {**result, "summary": archive.summary()}
    decisions = archive.report_decisions()
    if decisions:
        batch = archive.package(decisions)
        result["publication"] = publish_batch(archive, str(batch["batch"]))
    result["summary"] = archive.summary()
    return result
