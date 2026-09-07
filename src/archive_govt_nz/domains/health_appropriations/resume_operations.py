"""Thin local CLI and read-only MCP boundaries for existing resume contracts."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations.rebuild import PROFILES
from archive_govt_nz.domains.health_appropriations.rebuild_resume import plan_resume
from archive_govt_nz.domains.health_appropriations.resume_execution import (
    execute_resume,
    verify_resume,
)

Operation = Literal["plan-resume", "resume", "verify-resume"]
PATH_FIELDS = frozenset(
    {
        "donor_manifest",
        "previous_run",
        "store_root",
        "resume_plan",
        "output_dir",
        "attempt",
    }
)
FAILURE = {
    "schema_version": "archive-govt-nz.health-resume-operation/v1",
    "status": "failed",
    "error": "invalid_resume_operation",
}
_TEXT = {"type": "string", "minLength": 1, "maxLength": 4096}
_PIN = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_PLAN_FIELDS = {
    "donor_manifest": _TEXT,
    "donor_manifest_sha256": _PIN,
    "previous_run": _TEXT,
    "previous_plan_sha256": _PIN,
    "store_root": _TEXT,
    "observed_at": _TEXT,
    "stage_manifest_sha256": {
        "type": "object",
        "additionalProperties": False,
        "properties": dict.fromkeys(PROFILES, _PIN),
        "maxProperties": len(PROFILES),
    },
}


def _schema(fields: dict[str, Any], optional: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "properties": fields,
        "required": [key for key in fields if key not in optional],
    }


INPUTS = {
    "plan-resume": _schema(_PLAN_FIELDS),
    "resume": _schema(
        {
            **_PLAN_FIELDS,
            "resume_plan": _TEXT,
            "resume_plan_sha256": _PIN,
            "output_dir": _TEXT,
            "dry_run": {"type": "boolean", "default": True},
        },
        ("dry_run",),
    ),
    "verify-resume": _schema(
        {"attempt": _TEXT, "store_root": _TEXT, "receipt_sha256": _PIN}
    ),
}
OUTPUTS = {
    "plan-resume": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": [
            "schema_version",
            "execution",
            "stages",
            "source_plan",
            "rights_state",
        ],
        "properties": {
            "schema_version": {
                "const": "archive-govt-nz.health-readonly-resume-plan/v1"
            },
            "execution": {"const": "not_performed"},
            "rights_state": {"const": "not_evaluated"},
        },
    },
    "verify-resume": {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "required": [
            "schema_version",
            "status",
            "resume_plan_sha256",
            "child_manifest_sha256",
            "actions",
            "rights_state",
            "publication_state",
        ],
        "properties": {
            "schema_version": {"const": "archive-govt-nz.health-exclusive-resume/v1"},
            "status": {"const": "passed"},
            "rights_state": {"const": "not_evaluated"},
            "publication_state": {"const": "local_validation_only"},
        },
    },
}
MCP_OPERATIONS: dict[str, Operation] = {
    "health_appropriations_plan_resume": "plan-resume",
    "health_appropriations_verify_resume": "verify-resume",
}
MCP_TOOLS = tuple(
    {
        "name": name,
        "description": "Read-only pinned resume "
        + operation
        + "; no execution, repair or publication.",
        "inputSchema": INPUTS[operation],
        "outputSchema": OUTPUTS[operation],
        "annotations": {
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    }
    for name, operation in MCP_OPERATIONS.items()
)


def stage_pins(tokens: tuple[str, ...]) -> dict[str, str]:
    """Parse at most four explicit stage=SHA256 pairs without duplicate overwrite."""
    if len(tokens) > len(PROFILES):
        raise ValueError(FAILURE["error"])
    result = {}
    for token in tokens:
        name, separator, digest = token.partition("=")
        if (
            not separator
            or name not in PROFILES
            or name in result
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
        ):
            raise ValueError(FAILURE["error"])
        result[name] = digest
    return result


def invoke(operation: Operation, arguments: dict[str, Any]) -> dict[str, Any]:
    """Validate transport fields; preserve successful native receipts."""
    try:
        Draft202012Validator(INPUTS[operation]).validate(arguments)
        kwargs: dict[str, Any] = {
            key: Path(value) if key in PATH_FIELDS else value
            for key, value in arguments.items()
        }
        if operation == "plan-resume":
            result = plan_resume(**kwargs)
        elif operation == "resume":
            result = execute_resume(**kwargs)
        else:
            result = verify_resume(**kwargs)
        return json.loads(json.dumps(result))
    except Exception:  # noqa: BLE001 - transport errors must not disclose source context.
        return dict(FAILURE)


def mcp_call(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Dispatch only the two immutable read surfaces; there is no MCP executor."""
    operation = MCP_OPERATIONS[name]
    result = invoke(operation, arguments)
    if result.get("status") == "failed":
        raise ValueError(FAILURE["error"])
    return result


def _emit(operation: Operation, arguments: dict[str, Any]) -> int:
    try:
        args: dict[str, Any] = {
            key: str(value) if isinstance(value, Path) else value
            for key, value in arguments.items()
        }
        if "stage_pin" in args:
            args["stage_manifest_sha256"] = stage_pins(args.pop("stage_pin"))
        result = invoke(operation, args)
    except ValueError:
        result = dict(FAILURE)
    print(json.dumps(result, sort_keys=True))  # noqa: T201 - JSON CLI output contract.
    return 2 if result.get("status") == "failed" else 0


def cli_plan(  # noqa: PLR0913 - explicit native identity and provenance fields.
    *,
    donor_manifest: Path,
    donor_manifest_sha256: str,
    previous_run: Path,
    previous_plan_sha256: str,
    store_root: Path,
    observed_at: str,
    stage_pin: tuple[str, ...] = (),
) -> int:
    """Print a read-only native resume plan; repeat --stage-pin stage=SHA256."""
    return _emit("plan-resume", locals())


def cli_resume(  # noqa: PLR0913 - reuse native explicit inputs, no implicit state.
    *,
    donor_manifest: Path,
    donor_manifest_sha256: str,
    previous_run: Path,
    previous_plan_sha256: str,
    store_root: Path,
    observed_at: str,
    resume_plan: Path,
    resume_plan_sha256: str,
    output_dir: Path,
    stage_pin: tuple[str, ...] = (),
    dry_run: bool = True,
) -> int:
    """Preflight pinned resume; --no-dry-run creates one exclusive local attempt."""
    return _emit("resume", locals())


def cli_verify(*, attempt: Path, store_root: Path, receipt_sha256: str) -> int:
    """Verify the saved resume envelope and child; never plan or execute work."""
    return _emit("verify-resume", locals())
