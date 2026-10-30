# SPDX-License-Identifier: Apache-2.0
"""Run a bounded, pinned local normalization schedule plan."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from archive_govt_nz.domains.health_appropriations.scheduled_normalization import (
    run_scheduled_normalization,
)
from archive_govt_nz.domains.health_appropriations.source_layout_operations import (
    _read_pinned,
)
from archive_govt_nz.domains.health_appropriations.source_operations import (
    SOURCE_OPERATION_SCHEMA,
    SourceRequest,
)

_ID = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
_FIELDS = {"id", "source", "profile", "sha256", "vintage", "locator", "observed_at"}
_MAX_PLAN_BYTES = 1024 * 1024
_MAX_JOBS = 32


def run_normalization_plan(
    plan: Path, plan_sha256: str, job_root: Path, *, dry_run: bool = True
) -> dict[str, Any]:
    """Verify one immutable plan, then run independent jobs in stable order."""
    if type(dry_run) is not bool:
        msg = "schedule_arguments_invalid"
        raise ValueError(msg)
    payload, digest = _read_pinned(str(plan), plan_sha256)
    if len(payload) > _MAX_PLAN_BYTES:
        msg = "schedule_plan_size_invalid"
        raise ValueError(msg)
    try:
        document = json.loads(payload)
        if (
            not isinstance(document, dict)
            or set(document) != {"schema_version", "jobs"}
            or document["schema_version"]
            != "archive-govt-nz.health-normalization-schedule/v1"
            or not isinstance(document["jobs"], list)
            or not 0 < len(document["jobs"]) <= _MAX_JOBS
        ):
            msg = "schedule_plan_invalid"
            raise ValueError(msg)
        jobs = document["jobs"]
        if any(
            not isinstance(job, dict)
            or set(job) != _FIELDS
            or not all(isinstance(value, str) and value for value in job.values())
            or not _ID.fullmatch(job["id"])
            for job in jobs
        ):
            msg = "schedule_job_invalid"
            raise ValueError(msg)
        if len({job["id"] for job in jobs}) != len(jobs):
            msg = "schedule_job_duplicate"
            raise ValueError(msg)
    except (json.JSONDecodeError, UnicodeDecodeError, KeyError, TypeError) as error:
        msg = "schedule_plan_invalid"
        raise ValueError(msg) from error

    results = []
    for job in sorted(jobs, key=lambda item: item["id"]):
        request = SourceRequest(
            Path(job["source"]),
            job_root,
            job["profile"],
            job["sha256"],
            job["vintage"],
            job["locator"],
            job["observed_at"],
        )
        try:
            result = run_scheduled_normalization(request, job_root, dry_run=dry_run)
        except ValueError, OSError:
            result = {"status": "failed", "error": "scheduled_normalization_failed"}
        results.append({"id": job["id"], "result": result})
    failed = sum(item["result"]["status"] == "failed" for item in results)
    return {
        "schema_version": "archive-govt-nz.health-normalization-schedule-receipt/v1",
        "plan_sha256": digest,
        "status": "partial" if failed else ("planned" if dry_run else "completed"),
        "jobs": results,
        "job_count": len(results),
        "failed_count": failed,
    }


def render_normalization_report(receipt: dict[str, Any]) -> str:
    """Summarize a local run without copying job IDs, paths or source content."""
    msg = "schedule_report_invalid"
    states = ("dry_run", "written_local", "reused", "failed")
    try:
        jobs = receipt["jobs"]
        counts = dict.fromkeys(states, 0)
        if not isinstance(jobs, list) or not 0 < len(jobs) <= _MAX_JOBS:
            raise ValueError(msg)
        for job in jobs:
            counts[job["result"]["status"]] += 1
        expected = (
            "partial"
            if counts["failed"]
            else ("planned" if counts["dry_run"] == len(jobs) else "completed")
        )
        if (
            receipt["schema_version"]
            != "archive-govt-nz.health-normalization-schedule-receipt/v1"
            or not isinstance(receipt["plan_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", receipt["plan_sha256"])
            or type(receipt["job_count"]) is not int
            or receipt["job_count"] != len(jobs)
            or type(receipt["failed_count"]) is not int
            or receipt["failed_count"] != counts["failed"]
            or receipt["status"] != expected
            or (counts["dry_run"] and (counts["written_local"] or counts["reused"]))
        ):
            raise ValueError(msg)
    except (KeyError, TypeError) as error:
        raise ValueError(msg) from error
    rows = "\n".join(f"| {state} | {counts[state]} |" for state in states)
    return (
        "# Health normalization report\n\n"
        f"Plan SHA-256: {receipt['plan_sha256']}\n\n"
        f"Run state: {expected}\n\n"
        f"Jobs accounted for: {len(jobs)}\n\n"
        "| Local outcome | Jobs |\n| --- | ---: |\n"
        f"{rows}\n\n"
        "Scope: this local execution or preflight receipt only.\n"
        "Reuse checks retained output hashes; it does not independently "
        "authenticate prior execution.\n"
        "Capture: not performed\n"
        "Rights: not evaluated\n"
        "Publication: not performed\n"
        "Scheduled recurrence: not established\n"
    )


def mcp_preflight(arguments: dict[str, Any]) -> dict[str, Any]:
    """Expose the schedule only as a read-only MCP preflight."""
    if set(arguments) != {"plan", "plan_sha256", "job_root"} or not all(
        isinstance(value, str) and value for value in arguments.values()
    ):
        msg = "schedule_arguments_invalid"
        raise ValueError(msg)
    return run_normalization_plan(
        Path(arguments["plan"]), arguments["plan_sha256"], Path(arguments["job_root"])
    )


_DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_RESULT = {
    "oneOf": [
        {
            "type": "object",
            "properties": {
                "status": {"const": "failed"},
                "error": {"const": "scheduled_normalization_failed"},
            },
            "required": ["status", "error"],
            "additionalProperties": False,
        },
        {
            "type": "object",
            "properties": {
                "job_id": _DIGEST,
                "runtime_fingerprint": _DIGEST,
                "status": {"enum": ["dry_run", "failed"]},
                "operation": SOURCE_OPERATION_SCHEMA,
            },
            "required": ["job_id", "runtime_fingerprint", "status", "operation"],
            "additionalProperties": False,
        },
    ]
}
MCP_TOOL = {
    "name": "health_appropriations_preflight_normalization_plan",
    "description": "Preflight a pinned local normalization plan without writing.",
    "annotations": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
    },
    "inputSchema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "plan": {"type": "string", "minLength": 1},
            "plan_sha256": _DIGEST,
            "job_root": {"type": "string", "minLength": 1},
        },
        "required": ["plan", "plan_sha256", "job_root"],
        "additionalProperties": False,
    },
    "outputSchema": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema_version": {
                "const": "archive-govt-nz.health-normalization-schedule-receipt/v1"
            },
            "plan_sha256": _DIGEST,
            "status": {"enum": ["planned", "partial"]},
            "job_count": {"type": "integer", "minimum": 1, "maximum": 32},
            "failed_count": {"type": "integer", "minimum": 0, "maximum": 32},
            "jobs": {
                "type": "array",
                "maxItems": 32,
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "pattern": "^[a-z][a-z0-9_-]{0,63}$"},
                        "result": _RESULT,
                    },
                    "required": ["id", "result"],
                    "additionalProperties": False,
                },
            },
        },
        "required": [
            "schema_version",
            "plan_sha256",
            "status",
            "job_count",
            "failed_count",
            "jobs",
        ],
        "additionalProperties": False,
    },
}
