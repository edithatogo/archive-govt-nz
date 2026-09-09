"""Fail-closed negative fixtures for the eight structural record-set contracts."""

import json
from copy import deepcopy
from pathlib import Path

import jsonschema
import pytest

from archive_govt_nz.schemas.health_recordset_json import recordset_json_schema
from archive_govt_nz.schemas.health_recordsets import recordset_schema

_ROOT = Path(__file__).resolve().parents[1]
_NEGATIVE = _ROOT / "fixtures" / "health-recordset-negative-fixtures-v1.json"


def _fixture(name: str) -> dict[str, object]:
    row: dict[str, object] = {}
    for field in recordset_schema(name):
        if field.nullable:
            row[field.name] = None
        elif field.name == "source_object_sha256":
            row[field.name] = "a" * 64
        elif field.name == "observed_at":
            row[field.name] = "2026-08-31T00:00:00Z"
        elif field.name == "schema_version":
            row[field.name] = "archive-govt-nz.health-recordsets/v1"
        elif field.name == "domain":
            row[field.name] = "health_appropriations"
        elif field.name == "recordset":
            row[field.name] = name
        else:
            row[field.name] = "fixture"
    return row


@pytest.mark.parametrize(
    "case", json.loads(_NEGATIVE.read_text(encoding="utf-8"))["cases"]
)
def test_negative_fixture_is_rejected(case: dict[str, object]) -> None:
    """Known layout, lineage, unit, identity, and binary mutations fail closed."""
    row = _fixture(str(case["recordset"]))
    mutation = str(case["mutation"])
    field = str(case["field"])
    if mutation == "extra_field":
        row[field] = case["value"]
    elif mutation == "remove_field":
        del row[field]
    else:
        row[field] = case.get("value")
    validator = jsonschema.Draft202012Validator(
        recordset_json_schema(str(case["recordset"]))
    )
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(row)
