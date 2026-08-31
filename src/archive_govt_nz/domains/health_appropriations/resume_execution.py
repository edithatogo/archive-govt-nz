"""Exclusive local resumes of the four legacy raw profiles, never in-place repair.

The caller reviews the local filesystem. Ownership is checked at controlled
boundaries, not an atomic sandbox guarantee. A child raw-run completion is
independent of the envelope: a failed envelope leaves a potentially valid child
but never constitutes successful resume completion. No rights are inferred.
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import re
from itertools import islice
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.budget import (
    normalize_budget_workbook,
)
from archive_govt_nz.domains.health_appropriations.forecast import (
    normalize_forecast_workbook,
)
from archive_govt_nz.domains.health_appropriations.historical import (
    normalize_historical_workbook,
)
from archive_govt_nz.domains.health_appropriations.raw_reader import read_verified_run
from archive_govt_nz.domains.health_appropriations.rebuild import (
    PROFILES,
    describe_rebuild_completion,
    verify_rebuild,
)
from archive_govt_nz.domains.health_appropriations.rebuild_resume import (
    MAX_FILE_BYTES,
    MAX_METADATA_BYTES,
    MAX_ROWS,
    plan_resume,
    verify_resume_stages,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    verified_snapshot,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path

SCHEMA = "archive-govt-nz.health-exclusive-resume/v1"
MAX_REUSE_BYTES = 512 * 1024 * 1024


def _require(condition: bool) -> None:  # noqa: FBT001 - internal assertion predicate.
    if not condition:
        msg = "invalid_resume_state"
        raise ValueError(msg)


def _safe(path: Path) -> None:
    _require(not any(p.is_symlink() for p in (path, *path.parents)))


def _pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        _require(key not in result)
        result[key] = value
    return result


def _constant(_value: str) -> None:
    msg = "nonfinite_resume_metadata"
    raise ValueError(msg)


def _json(payload: bytes) -> dict[str, Any]:
    result = json.loads(
        payload,
        object_pairs_hook=_pairs,
        parse_constant=_constant,
        parse_float=_constant,
    )
    _require(isinstance(result, dict))
    return result


def _snapshot(path: Path, pin: str, cap: int) -> bytes:
    _safe(path)
    _require(path.is_file())
    payload = verified_snapshot(path, pin, max_bytes=cap)
    _safe(path)
    return payload


def _fresh(
    path: Path, pin: str, inputs: dict[str, Any]
) -> tuple[dict[str, Any], bytes]:
    payload = _snapshot(path, pin, MAX_METADATA_BYTES)
    plan = _json(payload)
    _require(_encoded(plan) == _encoded(plan_resume(**inputs)))
    _require(_snapshot(path, pin, MAX_METADATA_BYTES) == payload)
    return plan, payload


def _buffers(plan: dict[str, Any], old: Path) -> dict[str, dict[str, bytes]]:
    result = {}
    total = 0
    for name, action in plan["stages"].items():
        if action["action"] == "reuse_verified":
            manifest = _snapshot(
                old / name / "MANIFEST.json",
                action["manifest_sha256"],
                min(MAX_METADATA_BYTES, MAX_REUSE_BYTES - total),
            )
            total += len(manifest)
            stage = {"MANIFEST.json": manifest}
            hashes = _json(manifest)["output_sha256"]
            for filename in PROFILES[name].outputs:
                stage[filename] = _snapshot(
                    old / name / filename,
                    hashes[filename],
                    min(MAX_FILE_BYTES, MAX_REUSE_BYTES - total),
                )
                total += len(stage[filename])
            result[name] = stage
    return result


def _identity(path: Path) -> tuple[int, int]:
    _safe(path)
    _require(path.is_dir())
    state = path.stat()
    return state.st_dev, state.st_ino


def _owned(owners: dict[Path, tuple[int, int]]) -> None:
    for path, identity in owners.items():
        _require(_identity(path) == identity)


def _write(path: Path, payload: bytes, owners: dict[Path, tuple[int, int]]) -> None:
    _owned(owners)
    with path.open("xb") as handle:
        handle.write(payload)
    _owned(owners)


def _encoded(value: object) -> bytes:
    return (encode_json(value) + "\n").encode()


def _destination(output: Path, protected: list[Path]) -> None:
    _safe(output)
    _require(output.parent.is_dir() and not output.exists())
    target = output.resolve()
    for path in protected:
        existing = path.resolve()
        _require(
            not target.is_relative_to(existing) and not existing.is_relative_to(target)
        )


def _extract(
    name: str, run: Path, source_plan: dict[str, Any], store_root: Path
) -> None:
    source = source_plan["sources"][name]
    path = (
        ContentAddressedStore(store_root, create=False).verify(source["object_id"]).path
    )
    context = {
        "expected_sha256": source["sha256"],
        "observed_at": source_plan["observed_at"],
        "source_locator": source["locator"],
        "source_vintage": source["vintage"],
    }
    if name == "budget":
        normalize_budget_workbook(path, run / name, **context)
    elif name == "historical":
        normalize_historical_workbook(path, run / name, **context)
    else:
        normalize_forecast_workbook(path, run / name, profile=name, **context)


def _receipt(plan: dict[str, Any], plan_pin: str, child_pin: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA,
        "status": "passed",
        "resume_plan_sha256": plan_pin,
        "child_manifest_sha256": child_pin,
        "actions": {name: row["action"] for name, row in plan["stages"].items()},
        "verification_scope": "legacy_raw_run_fixity_and_lineage",
        "rights_state": "not_evaluated",
        "publication_state": "local_validation_only",
    }


def _pin(value: object) -> None:
    _require(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None
    )


def _saved_plan(plan: dict[str, Any]) -> None:
    constants = {
        "schema_version": "archive-govt-nz.health-readonly-resume-plan/v1",
        "source_verification_scope": "selected_four_originals_only",
        "execution": "not_performed",
        "verification_scope": "stage_fixity_and_structure_only",
        "semantic_validation": "not_performed",
        "rights_state": "not_evaluated",
    }
    _require(
        set(plan)
        == {
            *constants,
            "donor_manifest_sha256",
            "previous_plan_sha256",
            "stage_manifest_sha256",
            "selected_source_bytes",
            "source_plan",
            "stages",
        }
    )
    _require(all(plan[key] == value for key, value in constants.items()))
    _pin(plan["donor_manifest_sha256"])
    _pin(plan["previous_plan_sha256"])
    _require(
        plan["donor_manifest_sha256"] == plan["source_plan"]["donor_manifest_sha256"]
    )
    _require(set(plan["stage_manifest_sha256"]) <= set(PROFILES))
    for value in plan["stage_manifest_sha256"].values():
        _pin(value)
    _require(set(plan["stages"]) == set(PROFILES))
    for name, stage in plan["stages"].items():
        if stage["action"] == "reuse_verified":
            _require(set(stage) == {"action", "reason", "manifest_sha256", "rows"})
            _require(stage["reason"] == "pinned_structure_verified")
            _pin(stage["manifest_sha256"])
            _require(
                stage["manifest_sha256"] == plan["stage_manifest_sha256"].get(name)
            )
            _require(set(stage["rows"]) == set(PROFILES[name].outputs))
            _require(
                all(
                    type(count) is int and 0 < count <= MAX_ROWS
                    for count in stage["rows"].values()
                )
            )
        else:
            _require(
                set(stage) == {"action", "reason"} and stage["action"] == "reextract"
            )
            _require(
                stage["reason"]
                in {
                    "missing_stage",
                    "unpinned_stage",
                    "incomplete_stage",
                    "invalid_stage_manifest",
                    "stage_not_passed",
                    "invalid_stage_payload",
                }
            )


def _bounded_child(
    run: Path, plan: dict[str, Any], pin: str, store: Path
) -> dict[str, Any]:
    _require(
        {p.name for p in islice(run.iterdir(), len(PROFILES) + 3)}
        == {*PROFILES, "PLAN.json", "MANIFEST.json"}
    )
    child = _json(_snapshot(run / "MANIFEST.json", pin, MAX_METADATA_BYTES))
    checked = verify_resume_stages(run, plan["source_plan"], child["stages"])
    for name, stage in plan["stages"].items():
        if stage["action"] == "reuse_verified":
            _require(_encoded(stage) == _encoded(checked[name]))
    _originals(plan, store)
    return child


def _originals(plan: dict[str, Any], store: Path) -> None:
    total = 0
    for source in plan["source_plan"]["sources"].values():
        path = ContentAddressedStore(store, create=False).get_path(source["object_id"])
        total += len(_snapshot(path, source["sha256"], MAX_FILE_BYTES))
    _require(
        type(plan["selected_source_bytes"]) is int
        and total == plan["selected_source_bytes"]
    )


def _unsealed_stages(run: Path, plan: dict[str, Any], store: Path) -> None:
    _require(
        {p.name for p in islice(run.iterdir(), len(PROFILES) + 2)}
        == {*PROFILES, "PLAN.json"}
    )
    pins = {}
    for name in PROFILES:
        path = run / name / "MANIFEST.json"
        _safe(path)
        with path.open("rb") as handle:
            payload = handle.read(MAX_METADATA_BYTES + 1)
        _require(len(payload) <= MAX_METADATA_BYTES)
        pins[name] = hashlib.sha256(payload).hexdigest()
    verify_resume_stages(run, plan["source_plan"], pins)
    _originals(plan, store)


def verify_resume(
    attempt: Path, store_root: Path, receipt_sha256: str
) -> dict[str, Any]:
    """Verify the pinned envelope and child; do not revisit prior-attempt state.

    The saved plan records the execution-time decision, not present-day old
    source availability or independently approved source semantics.
    """
    try:
        _safe(attempt)
        _require(
            {p.name for p in islice(attempt.iterdir(), 4)}
            == {"RESUME_PLAN.json", "run", "RESUME_RECEIPT.json"}
        )
        payload = _snapshot(
            attempt / "RESUME_RECEIPT.json", receipt_sha256, MAX_METADATA_BYTES
        )
        receipt = _json(payload)
        plan = _json(
            _snapshot(
                attempt / "RESUME_PLAN.json",
                receipt["resume_plan_sha256"],
                MAX_METADATA_BYTES,
            )
        )
        _saved_plan(plan)
        run = attempt / "run"
        _safe(run)
        child = _bounded_child(run, plan, receipt["child_manifest_sha256"], store_root)
        _require(
            child == verify_rebuild(run, store_root, receipt["child_manifest_sha256"])
        )
        source_plan = _json(
            _snapshot(
                run / "PLAN.json",
                hashlib.sha256(_encoded(plan["source_plan"])).hexdigest(),
                MAX_METADATA_BYTES,
            )
        )
        _require(source_plan == plan["source_plan"])
        for name, row in plan["stages"].items():
            if row["action"] == "reuse_verified":
                _require(child["stages"][name] == row["manifest_sha256"])
        read_verified_run(run, store_root, receipt["child_manifest_sha256"])
        _require(
            receipt
            == _receipt(
                plan, receipt["resume_plan_sha256"], receipt["child_manifest_sha256"]
            )
        )
        _require(
            _snapshot(
                attempt / "RESUME_RECEIPT.json", receipt_sha256, MAX_METADATA_BYTES
            )
            == payload
        )
        _snapshot(
            attempt / "RESUME_PLAN.json",
            receipt["resume_plan_sha256"],
            MAX_METADATA_BYTES,
        )
        _require(
            {p.name for p in islice(attempt.iterdir(), 4)}
            == {"RESUME_PLAN.json", "run", "RESUME_RECEIPT.json"}
        )
    except Exception:  # noqa: BLE001 - public read-only redaction boundary.
        msg = "resume_verification_failed"
        raise ValueError(msg) from None
    else:
        return receipt


def _failure(
    output: Path, owners: dict[Path, tuple[int, int]], error: BaseException
) -> None:
    # A failed evidence write must never mask the original error or interrupt.
    with contextlib.suppress(BaseException):
        _write(
            output / "FAILURE.json",
            _encoded(
                {
                    "schema_version": SCHEMA,
                    "status": "failed",
                    "failure_kind": "interrupted"
                    if isinstance(error, (KeyboardInterrupt, SystemExit))
                    else "operation_failed",
                }
            ),
            owners,
        )


def execute_resume(  # noqa: PLR0913 - independently pinned inputs, no implicit globals.
    *,
    donor_manifest: Path,
    donor_manifest_sha256: str,
    previous_run: Path,
    previous_plan_sha256: str,
    store_root: Path,
    observed_at: str,
    stage_manifest_sha256: dict[str, str],
    resume_plan: Path,
    resume_plan_sha256: str,
    output_dir: Path,
    dry_run: bool = True,
) -> dict[str, Any]:
    """Revalidate a pinned plan; only explicit False permits a new local attempt."""
    owners: dict[Path, tuple[int, int]] = {}
    claimed = False
    try:
        _require(type(dry_run) is bool)
        inputs = {
            "donor_manifest": donor_manifest,
            "donor_manifest_sha256": donor_manifest_sha256,
            "previous_run": previous_run,
            "previous_plan_sha256": previous_plan_sha256,
            "store_root": store_root,
            "observed_at": observed_at,
            "stage_manifest_sha256": dict(stage_manifest_sha256),
        }
        plan, payload = _fresh(resume_plan, resume_plan_sha256, inputs)
        _destination(
            output_dir, [donor_manifest, previous_run, store_root, resume_plan]
        )
        buffers = _buffers(plan, previous_run)
        _require(_fresh(resume_plan, resume_plan_sha256, inputs)[0] == plan)
        if dry_run:
            return {
                "schema_version": SCHEMA,
                "status": "planned",
                "execution": "not_performed",
                "resume_plan_sha256": resume_plan_sha256,
            }
        owners[output_dir.parent] = _identity(output_dir.parent)
        output_dir.mkdir()
        owners[output_dir] = _identity(output_dir)
        claimed = True
        _write(output_dir / "RESUME_PLAN.json", payload, owners)
        run = output_dir / "run"
        _owned(owners)
        run.mkdir()
        owners[run] = _identity(run)
        _write(run / "PLAN.json", _encoded(plan["source_plan"]), owners)
        _build_stages(run, plan, store_root, buffers, owners)
        _owned(owners)
        _unsealed_stages(run, plan, store_root)
        child = describe_rebuild_completion(run, store_root, plan["source_plan"])
        _require(_fresh(resume_plan, resume_plan_sha256, inputs)[0] == plan)
        child_bytes = _encoded(child)
        _write(run / "MANIFEST.json", child_bytes, owners)
        child_pin = hashlib.sha256(child_bytes).hexdigest()
        _bounded_child(run, plan, child_pin, store_root)
        read_verified_run(run, store_root, child_pin)
        receipt = _receipt(plan, resume_plan_sha256, child_pin)
        encoded = _encoded(receipt)
        _write(output_dir / "RESUME_RECEIPT.json", encoded, owners)
        result = verify_resume(
            output_dir, store_root, hashlib.sha256(encoded).hexdigest()
        )
        _owned(owners)
    except BaseException as error:
        if claimed:
            _failure(output_dir, owners, error)
        if isinstance(error, (KeyboardInterrupt, SystemExit)):
            raise
        msg = "resume_execution_failed"
        raise ValueError(msg) from None
    else:
        return result


def _build_stages(
    run: Path,
    plan: dict[str, Any],
    store_root: Path,
    buffers: dict[str, dict[str, bytes]],
    owners: dict[Path, tuple[int, int]],
) -> None:
    for name in PROFILES:
        _owned(owners)
        if name in buffers:
            (run / name).mkdir()
            owners[run / name] = _identity(run / name)
            for filename, content in buffers[name].items():
                _write(run / name / filename, content, owners)
        else:
            _extract(name, run, plan["source_plan"], store_root)
            owners[run / name] = _identity(run / name)
        _owned(owners)
