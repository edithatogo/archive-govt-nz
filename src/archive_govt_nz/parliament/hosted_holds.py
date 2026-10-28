"""Trusted-main approval of one exact exclusion, without any Parliament request."""

from __future__ import annotations

import json
import os
import re
import time
from datetime import datetime
from typing import Any
lazy from pathlib import Path

from archive_govt_nz.parliament.hosted import github_receipt, github_run
from archive_govt_nz.parliament.hosted_checkpoint import (
    Checkpoints,
    read_pinned_snapshot,
)
from archive_govt_nz.parliament.hosted_state import digest
from archive_govt_nz.parliament.hosted_transport import NativeTransport, abort
from archive_govt_nz.parliament.report_holds import (
    ACCESS_STATUSES,
    HOLD_EVENT,
    HTTP_FAILURE_EVENT,
    MAX_HOLD_BYTES,
    V1,
    proof_bytes,
    register_hold,
    validate_hold,
)

CLOCK_SKEW = 120


def _row(state: dict[str, Any], source_id: str) -> dict[str, Any]:
    rows = [r for r in state["tables"]["records"] if r["source_id"] == source_id]
    if len(rows) != 1:
        abort("report_hold_source_missing")
    return rows[0]


def _last_failure(state: dict[str, Any], source_id: str) -> dict[str, Any]:
    rows = [
        r
        for r in state["tables"]["events"]
        if r["source_id"] == source_id and r["status"] == "failed"
    ]
    if not rows or rows[-1]["detail"] != "terminal_status":
        abort("report_hold_terminal_failure_required")
    return rows[-1]


def _publication_clear(state: dict[str, Any]) -> None:
    tables = state["tables"]
    if (
        state["work"] is not None
        or state["batches"]
        or any(r["status"] != "verified" for r in tables["publications"])
    ):
        abort("report_hold_requires_publication_recovery")
    statuses = {r["source_id"]: r["status"] for r in tables["records"]}
    members = {
        (r["source_id"], r["sha256"], r["record_sha256"]) for r in tables["members"]
    }
    if any(
        statuses[r["source_id"]] in {"captured", "metadata_only"}
        and (r["source_id"], r["sha256"], r["record_sha256"]) not in members
        for r in tables["observations"]
    ):
        abort("report_hold_requires_publication_recovery")


def _actor() -> str:
    run, attempt = (
        os.environ.get("GITHUB_RUN_ID", ""),
        os.environ.get("GITHUB_RUN_ATTEMPT", ""),
    )
    if os.environ.get("GITHUB_EVENT_NAME") != "workflow_dispatch":
        abort("report_hold_requires_manual_actions")
    info = github_run(run, attempt)
    if (
        info["status"] != "in_progress"
        or info["event"] != "workflow_dispatch"
        or info["head_sha"] != os.environ.get("GITHUB_SHA")
    ):
        abort("report_hold_action_identity")
    return "gha_" + run + "_" + attempt


def _failure_status(
    state: dict[str, Any], sid: str, record: str, url: str
) -> int | None:
    if state["schema"] == V1:
        return None
    rows = [
        r
        for r in state["tables"]["events"]
        if r["source_id"] == sid and r["status"] == HTTP_FAILURE_EVENT
    ]
    if not rows:
        abort("report_hold_http_evidence_missing")
    data = json.loads(rows[-1]["detail"])
    if (
        data["record_sha256"] != digest(record.encode())
        or data["url_sha256"] != digest(url.encode())
        or data["http_status"] not in ACCESS_STATUSES
    ):
        abort("report_hold_http_evidence_unqualified")
    return data["http_status"]


def _qualify_failure(
    manager: Checkpoints,
    source_id: str,
    failed_run: str,
    failure_sha: str,
    failure_revision: str,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    int | None,
]:
    """Bind the latest terminal row to its original native failure, not another run."""
    original = read_pinned_snapshot(manager.transport, failure_revision, failure_sha)
    current, previous = _row(manager.state, source_id), _row(original, source_id)
    if (
        current["status"] != "failed"
        or current["last_error"] != "terminal_status"
        or previous["status"] != "failed"
        or previous["last_error"] != "terminal_status"
        or current["record"] != previous["record"]
    ):
        abort("report_hold_target_changed")
    record = json.loads(current["record"])
    if record["metadata_only"] or len(record["attachments"]) != 1:
        abort("report_hold_requires_one_attachment")
    failure = _last_failure(original, source_id)
    if _last_failure(manager.state, source_id) != failure:
        abort("report_hold_failure_changed")
    work = original["work"]
    match = re.fullmatch(
        r"gha_([0-9]{1,20})_([0-9]{1,10})", work["invocation"] if work else ""
    )
    if not match or match[1] != failed_run or work["phase"] != "publish":
        abort("report_hold_failure_invocation")
    info = github_run(failed_run, match[2])
    receipt = github_receipt(failed_run, match[2])
    if (
        info["status"] != "completed"
        or info["conclusion"] != "failure"
        or receipt.get("status") != "failed"
        or receipt.get("error_class") != "HostedError"
        or receipt.get("operation") not in {"run", "pilot"}
        or receipt.get("reason") != "report_capture_failed"
    ):
        abort("report_hold_native_failure_unqualified")
    started = datetime.fromisoformat(info["run_started_at"]).timestamp()
    ended = datetime.fromisoformat(info["updated_at"]).timestamp()
    if not started - CLOCK_SKEW <= failure["observed"] <= ended + CLOCK_SKEW:
        abort("report_hold_failure_clock")
    status = _failure_status(
        original, source_id, current["record"], record["attachments"][0]
    )
    return original, current, failure, work, info, receipt, status


def _already_qualified(manager: Checkpoints, source_id: str) -> bool:
    """Verify a repeated approval read-only against its fresh pinned proof."""
    for event in manager.state["tables"]["events"]:
        if event["status"] == HOLD_EVENT and event["source_id"] == source_id:
            ref = manager.refs[event["detail"]]
            data = manager.transport.read(ref["path"], ref["revision"])
            if (
                len(data) != ref["size"]
                or len(data) > MAX_HOLD_BYTES
                or digest(data) != event["detail"]
            ):
                abort("report_hold_integrity")
            existing = json.loads(data)
            validate_hold(existing)
            row = _row(manager.state, source_id)
            if (
                row["status"] == "failed"
                and existing["source_id"] == source_id
                and row["last_error"] in {"terminal_status", "reviewed_access_hold"}
                and json.loads(row["record"])["attachments"] == [existing["source_url"]]
            ):
                return True
    return False


def approve_access_hold(  # noqa: PLR0913 - exact immutable evidence identity
    root: Path,
    *,
    source_id: str | None,
    failed_run: str | None,
    failure_sha: str | None,
    failure_revision: str | None,
    transport: NativeTransport | None = None,
) -> dict[str, Any]:
    """Approve one missing-original exclusion; never retry or grant publication."""
    if (
        not source_id
        or not re.fullmatch(r"report-[0-9a-f-]{36}", source_id)
        or not failed_run
        or not re.fullmatch(r"[0-9]{1,20}", failed_run)
        or not failure_sha
        or not re.fullmatch(r"[0-9a-f]{64}", failure_sha)
        or not failure_revision
        or not re.fullmatch(r"[0-9a-f]{40}", failure_revision)
    ):
        abort("report_hold_evidence_required")
    actor = _actor()
    manager = Checkpoints(transport or NativeTransport(), root)
    manager.load()
    if (
        manager.pointer["owner"]
        or manager.pointer["paused"] is None
        or manager.pointer["checkpoint"]["status"] != "verified"
    ):
        abort("report_hold_requires_quiescent_pause")
    _publication_clear(manager.state)
    if _already_qualified(manager, source_id):
        return {
            "status": "report_access_hold_already_qualified",
            "source_acquisition": False,
        }
    original, current, failure, work, info, receipt, status = _qualify_failure(
        manager, source_id, failed_run, failure_sha, failure_revision
    )
    record = json.loads(current["record"])
    observed_checkpoint = dict(manager.pointer["checkpoint"])
    manager.claim(actor, expected_generation=manager.pointer["generation"])
    try:
        if (
            manager.pointer["checkpoint"] != observed_checkpoint
            or manager.pointer["paused"] is None
        ):
            abort("report_hold_control_changed")
        manager.accept()
        archive = manager.restore()
        if (
            digest(manager.transport.read("README.md", manager.parent))
            != manager.pointer["card_sha256"]
        ):
            abort("maintained_card_changed")
        proof = {
            "schema_version": "parliament-report-access-hold/v1",
            "source_id": source_id,
            "record_sha256": digest(current["record"].encode()),
            "source_url": record["attachments"][0],
            "reason": "terminal_http_response_unclassified"
            if status is None
            else "terminal_http_access_unavailable",
            "original_http_status": status,
            "failure_state_schema": original["schema"],
            "native_failure_receipt": {
                key: receipt[key]
                for key in ("status", "operation", "error_class", "reason")
            },
            "native_failure_receipt_canonical_sha256": digest(proof_bytes(receipt)),
            "failure_code_revision": info["head_sha"],
            "failure_snapshot_sha256": failure_sha,
            "failure_snapshot_revision": failure_revision,
            "failing_invocation": work["invocation"],
            "failure_observed": failure["observed"],
            "approval_invocation": actor,
            "approval_observed": time.time(),
            "licence_grant": False,
            "original_publication_grant": False,
            "source_probed_during_approval": False,
            "scope": "single_unchanged_source_url",
        }
        manager.space(2 * MAX_HOLD_BYTES)
        sha = register_hold(archive, proof)
        manager.save()
        return {
            "status": "report_access_hold_qualified",
            "source_id": source_id,
            "proof_sha256": sha,
            "original_http_status": status,
            "source_acquisition": False,
            "source_reprobe": False,
            "original_publication_grant": False,
            "checkpoint": manager.pointer["checkpoint"],
        }
    finally:
        manager.release()
