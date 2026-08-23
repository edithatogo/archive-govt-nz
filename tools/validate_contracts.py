"""Executable validator for migration and quality contracts against schema.

Enforces schema conformance, typed executor registry, and receipt verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("schemas/contracts/v1/contract.schema.json")
CONTRACTS_DIR = Path("contracts")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

TYPED_EXECUTOR_REGISTRY: dict[str, dict[str, Any]] = {
    "pytest_runner": {
        "execution_class": "local_test",
        "side_effect_class": "read_only",
        "allowed_prefixes": ["uv run pytest", "uv run --locked pytest"],
        "max_timeout": 300,
    },
    "contract_validator": {
        "execution_class": "local_read_only",
        "side_effect_class": "read_only",
        "allowed_prefixes": [
            "uv run python tools/validate_contracts.py",
            "uv run --locked python tools/validate_contracts.py",
        ],
        "max_timeout": 60,
    },
    "completion_evaluator": {
        "execution_class": "local_read_only",
        "side_effect_class": "creates_evidence",
        "allowed_prefixes": [
            "uv run python tools/evaluate_legislation_completion.py",
            "uv run --locked python tools/evaluate_legislation_completion.py",
        ],
        "max_timeout": 60,
    },
    "schema_validator": {
        "execution_class": "local_read_only",
        "side_effect_class": "read_only",
        "allowed_prefixes": [
            "uv run python tools/validate_schemas.py",
            "uv run --locked python tools/validate_schemas.py",
        ],
        "max_timeout": 60,
    },
    "timestamp_validator": {
        "execution_class": "local_test",
        "side_effect_class": "read_only",
        "allowed_prefixes": [
            "uv run pytest tests/tools/test_receipt_timestamps.py",
            "uv run --locked pytest tests/tools/test_receipt_timestamps.py",
        ],
        "max_timeout": 60,
    },
    "one_batch_reconciler": {
        "execution_class": "local_generated_evidence",
        "side_effect_class": "creates_evidence",
        "allowed_prefixes": [
            "uv run python tools/reconcile_one_legislation_batch.py",
            "uv run --locked python tools/reconcile_one_legislation_batch.py",
        ],
        "max_timeout": 120,
    },
    "donor_inventory_generator": {
        "execution_class": "local_generated_evidence",
        "side_effect_class": "creates_evidence",
        "allowed_prefixes": [
            "uv run python tools/generate_donor_live_inventory.py",
            "uv run --locked python tools/generate_donor_live_inventory.py",
        ],
        "max_timeout": 120,
    },
    "issue_reconciler": {
        "execution_class": "local_generated_evidence",
        "side_effect_class": "creates_evidence",
        "allowed_prefixes": [
            "uv run python tools/reconcile_legislation_donor_issues.py",
            "uv run --locked python tools/reconcile_legislation_donor_issues.py",
        ],
        "max_timeout": 120,
    },
    "evidence_ledger_generator": {
        "execution_class": "local_generated_evidence",
        "side_effect_class": "creates_evidence",
        "allowed_prefixes": [
            "uv run python tools/generate_evidence_ledger.py",
            "uv run --locked python tools/generate_evidence_ledger.py",
        ],
        "max_timeout": 60,
    },
}


def execute_acceptance_check(
    check: dict[str, Any], root: Path
) -> tuple[bool, dict[str, Any]]:
    """Execute a typed acceptance check and generate a structured execution receipt."""
    ex_id = str(check.get("executor_id"))
    reg = TYPED_EXECUTOR_REGISTRY.get(ex_id)
    if not reg:
        return False, {"error": f"Unknown executor ID: {ex_id}"}

    cmd = check.get("command", "")
    argv = cmd.split() if isinstance(cmd, str) else list(cmd)
    cmd_str = " ".join(argv)

    if not any(cmd_str.startswith(p) for p in reg["allowed_prefixes"]):
        return False, {
            "error": f"Command '{cmd_str}' not allowed for executor '{ex_id}'"
        }

    timeout = int(check.get("timeout_seconds", 30))
    start_ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    t0 = time.time()

    proc = subprocess.run(
        argv,
        cwd=root,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
    elapsed = time.time() - t0
    finish_ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    dest = check.get("evidence_destination")
    dest_hash = None
    if dest:
        dest_file = root / str(dest)
        if dest_file.is_file():
            dest_hash = hashlib.sha256(dest_file.read_bytes()).hexdigest()

    expected_code = int(check.get("expected_exit_code", 0))
    passed = proc.returncode == expected_code

    receipt = {
        "check_id": check.get("check_id"),
        "executor_id": ex_id,
        "argv": argv,
        "working_directory": str(root.resolve()),
        "start_timestamp": start_ts,
        "finish_timestamp": finish_ts,
        "elapsed_seconds": round(elapsed, 3),
        "timeout_seconds": timeout,
        "exit_code": proc.returncode,
        "expected_exit_code": expected_code,
        "passed": passed,
        "stdout_sha256": hashlib.sha256(proc.stdout.encode("utf-8")).hexdigest(),
        "stderr_sha256": hashlib.sha256(proc.stderr.encode("utf-8")).hexdigest(),
        "evidence_destination": dest,
        "evidence_sha256": dest_hash,
    }
    return passed, receipt


def _validate_acceptance_checks(
    checks: object, filepath: Path, root: Path
) -> list[str]:
    """Validate acceptance checks list against executor registry and evidence paths."""
    errors: list[str] = []
    if not isinstance(checks, list):
        return errors

    for idx, check in enumerate(checks, 1):
        if not isinstance(check, dict):
            continue
        ex_id = check.get("executor_id")
        if not ex_id or ex_id not in TYPED_EXECUTOR_REGISTRY:
            errors.append(
                f"Check #{idx} in {filepath} has unknown or missing executor_id: '{ex_id}'"
            )
            continue

        reg = TYPED_EXECUTOR_REGISTRY[str(ex_id)]
        ex_class = check.get("execution_class")
        if ex_class != reg["execution_class"]:
            errors.append(
                f"Check #{idx} in {filepath} execution_class '{ex_class}' != expected '{reg['execution_class']}'"
            )

        cmd = check.get("command", "")
        cmd_str = " ".join(cmd) if isinstance(cmd, list) else str(cmd).strip()
        if not cmd_str:
            errors.append(
                f"Acceptance check #{idx} in {filepath} missing required command"
            )
        elif not any(cmd_str.startswith(p) for p in reg["allowed_prefixes"]):
            errors.append(
                f"Command '{cmd_str}' in check #{idx} of {filepath} not permitted for executor '{ex_id}'"
            )

        dest = check.get("evidence_destination")
        if dest and not (root / str(dest)).exists():
            errors.append(
                f"Evidence destination '{dest}' in check #{idx} of {filepath} does not exist"
            )

    return errors


def _validate_baseline_and_timestamps(
    data: dict[str, Any], filepath: Path
) -> list[str]:
    """Validate commit hashes and timestamp formats."""
    errors: list[str] = []
    baseline = data.get("baseline")
    if isinstance(baseline, dict):
        tgt = str(baseline.get("audited_target_commit", ""))
        dnr = str(baseline.get("audited_donor_commit", ""))
        if not SHA_PATTERN.match(tgt):
            errors.append(f"Malformed audited_target_commit '{tgt}' in {filepath}")
        if not SHA_PATTERN.match(dnr):
            errors.append(f"Malformed audited_donor_commit '{dnr}' in {filepath}")

    now = datetime.now(UTC) + timedelta(minutes=10)
    for ts_key in ("created_at", "updated_at"):
        if ts_key in data:
            try:
                ts = datetime.fromisoformat(str(data[ts_key]))
                if ts > now:
                    errors.append(f"Future timestamp {data[ts_key]} in {filepath}")
            except ValueError:
                errors.append(
                    f"Invalid ISO timestamp format for {ts_key} in {filepath}"
                )

    return errors


def validate_contract_dict(
    data: dict[str, Any], filepath: Path, repo_root: Path | None = None
) -> list[str]:
    """Validate a loaded contract against JSON Schema, executor registry, and invariants."""
    root = repo_root or Path()
    errors: list[str] = []

    # 1. JSON Schema validation
    schema_file = root / SCHEMA_PATH
    if schema_file.is_file():
        try:
            schema = json.loads(schema_file.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            validator = Draft202012Validator(schema)
            for err in validator.iter_errors(data):
                errors.append(f"Schema violation in {filepath}: {err.message}")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Failed to load or execute JSON Schema: {exc}")

    # 2. Track reference check
    owning_track = data.get("owning_track")
    if (
        owning_track
        and not (root / "conductor" / "tracks" / str(owning_track)).is_dir()
        and not (root / "conductor" / "archive" / str(owning_track)).is_dir()
    ):
        errors.append(
            f"Invalid track reference '{owning_track}' in {filepath}: directory does not exist in tracks or archive"
        )

    # 3. Acceptance checks validation
    errors.extend(
        _validate_acceptance_checks(data.get("acceptance_checks", []), filepath, root)
    )

    # 4. Baseline and timestamps
    errors.extend(_validate_baseline_and_timestamps(data, filepath))

    # 5. External gates check
    ext_gates = data.get("external_gates", [])
    if ext_gates and data.get("status") in ("enforced", "complete"):
        errors.append(
            f"Contract {filepath} claims status '{data.get('status')}' while external gates remain open: {ext_gates}"
        )

    return errors


def main() -> int:
    """Validate all or specific YAML contracts."""
    parser = argparse.ArgumentParser(
        description="Validate migration contracts with typed checks"
    )
    parser.add_argument(
        "--contract", type=Path, help="Specific contract file to validate"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute local acceptance checks and produce receipts",
    )
    args = parser.parse_args()

    files = [args.contract] if args.contract else sorted(CONTRACTS_DIR.rglob("*.yaml"))
    if not files:
        print("No contracts found to validate.")
        return 1

    seen_ids: set[str] = set()
    all_errors: list[str] = []
    receipts: list[dict[str, Any]] = []

    for f in files:
        if not f.is_file():
            all_errors.append(f"Contract file not found: {f}")
            continue
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                all_errors.append(f"Contract in {f} must be a top-level YAML mapping")
                continue

            cid = str(data.get("contract_id", ""))
            if cid in seen_ids:
                all_errors.append(f"Duplicate contract_id '{cid}' in {f}")
            seen_ids.add(cid)

            errs = validate_contract_dict(data, f)
            all_errors.extend(errs)

            if args.execute and not errs:
                for chk in data.get("acceptance_checks", []):
                    passed, rec = execute_acceptance_check(chk, Path())
                    receipts.append(rec)
                    if not passed:
                        all_errors.append(
                            f"Execution of check '{chk.get('check_id')}' in {f} failed: exit code {rec.get('exit_code')}"
                        )
        except Exception as exc:  # noqa: BLE001
            all_errors.append(f"YAML parse error in {f}: {exc}")

    if all_errors:
        print(f"Contract validation FAILED with {len(all_errors)} errors:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"All {len(files)} contracts VALIDATED successfully (0 errors).")
    if args.execute:
        print(f"Executed {len(receipts)} acceptance checks successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
