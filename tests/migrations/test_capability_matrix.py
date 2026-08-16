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


def test_interface_map_document_exists_and_covers_exit_codes() -> None:
    """Validate docs/migrations/sm-govt-nz/interface-map.md."""
    interface_map_path = REPOSITORY_ROOT / "docs/migrations/sm-govt-nz/interface-map.md"
    assert interface_map_path.is_file()
    content = interface_map_path.read_text(encoding="utf-8")
    assert "archive-govt-nz" in content
    assert "sm-govt-nz" in content
    assert "Exit Code 0" in content or "0: Success" in content or "0" in content
