"""Read-only FOI queue health summaries; never release work or renew authority."""

from __future__ import annotations

import json
import re
from collections import Counter
from typing import TYPE_CHECKING, Any, NoReturn

from archive_govt_nz.foi_github_state import LIMIT, MAX_GENERATIONS, SCHEMA
from archive_govt_nz.foi_queue import _decode

if TYPE_CHECKING:
    from archive_govt_nz.foi_scheduler import Job
    from archive_govt_nz.foi_state import StoredState

MAX_DETAIL_SOURCES = 50
_PROGRESS_NAMES = {
    "leased": "capture_in_progress",
    "captured": "captured_not_published",
    "exhausted": "capture_retry_exhausted",
    "blocked": "adapter_blocked",
    "verified": "publication_verified",
    "restricted": "terminal_disposition",
    "withdrawn": "terminal_disposition",
    "unsupported": "terminal_disposition",
}


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _record_progress(
    job: Job, now: int, progress: Counter[str], backlog_ages: list[int]
) -> None:
    if job.status == "pending":
        if job.ready_at <= now:
            progress["backlog_due"] += 1
            backlog_ages.append(now - job.ready_at)
        else:
            progress["backlog_scheduled"] += 1
        return
    name = _PROGRESS_NAMES.get(job.status)
    if name is not None:
        progress[name] += 1


def evaluate(snapshot: dict[str, StoredState], now: int) -> dict[str, Any]:
    """Check pending ownership, active leases and estimated control capacity."""
    if type(now) is not int or now < 0:
        _fail("health_clock")
    findings: Counter[str] = Counter()
    statuses: Counter[str] = Counter()
    affected: set[str] = set()
    progress: Counter[str] = Counter()
    backlog_ages: list[int] = []
    documents = {}
    for source, stored in snapshot.items():
        if (
            re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", source) is None
            or type(stored.version) is not int
            or stored.version < 1
        ):
            _fail("health_source_identity")
        owner, queue = _decode(stored.document)
        if owner.source_id != source:
            _fail("health_source_identity")
        pending = any(job.status in {"pending", "leased"} for job in queue.jobs)
        if pending and now >= owner.expires_at:
            findings["owner_expired_with_unfinished_work"] += 1
            affected.add(source)
        for job in queue.jobs:
            statuses[job.status] += 1
            _record_progress(job, now, progress, backlog_ages)
            if job.status == "leased" and now >= job.expires_at:
                findings["capture_lease_expired"] += 1
                affected.add(source)
        documents[source] = {"version": stored.version, "document": stored.document}
    versions = sum(stored.version for stored in snapshot.values())
    estimated = {
        "schema_version": SCHEMA,
        "generation": versions,
        "documents": documents,
    }
    size = len(
        json.dumps(
            estimated, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    )
    if size * 10 >= LIMIT * 9:
        findings["state_bytes_near_capacity"] += 1
    if versions * 10 >= MAX_GENERATIONS * 9:
        findings["state_versions_near_capacity"] += 1
    incomplete = sum(
        progress[name]
        for name in (
            "backlog_due",
            "backlog_scheduled",
            "capture_in_progress",
            "captured_not_published",
            "capture_retry_exhausted",
            "adapter_blocked",
        )
    )
    control_status = "failed" if findings else "healthy"
    corpus_status = "incomplete" if incomplete else "complete"
    attention = control_status == "failed" or any(
        progress[name]
        for name in (
            "captured_not_published",
            "capture_retry_exhausted",
            "adapter_blocked",
        )
    )
    return {
        "schema_version": "archive-govt-nz.foi-health/v1",
        "status": control_status,
        "monitor_status": ("attention_required" if attention else "healthy"),
        "checked_at_unix": now,
        "sources": len(snapshot),
        "jobs": sum(statuses.values()),
        "job_status_counts": dict(sorted(statuses.items())),
        "finding_counts": dict(sorted(findings.items())),
        "affected_sources": sorted(affected)[:MAX_DETAIL_SOURCES],
        "affected_source_count": len(affected),
        "affected_sources_omitted": max(0, len(affected) - MAX_DETAIL_SOURCES),
        "corpus_progress": {
            "status": corpus_status,
            "counts": dict(sorted(progress.items())),
            "incomplete_jobs": incomplete,
            "oldest_due_backlog_seconds": max(backlog_ages, default=None),
            "control_health_implies_corpus_complete": False,
        },
        "capacity": {
            "estimated": True,
            "state_bytes_estimate": size,
            "state_bytes_limit": LIMIT,
            "source_version_sum_estimate": versions,
            "generation_limit": MAX_GENERATIONS,
            "failure_threshold_percent": 90,
            "basis": (
                "Reconstructed envelope and sum of source versions; "
                "backend global generation is not exposed."
            ),
        },
        "state_modified": False,
        "leases_released": False,
        "publication_performed": False,
    }
