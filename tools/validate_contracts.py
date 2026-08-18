"""Executable validator for migration and quality contracts against schema."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("schemas/contracts/v1/contract.schema.json")
CONTRACTS_DIR = Path("contracts")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

COMMAND_ALLOWLIST_PREFIXES = (
    "uv run python tools/",
    "uv run --locked python tools/",
    "uv run pytest",
    "uv run --locked pytest",
    "true",
    "uv run",
)


def validate_contract_dict(
    data: dict[str, Any], filepath: Path, repo_root: Path | None = None
) -> list[str]:
    """Validate a loaded contract against JSON Schema and domain-specific rules."""
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
    if owning_track:
        track_dir = root / "conductor" / "tracks" / str(owning_track)
        if not track_dir.is_dir():
            errors.append(
                f"Invalid track reference '{owning_track}' in {filepath}: directory does not exist"
            )

    # 3. Evidence destinations check
    checks = data.get("acceptance_checks", [])
    if isinstance(checks, list):
        for idx, check in enumerate(checks, 1):
            if isinstance(check, dict):
                cmd = str(check.get("command", "")).strip()
                if not cmd:
                    errors.append(
                        f"Acceptance check #{idx} in {filepath} missing required command"
                    )
                elif not any(
                    cmd.startswith(prefix) for prefix in COMMAND_ALLOWLIST_PREFIXES
                ):
                    errors.append(
                        f"Command '{cmd}' in check #{idx} of {filepath} outside allowlist"
                    )

                dest = check.get("evidence_destination")
                if dest:
                    dest_path = root / str(dest)
                    if not dest_path.exists():
                        errors.append(
                            f"Evidence destination '{dest}' in check #{idx} of {filepath} does not exist"
                        )

    # 4. SHA checks
    baseline = data.get("baseline")
    if isinstance(baseline, dict):
        tgt = str(baseline.get("audited_target_commit", ""))
        dnr = str(baseline.get("audited_donor_commit", ""))
        if not SHA_PATTERN.match(tgt):
            errors.append(f"Malformed audited_target_commit '{tgt}' in {filepath}")
        if not SHA_PATTERN.match(dnr):
            errors.append(f"Malformed audited_donor_commit '{dnr}' in {filepath}")

    # 5. Chronology check
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

    # 6. External gates check
    ext_gates = data.get("external_gates", [])
    if ext_gates and data.get("status") in ("enforced", "complete"):
        errors.append(
            f"Contract {filepath} claims status '{data.get('status')}' while external gates remain open: {ext_gates}"
        )

    return errors


def main() -> int:
    """Validate all or specific YAML contracts."""
    parser = argparse.ArgumentParser(description="Validate migration contracts")
    parser.add_argument(
        "--contract", type=Path, help="Specific contract file to validate"
    )
    args = parser.parse_args()

    files = [args.contract] if args.contract else sorted(CONTRACTS_DIR.rglob("*.yaml"))
    if not files:
        print("No contracts found to validate.")
        return 1

    seen_ids: set[str] = set()
    all_errors: list[str] = []

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
        except Exception as exc:  # noqa: BLE001
            all_errors.append(f"YAML parse error in {f}: {exc}")

    if all_errors:
        print(f"Contract validation FAILED with {len(all_errors)} errors:")
        for err in all_errors:
            print(f"  - {err}")
        return 1

    print(f"All {len(files)} contracts VALIDATED successfully (0 errors).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
