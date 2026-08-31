"""Run shared controls and bounded private capture without publication or cutover."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, NoReturn

import httpx

from archive_govt_nz.foi_discovery import build_reviewed_catalogue
from archive_govt_nz.foi_github_state import GitHubStateStore
from archive_govt_nz.foi_ownership import OwnerFence, require_owner
from archive_govt_nz.foi_queue import QueueRepository, _decode
from archive_govt_nz.foi_scheduler import (
    Budget,
    Job,
    Queue,
    SourcePolicy,
    record_capture,
    reserve,
    retry,
)

ROOT = Path(__file__).resolve().parents[1]
MAX_RECEIPT_BYTES = 65536
GLOBAL_BUDGET = Budget(10, 256 * 1024 * 1024, 600)
BATCH_BUDGET = Budget(1, 64 * 1024 * 1024, 60)
# These are bounded acquisition scopes, never transfer of the full donor source.
ACQUISITION_SCOPES = {
    "ca-federal-atip.nil-returns": "https://open.canada.ca",
    "us-federal-foia.annual-statistics": "https://www.justice.gov",
}


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _scope(source: str) -> str | None:
    for scope in ACQUISITION_SCOPES:
        if source == scope or re.fullmatch(
            re.escape(scope) + r"\.[0-9]+-[0-9]+", source
        ):
            return scope
    return None


def policy(source: str, catalogue: dict[str, Any]) -> SourcePolicy:
    """Resolve safe control scopes; registry membership alone cannot enable capture."""
    if re.fullmatch(r"rehearsal-[0-9]+-[0-9]+", source):
        return SourcePolicy(source, "https://example.org", "eligible", max_attempts=1)
    scope = _scope(source)
    if scope is not None:
        base_id = scope.split(".", 1)[0]
        rows = [row for row in catalogue["sources"] if row["id"] == base_id]
        if len(rows) != 1:
            _fail("acquisition_registry_binding")
        row = rows[0]
        disposition = (
            "restricted"
            if row.get("rights_status") == "restricted" or not row.get("origins")
            else ("eligible" if scope.startswith("ca-") else "executor_required")
        )
        return SourcePolicy(
            source, ACQUISITION_SCOPES[scope], disposition, max_attempts=2
        )
    for row in catalogue["sources"]:
        if row["id"] == source:
            return SourcePolicy(source, "https://example.org", "blocked")
    _fail("unknown_control_scope")


def _policy_hash(source: str, catalogue: dict[str, Any]) -> str:
    selected = policy(source, catalogue)
    value = {
        "source": source,
        "origin": selected.origin,
        "mode": "shared-controls-and-offline-ca-v1",
        "requests": BATCH_BUDGET.requests,
        "bytes": BATCH_BUDGET.bytes,
        "seconds": BATCH_BUDGET.seconds,
        "scopes": ACQUISITION_SCOPES,
        "registry": catalogue["sources"],
        "max_attempts": selected.max_attempts,
        "lease_seconds": selected.lease_seconds,
        "retry_seconds": selected.retry_seconds,
        "global_budget": [
            GLOBAL_BUDGET.requests,
            GLOBAL_BUDGET.bytes,
            GLOBAL_BUDGET.seconds,
        ],
    }
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _all_active(
    store: GitHubStateStore, catalogue: dict[str, Any]
) -> tuple[list[Job], set[str]]:
    jobs: list[Job] = []
    origins: set[str] = set()
    for stored in store.read_all().values():
        owner, queue = _decode(stored.document)
        selected = policy(owner.source_id, catalogue)
        for job in queue.jobs:
            if job.status == "leased":
                if not job.id.startswith(
                    "p" + _policy_hash(job.source_id, catalogue) + "-"
                ):
                    _fail("active_policy_drift")
                jobs.append(job)
                origins.add(selected.origin)
    return jobs, origins


def _global_budget(
    active: list[Job], origins: set[str], selected: SourcePolicy
) -> None:
    if selected.origin in origins or len(active) >= GLOBAL_BUDGET.requests:
        _fail("global_origin_or_job_budget")
    used = (
        sum(job.requests for job in active),
        sum(job.bytes for job in active),
        sum(job.seconds for job in active),
    )
    if any(
        a + b > limit
        for a, b, limit in zip(
            used,
            (BATCH_BUDGET.requests, BATCH_BUDGET.bytes, BATCH_BUDGET.seconds),
            (
                GLOBAL_BUDGET.requests,
                GLOBAL_BUDGET.bytes,
                GLOBAL_BUDGET.seconds,
            ),
            strict=True,
        )
    ):
        _fail("global_resource_budget")


def _authorize(request: argparse.Namespace, selected: SourcePolicy) -> None:
    if selected.disposition != "eligible" or (
        _scope(request.source) is not None
        and (not request.acquisition_authorized or not request.executor_attached)
    ):
        _fail("acquisition_scope_not_authorized")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", request.owner_lease):
        _fail("invalid_owner_lease")


def execute(
    store: GitHubStateStore,
    request: argparse.Namespace,
    catalogue: dict[str, Any],
    now: int,
) -> dict[str, Any]:
    """Persist one fenced control action without invoking an adapter."""
    selected = policy(request.source, catalogue)
    active, origins = _all_active(store, catalogue)
    repository = QueueRepository(store, request.source)
    current = repository.read()
    if request.action == "plan":
        return {
            "status": "planned",
            "authority_commit_sha": store.batch_head,
            "source": request.source,
            "disposition": "executor_required"
            if _scope(request.source) is not None and selected.disposition == "eligible"
            else selected.disposition,
            "version": None if current is None else current.version,
            "global_active_jobs": len(active),
            "capture_executed": False,
            "raw_publication_verified": False,
            "cutover": False,
        }
    _authorize(request, selected)
    job_id = (
        "p"
        + _policy_hash(request.source, catalogue)
        + "-"
        + hashlib.sha256(request.owner_lease.encode()).hexdigest()[:16]
    )
    if request.action == "enqueue":
        if request.expected_version is not None:
            _fail("enqueue_requires_absent_scope")
        owner = OwnerFence(
            request.source,
            "edithatogo/archive-govt-nz",
            1,
            request.owner_lease,
            now + 3600,
        )
        result = repository.initialize(
            owner,
            Queue(
                (
                    Job(
                        job_id,
                        request.source,
                        now,
                        BATCH_BUDGET.requests,
                        BATCH_BUDGET.bytes,
                        BATCH_BUDGET.seconds,
                    ),
                )
            ),
            now,
        )
    else:
        if (
            current is None
            or request.expected_version != current.version
            or request.owner_lease != current.owner.lease_id
        ):
            _fail("expected_control_state_required")
        if request.action == "reserve":
            _global_budget(active, origins, selected)
            if any(job.id != job_id for job in current.queue.jobs):
                _fail("active_policy_drift")
            result = repository.transact(
                current.version,
                current.owner,
                now,
                lambda queue: reserve(
                    queue, (selected,), BATCH_BUDGET, now, "job-" + request.owner_lease
                ),
            )
        elif request.action == "reconcile":
            # The only terminal outcome this tool can establish itself is its own
            # deliberately failed control rehearsal: no external capture ran.
            if not request.source.startswith("rehearsal-"):
                _fail("executor_terminal_receipt_required")
            result = repository.transact(
                current.version,
                current.owner,
                now,
                lambda queue: retry(
                    queue,
                    job_id,
                    "job-" + request.owner_lease,
                    selected,
                    now,
                    terminal_failure_verified=True,
                ),
            )
        else:
            _fail("unknown_control_action")
    return {
        "status": "persisted",
        "authority_commit_sha": store.batch_head,
        "source": request.source,
        "action": request.action,
        "version": result.version,
        "jobs": [job.status for job in result.queue.jobs],
        "capture_executed": False,
        "raw_publication_verified": False,
        "cutover": False,
    }


def _pilot_step(arguments: list[str], deadline: float) -> dict[str, Any]:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        _fail("executor_runtime_budget")
    result = subprocess.run(  # noqa: S603 - fixed local offline tool, no shell
        [sys.executable, str(ROOT / "tools/foi_country_pilot.py"), *arguments],
        check=False,
        capture_output=True,
        text=True,
        timeout=remaining,
    )
    if result.returncode != 0 or len(result.stdout) > MAX_RECEIPT_BYTES:
        _fail("offline_executor_failed")
    value = json.loads(result.stdout)
    if not isinstance(value, dict) or value.get("public_upload") is not False:
        _fail("offline_executor_receipt")
    return value


def _admit(
    store: GitHubStateStore, request: argparse.Namespace, version: int, now: int
) -> None:
    stored = store.read(request.source)
    if stored is None or stored.version != version:
        _fail("executor_reservation_changed")
    owner, queue = _decode(stored.document)
    require_owner(owner, "edithatogo/archive-govt-nz", 1, request.owner_lease, now)
    if (
        len(queue.jobs) != 1
        or queue.jobs[0].status != "leased"
        or queue.jobs[0].lease_id != "job-" + request.owner_lease
        or not queue.jobs[0].ready_at <= now < queue.jobs[0].expires_at
    ):
        _fail("executor_reservation_required")


def capture_ca(
    store: GitHubStateStore,
    request: argparse.Namespace,
    catalogue: dict[str, Any],
    outcomes: list[dict[str, Any]],
) -> None:
    """Preserve and restore retained CA bytes under a shared reservation."""
    if (
        _scope(request.source) != "ca-federal-atip.nil-returns"
        or request.input_root is None
        or request.output_root is None
    ):
        _fail("offline_executor_inputs")
    source, output = request.input_root, request.output_root
    restored = output.with_name(output.name + "-restore")
    if source.is_symlink() or output.exists() or restored.exists():
        _fail("offline_executor_paths")
    names = ("ati-nil.csv", "ati-schema.json", "source-metadata.json")
    if any(
        (source / name).is_symlink() or not (source / name).is_file() for name in names
    ):
        _fail("offline_executor_paths")
    if sum((source / name).stat().st_size for name in names) > 24 * 1024 * 1024:
        _fail("offline_executor_bytes")
    request.executor_attached = True
    for action in ("enqueue", "reserve"):
        request.action = action
        request.expected_version = outcomes[-1]["version"] if outcomes else None
        outcomes.append(execute(store, request, catalogue, int(time.time())))
    reserved_version = outcomes[-1]["version"]
    _admit(store, request, reserved_version, int(time.time()))
    outcomes.append(
        {
            "status": "capture_attempted",
            "authority_commit_sha": store.batch_head,
            "capture_attempted": True,
            "capture_executed": None,
            "local_verification_completed": False,
        }
    )
    deadline = time.monotonic() + BATCH_BUDGET.seconds
    prepared = _pilot_step(
        ["prepare", "--source", str(source), "--output", str(output)], deadline
    )
    digest = prepared["manifest_sha256"]
    outcomes.append(
        {
            "status": "package_prepared",
            "authority_commit_sha": store.batch_head,
            "manifest_sha256": digest,
            "capture_executed": True,
            "local_verification_completed": False,
        }
    )
    proof = _pilot_step(
        [
            "restore",
            "--source",
            str(output),
            "--output",
            str(restored),
            "--manifest-sha256",
            digest,
        ],
        deadline,
    )
    if proof.get("manifest_sha256") != digest:
        _fail("offline_executor_restore")
    if (
        sum(
            path.stat().st_size
            for folder in (output, restored)
            for path in folder.iterdir()
        )
        > BATCH_BUDGET.bytes
    ):
        _fail("offline_executor_bytes")
    outcomes.append(
        {
            "status": "local_restore_verified",
            "authority_commit_sha": store.batch_head,
            "manifest_sha256": digest,
            "capture_executed": True,
            "local_verification_completed": True,
        }
    )
    store.read_all()
    repository = QueueRepository(store, request.source)
    current = repository.read()
    if (
        current is None
        or current.version != reserved_version
        or current.owner.lease_id != request.owner_lease
    ):
        _fail("expected_control_state_required")
    job = current.queue.jobs[0]
    result = repository.transact(
        current.version,
        current.owner,
        int(time.time()),
        lambda queue: record_capture(
            queue,
            job.id,
            "job-" + request.owner_lease,
            int(time.time()),
            manifest_sha256=digest,
            locally_verified=True,
        ),
    )
    outcomes.append(
        {
            "status": "captured_locally",
            "authority_commit_sha": store.batch_head,
            "source": request.source,
            "version": result.version,
            "manifest_sha256": digest,
            "capture_executed": True,
            "origin_requests": 0,
            "raw_publication_verified": False,
            "cutover": False,
        }
    )


def _arguments() -> argparse.Namespace:
    """Read an explicit command without overwriting earlier evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("plan", "enqueue", "reserve", "reconcile", "rehearsal", "capture-ca"),
    )
    parser.add_argument("--source", required=True)
    parser.add_argument("--owner-lease", default="")
    parser.add_argument("--expected-version", type=int)
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--input-root", type=Path)
    parser.add_argument("--output-root", type=Path)
    parser.set_defaults(executor_attached=False)
    parser.add_argument("--bootstrap", action="store_true")
    parser.add_argument("--acquisition-authorized", action="store_true")
    request = parser.parse_args()
    if request.receipt.exists():
        parser.error("receipt already exists")
    return request


def main() -> int:
    """Run bounded shared controls and preserve sanitized outcomes."""
    request = _arguments()
    outcomes: list[dict[str, Any]] = []
    bootstrap_sha: str | None = None
    try:
        token = os.environ.get("GH_TOKEN", "")
        if not token:
            _fail("credential_required")
        with httpx.Client(
            headers={
                "Authorization": "Bearer " + token,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30,
        ) as client:
            store = GitHubStateStore(client)
            if request.bootstrap:
                bootstrap_sha = store.bootstrap()
            catalogue = build_reviewed_catalogue(ROOT / "config/foi")
            if request.action == "capture-ca":
                capture_ca(store, request, catalogue, outcomes)
            elif request.action == "rehearsal":
                if not re.fullmatch(r"rehearsal-[0-9]+-[0-9]+", request.source):
                    _fail("rehearsal_scope_required")
                for action in ("enqueue", "reserve", "reconcile", "plan"):
                    request.action = action
                    request.expected_version = (
                        outcomes[-1]["version"] if outcomes else None
                    )
                    outcomes.append(
                        execute(store, request, catalogue, int(time.time()))
                    )
            else:
                outcomes.append(execute(store, request, catalogue, int(time.time())))
        result = {
            "status": "passed",
            "bootstrap_sha": bootstrap_sha,
            "outcomes": outcomes,
            "capture_executed": any(
                row.get("capture_executed") is True for row in outcomes
            ),
            "cutover": False,
        }
        code = 0
    except (
        ValueError,
        OSError,
        httpx.HTTPError,
        KeyError,
        TypeError,
        subprocess.TimeoutExpired,
    ) as error:
        result = {
            "status": "failed",
            "bootstrap_sha": bootstrap_sha,
            "error_class": type(error).__name__,
            "outcomes": outcomes,
            "remote_state": "inspect_before_retry",
            "capture_executed": True
            if any(row.get("capture_executed") is True for row in outcomes)
            else (
                None if any(row.get("capture_attempted") for row in outcomes) else False
            ),
            "local_verification_completed": any(
                row.get("local_verification_completed") is True for row in outcomes
            ),
            "cutover": False,
        }
        code = 1
    try:
        request.receipt.parent.mkdir(parents=True, exist_ok=True)
        with request.receipt.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, indent=2)
            handle.write("\n")
    except OSError:
        result["receipt_saved"] = False
        result["status"] = "receipt_save_failed"
        code = 1
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
