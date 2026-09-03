"""Mutation control for distinct batch and execution identities."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[1]


def run_identity_mutant(base: Path) -> int:
    """Restore the invalid equality between batch and hosted execution IDs."""
    source = ROOT / "tools/merge_legislation_states.py"
    target = base / "tools/merge_legislation_states.py"
    text = source.read_text(encoding="utf-8")
    anchor = """        accounting = cast("Any", parsed.accounting)
        if expected_run_identity is not None:
"""
    mutant = """        accounting = cast("Any", parsed.accounting)
        v.equal(accounting.run_identity, manifest["run_id"], "receipt_run")
        if expected_run_identity is not None:
"""
    if text.count(anchor) != 1:
        message = "identity mutation anchor mismatch"
        raise SystemExit(message)
    target.write_text(text.replace(anchor, mutant), encoding="utf-8")
    environment = dict(os.environ)
    environment["PARENT_STATE_UNDER_TEST"] = str(
        base / "tools/legislation_parent_state.py"
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/tools/test_legislation_parent_state.py",
            "-k",
            "persisted_checkpoint_byte_root_seals_end_to_end",
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        timeout=60,
        check=False,
    )
    return result.returncode


def main() -> None:
    """Require both regressions to kill their corresponding mutants."""
    with tempfile.TemporaryDirectory(prefix="legislation-continuation-mutants-") as raw:
        base = Path(raw)
        shutil.copytree(ROOT / "src/archive_govt_nz", base / "src/archive_govt_nz")
        (base / "tools").mkdir()
        for name in (
            "legislation_parent_state.py",
            "merge_legislation_states.py",
            "seed_registry.py",
            "verify_final_donor_state.py",
        ):
            shutil.copy2(ROOT / "tools" / name, base / "tools" / name)
        outcomes = [("conflate_batch_and_execution", run_identity_mutant(base))]
    receipt = {
        "schema_version": (
            "archive-govt-nz.legislation-continuation-integrity-mutation/v1"
        ),
        "mutants": [
            {"name": name, "exit_code": code, "killed": code == 1}
            for name, code in outcomes
        ],
        "killed": sum(code == 1 for _, code in outcomes),
        "total": len(outcomes),
    }
    print(json.dumps(receipt, sort_keys=True))
    if receipt["killed"] != receipt["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
