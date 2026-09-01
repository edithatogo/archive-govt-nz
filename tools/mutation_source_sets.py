"""Targeted mutation controls for the typed source-set trust boundary."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).parents[1]
SOURCE = ROOT / "src/archive_govt_nz/source_sets.py"
TEST = "tests/test_source_set_contract.py"
MUTANTS = (
    (
        "duplicates",
        "if duplicate:",
        "if False and duplicate:",
        "test_duplicate_key_bad_indentation_and_yaml_boolean_fail",
    ),
    (
        "schema_errors",
        "if errors:",
        "if False and errors:",
        "test_invalid_nested_contracts_fail_before_action",
    ),
    (
        "lane_scope",
        'if execution["lane_type"] != scope["type"]:',
        "if False:",
        "test_invalid_nested_contracts_fail_before_action",
    ),
    (
        "schedule",
        'if schedule["active"] != scheduled:',
        "if False:",
        "test_invalid_nested_contracts_fail_before_action",
    ),
    (
        "enabled",
        'if value["enabled"] != (execution["activation"] == "active"):',
        "if False:",
        "test_legacy_shape_and_remaining_contradictions_fail",
    ),
    (
        "adapters",
        (
            'if not value["enabled"] and '
            'any(item["active"] for item in value["adapters"]):'
        ),
        "if False:",
        "test_legacy_shape_and_remaining_contradictions_fail",
    ),
    (
        "publication",
        'if destinations != publication["external_actions_enabled"]:',
        "if False:",
        "test_publication_external_action_consistency_is_independent",
    ),
    (
        "adapter_name_uniqueness",
        (
            'if len({item["name"] for item in value["adapters"]}) '
            '!= len(value["adapters"]):'
        ),
        "if False:",
        "test_semantic_ambiguity_and_unsupported_activation_fail",
    ),
    (
        "format_capability",
        (
            'if any(item["active"] and item["capability"] != "supported" '
            "for item in formats):"
        ),
        "if False:",
        "test_semantic_ambiguity_and_unsupported_activation_fail",
    ),
    (
        "publication_gates",
        "if destinations != approved_gates:",
        "if False:",
        "test_publication_requires_capability_rights_and_open_gates",
    ),
    (
        "rights",
        'if destinations and value["rights"]["payload_publication"] != "approved":',
        "if False:",
        "test_legacy_shape_and_remaining_contradictions_fail",
    ),
    (
        "concurrency",
        'if serial != (limits["concurrency_semantics"] == "serial"):',
        "if False:",
        "test_invalid_nested_contracts_fail_before_action",
    ),
    (
        "version",
        "if version != V2:",
        "if False:",
        "test_unsupported_version_and_non_regular_input_fail",
    ),
    (
        "migration",
        'if version is None and value.get("name") == "legislation":',
        "if False:",
        "test_known_v1_legislation_migrates_without_activating_publication",
    ),
)


def run(source: str, test_name: str, mutation: str | None) -> int:
    """Run one isolated targeted mutation control."""
    with tempfile.TemporaryDirectory(prefix="source-set-mutant-") as raw:
        base = Path(raw)
        shutil.copytree(ROOT / "src/archive_govt_nz", base / "src/archive_govt_nz")
        (base / "schemas").mkdir()
        shutil.copy(ROOT / "schemas/source-set-v2.schema.json", base / "schemas")
        if mutation is not None:
            (base / "src/archive_govt_nz/source_sets.py").write_text(source)
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(base / "src")
        environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
        result = subprocess.run(
            [
                str(ROOT / ".venv/bin/python"),
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
    """Kill every declared source-set mutant."""
    source = SOURCE.read_text(encoding="utf-8")
    if (
        run(
            source,
            "test_canonical_legislation_is_typed_and_inactive_for_publication",
            None,
        )
        != 0
    ):
        msg = "source-set mutation baseline failed"
        raise SystemExit(msg)
    outcomes = []
    for name, old, new, test_name in MUTANTS:
        if source.count(old) != 1:
            msg = f"mutation anchor mismatch: {name}"
            raise SystemExit(msg)
        code = run(source.replace(old, new), test_name, name)
        outcomes.append({"name": name, "exit_code": code, "killed": code == 1})
    receipt = {
        "schema_version": "archive-govt-nz.source-set-mutation/v1",
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
