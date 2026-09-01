"""Targeted mutation controls for legislation harvest accounting invariants."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "src/archive_govt_nz/domains/legislation/accounting.py"
TEST = "tests/domains/test_legislation_accounting.py"
MUTANTS = (
    (
        "candidate_scope",
        "if self.candidate_works_discovered < self.works_in_scope:",
        "if False:",
        "test_invalid_aggregate_or_identity_is_rejected",
    ),
    (
        "work_count",
        "if len(self.works) != self.works_in_scope:",
        "if len(self.works) == self.works_in_scope:",
        "test_each_terminal_disposition_can_account_for_one_work",
    ),
    (
        "unique_work_ids",
        "if len(set(ids)) != len(ids):",
        "if False:",
        "test_duplicate_work_ids_are_rejected",
    ),
    (
        "disposition_counts",
        "if getattr(self, disposition.value) != observed[disposition]:",
        "if False:",
        "test_invalid_aggregate_or_identity_is_rejected",
    ),
    (
        "attempted_excludes_skips",
        "if self.works_attempted != expected_attempted:",
        "if False:",
        "test_invalid_aggregate_or_identity_is_rejected",
    ),
    (
        "state_monotonic",
        "if self.total_state_records_after < self.total_state_records_before:",
        "if False:",
        "test_invalid_aggregate_or_identity_is_rejected",
    ),
    (
        "cas_monotonic",
        "if self.total_cas_objects_after < self.total_cas_objects_before:",
        "if False:",
        "test_invalid_aggregate_or_identity_is_rejected",
    ),
    (
        "state_delta_requires_preservation",
        "if state_mutation_capable == 0 and state_delta:",
        "if False:",
        "test_no_change_cannot_hide_state_mutation",
    ),
    (
        "preservation_requires_delta",
        "if mutations and state_delta == 0 and cas_delta == 0:",
        "if False:",
        "test_preserved_disposition_requires_observable_delta",
    ),
    (
        "attempt_requires_classification",
        (
            "self.disposition is not WorkDisposition.ALREADY_PROCESSED_SKIPPED\n"
            "            and not self.source_response_classifications"
        ),
        "False",
        "test_attempt_requires_source_classification",
    ),
    (
        "skip_has_no_retries",
        (
            "self.disposition is WorkDisposition.ALREADY_PROCESSED_SKIPPED\n"
            "            and self.retry_count"
        ),
        "False",
        "test_skipped_work_cannot_claim_retries",
    ),
    (
        "no_change_has_no_mutation",
        "self.state_commit_status is StateCommitStatus.NO_CHANGE",
        "self.state_commit_status is StateCommitStatus.COMMITTED",
        "test_each_terminal_disposition_can_account_for_one_work",
    ),
    (
        "computed_counter_fixity",
        "if key in value and _required_int(value, key) != expected:",
        "if False:",
        "test_v3_rejects_tampered_computed_counter",
    ),
)


def run(source: str, test_name: str, mutation: str | None) -> int:
    """Run one accounting mutant in an isolated source tree."""
    with tempfile.TemporaryDirectory(prefix="legislation-accounting-mutant-") as raw:
        base = Path(raw)
        shutil.copytree(ROOT / "src/archive_govt_nz", base / "src/archive_govt_nz")
        if mutation is not None:
            target = base / "src/archive_govt_nz/domains/legislation/accounting.py"
            target.write_text(source, encoding="utf-8")
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(base / "src")
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                f"{TEST}::{test_name}",
            ],
            cwd=ROOT,
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=60,
            check=False,
        )
        return result.returncode


def main() -> None:
    """Kill every declared legislation accounting mutant."""
    source = SOURCE.read_text(encoding="utf-8")
    if run(source, "test_v3_round_trip_and_computed_deltas", None) != 0:
        msg = "legislation accounting mutation baseline failed"
        raise SystemExit(msg)
    outcomes = []
    for name, old, new, test_name in MUTANTS:
        if source.count(old) != 1:
            msg = f"mutation anchor mismatch: {name}"
            raise SystemExit(msg)
        code = run(source.replace(old, new), test_name, name)
        outcomes.append({"name": name, "exit_code": code, "killed": code == 1})
    receipt = {
        "schema_version": "archive-govt-nz.legislation-accounting-mutation/v1",
        "source_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        "mutants": outcomes,
        "killed": sum(item["killed"] for item in outcomes),
        "total": len(outcomes),
    }
    print(json.dumps(receipt, sort_keys=True))
    if receipt["killed"] != receipt["total"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
