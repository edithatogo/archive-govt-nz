"""Non-interactive Parliament operations with explicit durable state selection."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Literal

import httpx

from archive_govt_nz.parliament.pipeline import USER_AGENT, Bounds, ParliamentArchive
from archive_govt_nz.parliament.publication import publish_batch
from archive_govt_nz.parliament.reports import ReportQuery
from archive_govt_nz.parliament.worker import run_reports

if TYPE_CHECKING:
    from pathlib import Path

Action = Literal[
    "run-reports",
    "status",
    "discover",
    "reports",
    "capture",
    "verify",
    "package",
    "publish",
    "retry",
    "refresh",
]


async def _network(  # noqa: PLR0913 - explicit network operation inputs
    archive: ParliamentArchive,
    action: str,
    url: str | None,
    partition: str,
    bounds: Bounds,
    *,
    query: ReportQuery | None,
) -> dict[str, object]:
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as client:
        if action == "reports":
            return await archive.reports(
                client,
                partition=partition,
                query=query,
                bounds=bounds,
            )
        if action == "discover":
            if not url:
                message = "source_url_required"
                raise ValueError(message)
            return await archive.discover(client, url, partition=partition)
        return await archive.capture(client, bounds)


def _run(state_dir: Path, partition: str, bounds: Bounds) -> dict[str, object]:
    if partition not in {"historical", "recent"}:
        message = "invalid_report_partition"
        raise ValueError(message)
    mode = "recent" if partition == "recent" else "historical"
    return run_reports(state_dir, mode=mode, bounds=bounds)


def execute(  # noqa: PLR0913 - mirrors the public CLI operation options
    action: Action,
    state_dir: Path,
    *,
    source_url: str | None = None,
    partition: str = "historical",
    decisions_path: Path | None = None,
    source_id: str | None = None,
    batch_id: str | None = None,
    max_records: int = 100,
    max_bytes: int = 250 * 1024 * 1024,
    max_seconds: float = 900,
    max_spool_bytes: int = 1024 * 1024 * 1024,
    page: int | None = None,
    keyword: str = "",
) -> dict[str, object]:
    """Run one bounded operation without enabling schedules or new services."""
    bounds = Bounds(
        max_records=max_records,
        max_bytes=max_bytes,
        max_seconds=max_seconds,
        max_spool_bytes=max_spool_bytes,
    )
    if action == "run-reports":
        return _run(state_dir, partition, bounds)
    archive = ParliamentArchive(state_dir)
    if action in {"status", "verify"}:
        return archive.summary() if action == "status" else dict(archive.verify())
    if action in {"retry", "refresh"}:
        if not source_id:
            message = "source_id_required"
            raise ValueError(message)
        archive.requeue(source_id, refresh=action == "refresh")
        return {"status": "pending", "source_id": source_id}
    if action == "package":
        decisions = (
            archive.report_decisions()
            if decisions_path is None
            else json.loads(decisions_path.read_text(encoding="utf-8"))
        )
        return archive.package(decisions)
    if action == "publish":
        if not batch_id:
            message = "batch_id_required"
            raise ValueError(message)
        return dict(publish_batch(archive, batch_id))
    if action not in {"discover", "reports", "capture"}:
        message = "unsupported_parliament_action"
        raise ValueError(message)
    query = (
        ReportQuery(page=page or 1, keyword=keyword)
        if page is not None or keyword
        else None
    )
    return asyncio.run(
        _network(archive, action, source_url, partition, bounds, query=query)
    )
