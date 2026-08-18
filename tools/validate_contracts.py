"""Executable validator for migration and quality contracts against schema."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml

SCHEMA_PATH = Path("schemas/contracts/v1/contract.schema.json")
CONTRACTS_DIR = Path("contracts")
SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")


def validate_contract_dict(data: dict[str, Any], filepath: Path) -> list[str]:
    """Validate a loaded contract against required invariants and rules."""
    errors = []
    required_keys = [
        "contract_id",
        "version",
        "status",
        "scope",
        "owning_track",
        "baseline",
        "invariants",
        "preconditions",
        "postconditions",
        "forbidden_actions",
        "acceptance_checks",
        "evidence_paths",
        "created_at",
        "updated_at",
    ]

    for req in required_keys:
        if req not in data:
            errors.append(f"Missing required field '{req}' in {filepath}")

    if "baseline" in data:
        base = data["baseline"]
        if not isinstance(base, dict):
            errors.append(f"'baseline' must be an object in {filepath}")
        else:
            tgt = base.get("audited_target_commit", "")
            dnr = base.get("audited_donor_commit", "")
            if not SHA_PATTERN.match(str(tgt)):
                errors.append(f"Invalid audited_target_commit '{tgt}' in {filepath}")
            if not SHA_PATTERN.match(str(dnr)):
                errors.append(f"Invalid audited_donor_commit '{dnr}' in {filepath}")

    now = datetime.now(UTC) + timedelta(minutes=10)
    for ts_key in ("created_at", "updated_at"):
        if ts_key in data:
            try:
                ts = datetime.fromisoformat(str(data[ts_key]))
                if ts > now:
                    errors.append(f"Future timestamp {data[ts_key]} in {filepath}")
            except ValueError:
                errors.append(f"Invalid ISO timestamp format for {ts_key} in {filepath}")

    if "acceptance_checks" in data and isinstance(data["acceptance_checks"], list):
        for idx, check in enumerate(data["acceptance_checks"], 1):
            if not isinstance(check, dict):
                errors.append(f"acceptance_check #{idx} must be an object in {filepath}")
                continue
            for chk_key in ("check_id", "description", "command", "expected_exit_code"):
                if chk_key not in check:
                    errors.append(f"Check #{idx} missing '{chk_key}' in {filepath}")

    return errors


def main() -> int:
    """Validate all or specific YAML contracts."""
    parser = argparse.ArgumentParser(description="Validate migration contracts")
    parser.add_argument("--contract", type=Path, help="Specific contract file to validate")
    args = parser.parse_args()

    files = [args.contract] if args.contract else sorted(CONTRACTS_DIR.rglob("*.yaml"))
    if not files:
        print("No contracts found to validate.")
        return 1

    seen_ids = set()
    all_errors = []

    for f in files:
        if not f.is_file():
            all_errors.append(f"Contract file not found: {f}")
            continue
        try:
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                all_errors.append(f"Contract in {f} must be a top-level YAML mapping")
                continue

            cid = data.get("contract_id")
            if cid in seen_ids:
                all_errors.append(f"Duplicate contract_id '{cid}' in {f}")
            seen_ids.add(cid)

            errs = validate_contract_dict(data, f)
            all_errors.extend(errs)
        except Exception as exc:
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
