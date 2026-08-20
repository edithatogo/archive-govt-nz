"""Test suite for capability matrix and interface reconciliation."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent


def test_capability_matrix_conforms_to_schema() -> None:
    """Validate docs/migrations/sm-govt-nz/capability-matrix.json."""
    schema_path = (
        REPOSITORY_ROOT / "schemas/migrations/capability-matrix-v1.schema.json"
    )
    matrix_path = REPOSITORY_ROOT / "docs/migrations/sm-govt-nz/capability-matrix.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))

    jsonschema.validate(instance=matrix, schema=schema)
    assert matrix["schema_version"] == "archive-govt-nz.capability-matrix/v1"
    assert len(matrix["capabilities"]) == 22

    # Check valid dispositions
    valid_dispositions = {
        "target_native_preferred",
        "donor_native_preferred",
        "target_only",
        "donor_only",
        "overlapping_needs_parity_test",
        "complementary",
        "defer",
        "retire",
    }
    for item in matrix["capabilities"]:
        assert item["disposition"] in valid_dispositions
        assert len(item["rationale"]) > 10


def test_operator_documents_match_fail_closed_global_cli() -> None:
    """Reject the superseded PR #150 grammar and operational claims."""
    interface_map_path = REPOSITORY_ROOT / "docs/migrations/sm-govt-nz/interface-map.md"
    assert interface_map_path.is_file()
    content = interface_map_path.read_text(encoding="utf-8")
    assert "archive-govt-nz" in content
    assert "sm-govt-nz" in content
    assert "--format text|json" in content
    assert "--manifest-path" in content
    assert "not_configured" in content
    assert "NO_STATE_OR_FAILED_VERIFICATION" in content
    assert "capture plan" not in content
    assert "search query" not in content
    assert "when `--json` is supplied" not in content

    readme = (REPOSITORY_ROOT / "README.md").read_text(encoding="utf-8")
    assert "remains **unarchived**" in readme
    assert "zero open-issue count" in readme
    assert "deprecatingly archived" not in readme
    assert "350+ Agency Seed Registry" not in readme

    runbook = (REPOSITORY_ROOT / "docs/operations/runbook.md").read_text(
        encoding="utf-8"
    )
    assert "Expected: status=not_configured and exit code 2" in runbook
    assert "Do not trigger the scheduled workflow as a production harvest" in runbook
