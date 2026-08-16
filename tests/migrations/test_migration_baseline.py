"""Test suite for migration baseline and schema validation."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent.parent


def test_migration_baseline_manifest_conforms_to_schema() -> None:
    """Validate conductor/migrations/sm-govt-nz.json against its schema."""
    schema_path = REPOSITORY_ROOT / "schemas/archive/v1/migration-baseline.schema.json"
    manifest_path = REPOSITORY_ROOT / "conductor/migrations/sm-govt-nz.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    jsonschema.validate(instance=manifest, schema=schema)
    assert manifest["migration_id"] == "sm-govt-nz-to-archive-govt-nz-20260817"
    assert manifest["donor"]["package_name"] == "sm-govt-nz"
    assert manifest["target"]["package_name"] == "archive-govt-nz"


def test_migration_baseline_evidence_conforms_to_schema() -> None:
    """Validate evidence/migrations/sm-govt-nz/baseline.json against its schema."""
    schema_path = (
        REPOSITORY_ROOT / "schemas/archive/v1/migration-baseline-evidence.schema.json"
    )
    evidence_path = REPOSITORY_ROOT / "evidence/migrations/sm-govt-nz/baseline.json"

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))

    jsonschema.validate(instance=evidence, schema=schema)
    assert evidence["status"] == "frozen_baseline"
    assert evidence["donor_statistics"]["workflow_count"] == 66
    assert len(evidence["donor_workflows"]) >= 10
