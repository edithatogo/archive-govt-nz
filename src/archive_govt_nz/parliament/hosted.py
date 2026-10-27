"""Finite hosted jobs over durable, serial, rights-gated report attempts."""

from __future__ import annotations

import asyncio
import io
import json
import os
import re
import signal
import sqlite3
import subprocess
import sys
import time
import uuid
import zipfile
from contextlib import closing, contextmanager
from typing import TYPE_CHECKING, Any
lazy from pathlib import Path

import httpx

from archive_govt_nz.parliament.hosted_checkpoint import Checkpoints
from archive_govt_nz.parliament.hosted_state import canonical, digest
from archive_govt_nz.parliament.hosted_transport import (
    POINTER,
    NativeTransport,
    abort,
)
from archive_govt_nz.parliament.lease import file_lock
from archive_govt_nz.parliament.pipeline import USER_AGENT, Bounds, ParliamentArchive
from archive_govt_nz.parliament.publication import publish_batch
from archive_govt_nz.parliament.reports import ReportQuery

if TYPE_CHECKING:
    from collections.abc import Iterator

LATE_SLOT = 9
DEEP_SLOT = 8
MAX_RECORDS = 100
PROOF_RUN_COUNT = 3
MAX_JOB_BATCHES = 1000
MAX_JOB_SECONDS = 14400
MAX_HOLD_SECONDS = 300


def github_run(run: str, attempt: str | None = None) -> dict[str, Any]:
    """Read an exact native run/attempt without handling token values ourselves."""
    if not re.fullmatch(r"[0-9]{1,20}", run) or (
        attempt is not None and not re.fullmatch(r"[0-9]{1,10}", attempt)
    ):
        abort("github_run_identity")
    url = "repos/edithatogo/archive-govt-nz/actions/runs/" + run
    if attempt is not None:
        url += "/attempts/" + attempt
    result = subprocess.run(  # noqa: S603 - fixed gh command and validated IDs
        ["gh", "api", url],  # noqa: S607 - qualified existing CLI
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    value = json.loads(result.stdout)
    if (
        value["path"] != ".github/workflows/parliament-continuation.yml"
        or value["head_branch"] != "main"
        or value["event"] not in {"workflow_dispatch", "schedule"}
    ):
        abort("github_run_authority")
    return value


def github_receipt(run: str) -> dict[str, Any]:
    """Read the single sanitized receipt from this exact trusted workflow run."""
    github_run(run)
    endpoint = "repos/edithatogo/archive-govt-nz/actions/runs/" + run + "/artifacts"
    listing = subprocess.run(  # noqa: S603 - fixed gh, validated run ID
        ["gh", "api", endpoint],  # noqa: S607 - qualified native CLI
        check=True,
        capture_output=True,
        timeout=30,
    )
    artifacts = [
        a
        for a in json.loads(listing.stdout)["artifacts"]
        if a["name"].startswith("parliament-receipt-" + run + "-") and not a["expired"]
    ]
    if len(artifacts) != 1 or artifacts[0]["size_in_bytes"] > 1024 * 1024:
        abort("native_receipt_missing")
    artifact_id = artifacts[0]["id"]
    if type(artifact_id) is not int or artifact_id <= 0:
        abort("native_receipt_identity")
    endpoint = (
        "repos/edithatogo/archive-govt-nz/actions/artifacts/"
        + str(artifact_id)
        + "/zip"
    )
    download = subprocess.run(  # noqa: S603 - fixed gh, native integer ID
        ["gh", "api", endpoint],  # noqa: S607 - qualified native CLI
        check=True,
        capture_output=True,
        timeout=30,
    )
    with zipfile.ZipFile(io.BytesIO(download.stdout)) as archive:
        files = archive.infolist()
        if (
            len(files) != 1
            or files[0].filename != "receipt.json"
            or files[0].file_size > 1024 * 1024
        ):
            abort("native_receipt_shape")
        return json.loads(archive.read(files[0]))


def terminal_owner(owner: str | None) -> bool:
    """Allow early takeover only after exact native GitHub terminal readback."""
    match = re.fullmatch(r"gha_([0-9]{1,20})_([0-9]{1,10})", owner or "")
    return bool(match and github_run(match[1], match[2])["status"] == "completed")


def controls(archive: ParliamentArchive) -> dict[str, Any]:
    """Read only the report cursor map."""
    with closing(sqlite3.connect(archive.database)) as connection, connection:
        return {
            k: json.loads(v)
            for k, v in connection.execute(
                "SELECT key,value FROM control WHERE key LIKE 'reports:%'"
            )
        }


def begin(manager: Checkpoints) -> None:
    """Select one small recoverable page, with alternating recent/history lanes."""
    archive = manager.archive
    if archive is None:
        abort("hosted_archive_missing")
    cursor = controls(archive)
    recent = manager.cycle % 2 == 0
    query = {"page": (manager.cycle // 2) % 10 + 1, "page_size": 10, "keyword": ""}
    partition = "recent"
    if not recent:
        round_number = manager.cycle // 2
        if round_number % 10 == LATE_SLOT:
            partition = "late-attachment-reconciliation-20261027"
            query.update(page=1, keyword="Tāmaki Redevelopment")
        elif (
            round_number % 10 == DEEP_SLOT
            or cursor.get("reports:historical", {}).get("page", 1) is None
        ):
            partition = "historical-reconciliation-20261027"
            query = cursor.get(
                "reports:" + partition, {"page": 1, "page_size": 10, "keyword": ""}
            )
            # A completed sweep starts a new observed reconciliation epoch;
            # it never converts terminal pagination into archive completeness.
            if query["page"] is None:
                query = {"page": 1, "page_size": 10, "keyword": ""}
        else:
            partition = "historical"
            query = cursor.get(
                "reports:historical", {"page": 1, "page_size": 10, "keyword": ""}
            )
    pending = int(str(archive.summary()["pending"]))
    manager.work = {
        "phase": "capture" if pending else "discover",
        "query": query,
        "partition": partition,
        "bytes": 0,
        "observed": 0,
        "captured": 0,
        "seconds": 0.0,
        "reserved": 0,
        "interrupted": False,
        "invocation": manager.owner,
    }
    manager.last_tick = time.monotonic()
    manager.save()


def retry_transport_once(archive: ParliamentArchive, source_id: str) -> bool:
    """Requeue only one identified transient read, preserving the first failure."""
    with closing(sqlite3.connect(archive.database)) as connection, connection:
        row = connection.execute(
            "SELECT status,last_error FROM records WHERE source_id=?", (source_id,)
        ).fetchone()
        count = connection.execute(
            "SELECT count(*) FROM events WHERE source_id=? "
            "AND status='retry_requested'",
            (source_id,),
        ).fetchone()[0]
    if (
        row is None
        or row[0] != "failed"
        or row[1]
        not in {
            "transport_retryable",
            "ReadTimeout",
            "ConnectTimeout",
            "ReadError",
            "ConnectError",
        }
        or count
    ):
        return False
    archive.requeue(source_id)
    return True


async def acquire(manager: Checkpoints) -> None:
    """Preserve per-file milestones before source counters can advance."""
    archive = manager.archive
    if archive is None or manager.work is None:
        abort("hosted_state_missing")
    async with httpx.AsyncClient(headers={"User-Agent": USER_AGENT}) as client:
        if manager.work["phase"] == "discover":
            manager.work["reserved"] = 4 * 1024 * 1024
            manager.save()
            async with asyncio.timeout(900 - manager.work["seconds"]):
                result = await archive.reports(
                    client,
                    partition=manager.work["partition"],
                    query=ReportQuery(**manager.work["query"]),
                    bounds=Bounds(
                        max_records=10,
                        max_bytes=262144000,
                        max_seconds=900,
                        max_spool_bytes=8589934592,
                    ),
                )
            if result.get("status"):
                abort("discovery_deferred")
        while archive.summary()["pending"] and manager.work["captured"] < MAX_RECORDS:
            manager.tick()
            remaining = 900 - manager.work["seconds"]
            available = 262144000 - manager.work["bytes"]
            if remaining <= 0 or available <= 0:
                break
            manager.work["reserved"] = min(64 * 1024 * 1024, available)
            with closing(sqlite3.connect(archive.database)) as connection, connection:
                target = connection.execute(
                    "SELECT source_id FROM records WHERE status='pending' "
                    "ORDER BY source_id LIMIT 1"
                ).fetchone()[0]
            result = await archive.capture(
                client,
                Bounds(
                    max_records=1,
                    max_bytes=available,
                    max_seconds=remaining,
                    max_file_bytes=64 * 1024 * 1024,
                    max_spool_bytes=8589934592,
                ),
            )
            manager.tick()
            if result["failed"]:
                manager.work["bytes"] += manager.work["reserved"]
                manager.work["reserved"] = 0
                manager.save()
                if retry_transport_once(archive, target):
                    manager.save()
                    continue
                manager.work["phase"] = "publish"
                manager.save()
                abort("report_capture_failed")
            if not result["captured"]:
                manager.work["bytes"] += manager.work["reserved"]
                break
    manager.tick()
    manager.work.update(phase="publish", reserved=0)
    manager.save()


def finish(manager: Checkpoints) -> dict[str, Any]:
    """Resolve publication before starting another source attempt."""
    archive = manager.archive
    if archive is None:
        abort("hosted_archive_missing")
    pending = archive.pending_report_batch()
    if pending:
        publication = publish_batch(archive, pending)
    else:
        decisions = archive.report_decisions()
        publication = None
        if decisions:
            batch = archive.package(decisions)
            publication = publish_batch(archive, str(batch["batch"]))
    manager.save()
    result = {
        "cycle": manager.cycle,
        "work": manager.work,
        "publication": publication,
        "summary": archive.summary(),
        "checkpoint": dict(manager.pointer["checkpoint"]),
        "coverage_claim": False,
        "recurrence_acceptance": False,
    }
    # Preserve a final immutable accounting snapshot before clearing this attempt.
    # The receipt references the exact accepted checkpoint and public revision.
    manager.work = None
    manager.cycle += 1
    manager.save()
    manager.retire()
    return result


@contextmanager
def bootstrap_lease(root: Path) -> Iterator[None]:
    """Exclude an in-flight local writer before freezing or exporting its state."""
    root.mkdir(parents=True, exist_ok=True)
    with (root / "writer.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        try:
            file_lock(handle)
        except OSError:
            abort("bootstrap_writer_busy")
        try:
            yield
        finally:
            file_lock(handle, release=True)


def bootstrap(root: Path, index: Path, transport: NativeTransport) -> dict[str, Any]:
    """Hold the existing local writer lock through checkpoint acceptance."""
    with bootstrap_lease(root):
        return _bootstrap(root, index, transport)


def _bootstrap(root: Path, index: Path, transport: NativeTransport) -> dict[str, Any]:
    """Seed only reviewed report references; leave acquisition disabled."""
    manager = Checkpoints(transport, root)
    manager.parent = transport.head()
    if transport.exists(POINTER, manager.parent):
        manager.pointer = manager.current()
        marker = root / "hosted-authority.json"
        if (
            manager.pointer["checkpoint"] is not None
            or manager.pointer["enabled"]
            or manager.pointer["authority"] != "local"
            or not marker.exists()
            or json.loads(marker.read_bytes()).get("bootstrap_owner")
            != manager.pointer["owner"]
        ):
            abort("checkpoint_already_bootstrapped")
        # The first pointer mutation may have succeeded before its response was
        # lost. Recover only that exact frozen bootstrap, never an active owner.
        manager.owner = manager.pointer["owner"]
        manager.archive = ParliamentArchive(root)
        manager.refs = json.loads(index.read_bytes())
        try:
            manager.save()
            return {
                "status": "bootstrap_recovered_disabled",
                "objects": len(manager.refs),
            }
        finally:
            manager.release()
    archive = ParliamentArchive(root)
    if archive.pending_report_batch():
        abort("bootstrap_publication_pending")
    refs = json.loads(index.read_bytes())
    card = digest(transport.read("README.md", manager.parent))
    owner = "bootstrap_" + uuid.uuid4().hex
    manager.pointer = {
        "schema": "parliament-continuation/v1",
        "generation": 0,
        "owner": owner,
        "lease_until": time.time() + 5 * 3600,
        "authority": "local",
        "enabled": False,
        "paused": None,
        "checkpoint": None,
        "card_sha256": card,
    }
    # Freeze the authoritative SSD before creating the shared authority. Never
    # delete this marker automatically on a failed/unknown remote mutation.
    (root / "hosted-authority.json").write_bytes(
        canonical({"authority": "hosted", "bootstrap_owner": owner})
    )
    manager.archive = archive
    manager.refs = refs
    manager.owner = owner
    manager.write_pointer()
    try:
        manager.save()
        return {
            "status": "bootstrapped_disabled",
            "checkpoint": manager.pointer["checkpoint"],
            "records": archive.summary(),
            "objects": len(manager.refs),
        }
    finally:
        manager.release()


def validate_enable_proofs(pilot: str, cancelled: str, restored: str) -> None:
    """Require native cold verification and checkpoint-linked cancellation restore."""
    if len({pilot, cancelled, restored}) != PROOF_RUN_COUNT:
        abort("native_proof_identity")
    values = [github_run(value) for value in (pilot, cancelled, restored)]
    if [value["conclusion"] for value in values] != [
        "success",
        "cancelled",
        "success",
    ] or len({v["head_sha"] for v in values}) != 1:
        abort("native_proof_required")
    branch = subprocess.run(
        ["gh", "api", "repos/edithatogo/archive-govt-nz/branches/main"],  # noqa: S607 - qualified native CLI
        check=True,
        capture_output=True,
        timeout=30,
    )
    if json.loads(branch.stdout)["commit"]["sha"] != values[0]["head_sha"]:
        abort("native_proof_stale_code")
    cold = github_receipt(pilot)
    recovery = github_receipt(restored)
    expected = "gha_" + cancelled + "_" + str(values[1]["run_attempt"])
    if (
        cold.get("status") != "cold_restore_verified"
        or cold.get("objects", 0) <= 0
        or recovery.get("status") != "completed_bounded_invocation"
        or not any(
            row["work"]["interrupted"] and row["work"]["invocation"] == expected
            for row in recovery.get("attempts", [])
        )
    ):
        abort("native_interruption_restore_required")


def run(  # noqa: C901, PLR0912, PLR0913, PLR0915 - finite checkpointed lifecycle
    root: Path,
    *,
    mode: str,
    max_batches: int = 1,
    max_seconds: int = 10800,
    hold_seconds: int = 0,
    transport: NativeTransport | None = None,
) -> dict[str, Any]:
    """Restore, fence and process finite serial attempts; no unrestricted lane."""
    if (
        sys.version_info[:3] != (3, 15, 1)
        or mode not in {"verify", "pilot", "run"}
        or not 1 <= max_batches <= MAX_JOB_BATCHES
        or not 1 <= max_seconds <= MAX_JOB_SECONDS
        or not 0 <= hold_seconds <= MAX_HOLD_SECONDS
    ):
        abort("hosted_invocation_bounds")
    if (mode == "pilot" and max_batches != 1) or (mode != "pilot" and hold_seconds):
        abort("pilot_requires_one_bounded_attempt")
    manager = Checkpoints(transport or NativeTransport(), root)
    if mode == "run":
        head = manager.transport.head()
        if not manager.transport.exists(POINTER, head):
            return {"status": "not_bootstrapped"}
    manager.pointer = manager.current()
    if (manager.pointer["paused"] and mode != "verify") or (
        mode == "run" and not manager.pointer["enabled"]
    ):
        return {
            "status": "paused" if manager.pointer["paused"] else "disabled",
            "checkpoint": manager.pointer["checkpoint"],
        }
    manager.load()
    previous_terminal_owner = manager.pointer["owner"]
    if previous_terminal_owner is not None and not terminal_owner(
        previous_terminal_owner
    ):
        previous_terminal_owner = None
    owner = (
        "gha_"
        + os.environ["GITHUB_RUN_ID"]
        + "_"
        + os.environ.get("GITHUB_RUN_ATTEMPT", "1")
        if os.environ.get("GITHUB_RUN_ID")
        else "local_" + uuid.uuid4().hex
    )
    manager.claim(owner, previous_terminal_owner=previous_terminal_owner)
    results = []
    started = time.monotonic()
    try:
        manager.accept(all_objects=mode == "verify")
        archive = manager.restore()
        manager.hold_seconds = hold_seconds
        if mode == "verify":
            return {
                "status": "cold_restore_verified",
                "objects": len(manager.refs),
                "summary": archive.summary(),
                "checkpoint": manager.pointer["checkpoint"],
            }
        for _ in range(max_batches):
            if time.monotonic() - started > max_seconds:
                break
            manager.guard()
            if manager.pointer["paused"] is not None:
                break
            if (
                digest(manager.transport.read("README.md", manager.parent))
                != manager.pointer["card_sha256"]
            ):
                abort("maintained_card_changed")
            if manager.work is not None:
                results.append(finish(manager))
                continue
            if archive.pending_report_batch():
                publish_batch(archive, str(archive.pending_report_batch()))
            if archive.summary()["failed"]:
                abort("held_failed_reports")
            begin(manager)
            try:
                asyncio.run(acquire(manager))
            except TimeoutError:
                if manager.work is None:
                    abort("hosted_state_missing")
                manager.work["bytes"] += manager.work["reserved"]
                manager.work.update(phase="publish", seconds=900, reserved=0)
                manager.save()
            results.append(finish(manager))
        return {
            "status": "completed_bounded_invocation",
            "attempts": results,
            "checkpoint": manager.pointer["checkpoint"],
            "summary": archive.summary(),
            "execution_kind": os.environ.get("GITHUB_EVENT_NAME", "manual_local"),
        }
    except KeyboardInterrupt:
        # Last acknowledged pointer is authoritative. Never re-save interrupted
        # local state or convert an unknown write outcome to accepted progress.
        raise
    except Exception:  # noqa: BLE001 - persist pause then re-raise every failure
        try:
            manager.pointer = manager.current()
            if manager.pointer["owner"] == owner:
                manager.pointer["paused"] = manager.pointer["paused"] or "failure"
                manager.write_pointer()
        finally:
            raise
    finally:
        manager.release()


def stop_signal(_signum: int, _frame: object) -> None:
    """Treat cancellation as interruption, not successful completion."""
    raise KeyboardInterrupt


def install_signals() -> None:
    """Honor GitHub's ordinary cancellation signals at durable boundaries."""
    signal.signal(signal.SIGINT, stop_signal)
    signal.signal(signal.SIGTERM, stop_signal)
