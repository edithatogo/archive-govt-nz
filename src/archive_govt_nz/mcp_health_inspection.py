"""Read-only MCP binding for the existing hash-pinned workbook inspector."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations.inspection import inspect_workbook

# Runtime copy of the canonical schema; parity is tested byte-content-wise.
# Repository-root schema paths are not assumed to exist in installed packages.
OUTPUT_SCHEMA = json.loads(r"""{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://archive-govt-nz.org/schemas/health-workbook-inspection-v1.schema.json",
  "title": "Successful read-only workbook inspection",
  "type": "object",
  "additionalProperties": false,
  "required": ["schema_version", "status", "source_sha256", "source_byte_count",
               "inventory", "value_semantics", "previews"],
  "properties": {
    "schema_version": {"const": "archive-govt-nz.health-workbook-inspection/v1"},
    "status": {"const": "inspected"},
    "source_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "source_byte_count": {"type": "integer", "minimum": 1, "maximum": 67108864},
    "value_semantics": {"const": "decoded_preview_not_canonical_facts"},
    "inventory": {
      "type": "object",
      "required": ["schema_version", "kind", "sheets"],
      "properties": {
        "schema_version": {"const": "archive-govt-nz.workbook-inventory/v1"},
        "kind": {"const": "xlsx"},
        "sheets": {"type": "array", "items": {"type": "object",
          "required": ["title"], "properties": {
            "title": {"type": "string", "minLength": 1}}}}
      }
    },
    "previews": {
      "type": "array", "maxItems": 2000,
      "items": {
        "type": "object", "additionalProperties": false,
        "required": ["name", "row_truncated", "column_truncated", "cells"],
        "properties": {
          "name": {"type": "string", "minLength": 1},
          "row_truncated": {"type": "boolean"},
          "column_truncated": {"type": "boolean"},
          "cells": {
            "type": "array", "maxItems": 2000,
            "items": {
              "type": "object", "additionalProperties": false,
              "required": ["coordinate", "data_type", "decoded_value_json"],
              "properties": {
                "coordinate": {"type": "string", "pattern": "^[A-Z]+[1-9][0-9]*$"},
                "data_type": {"type": "string", "minLength": 1},
                "decoded_value_json": {"type": "string", "maxLength": 131072}
              }
            }
          }
        }
      }
    }
  }
}""")
INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["source", "expected_sha256"],
    "properties": {
        "source": {"type": "string", "minLength": 1, "maxLength": 4096},
        "expected_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "sheet": {"type": "string", "minLength": 1, "maxLength": 31},
        "rows": {"type": "integer", "minimum": 0, "maximum": 20, "default": 0},
        "columns": {"type": "integer", "minimum": 1, "maximum": 50, "default": 12},
    },
}


def validate_arguments(arguments: dict[str, Any]) -> None:
    """Reject invalid inputs before opening sources; never disclose their values."""
    invalid = bool(list(Draft202012Validator(INPUT_SCHEMA).iter_errors(arguments)))
    invalid |= any(
        key in arguments and type(arguments[key]) is not int
        for key in ("rows", "columns")
    )
    if invalid:
        message = "invalid_workbook_inspection_arguments"
        raise ValueError(message)


def inspect(arguments: dict[str, Any]) -> dict[str, Any]:
    """Default to inventory only, with previews available solely by explicit request."""
    validate_arguments(arguments)
    result = inspect_workbook(
        Path(arguments["source"]),
        arguments["expected_sha256"],
        sheet=arguments.get("sheet"),
        rows=arguments.get("rows", 0),
        columns=arguments.get("columns", 12),
    )
    return json.loads(json.dumps(result))
