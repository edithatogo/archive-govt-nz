"""Standalone JSON row-shape descriptors for the additive Arrow contracts.

Decimal values use fixed-point strings, not binary floating-point JSON numbers.
Every column must be present, including nullable columns. Format validation
requires an explicitly enabled JSON Schema format checker. These descriptors
do not validate source identities, rights, time alignment or lineage closure.
"""

from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType
from typing import Any

import pyarrow as pa

from archive_govt_nz.schemas.health_recordsets import recordset_schema

_TYPES = MappingProxyType(
    {
        pa.string(): {"type": "string"},
        pa.date32(): {"type": "string", "format": "date"},
        pa.timestamp("us", tz="UTC"): {"type": "string", "format": "date-time"},
        pa.int16(): {"type": "integer", "minimum": -32768, "maximum": 32767},
        pa.decimal128(38, 18): {
            "type": "string",
            # End assertion is portable to ECMA/Python regex and rejects a
            # final newline, which the ordinary dollar anchor can admit.
            "pattern": r"^-?(?:0|[1-9][0-9]{0,19})(?:\.[0-9]{1,18})?(?![\s\S])",
        },
        pa.list_(pa.field("element", pa.string())): {
            "type": "array",
            "items": {"type": ["string", "null"]},
        },
    }
)


def recordset_json_schema(name: str, *, version: str = "v1") -> dict[str, Any]:
    """Return a fresh descriptor; reject unknown record sets/types/versions.

    The caller enables format checks when validating values. This shape API
    never reads source payloads or writes files, and makes no promotion claim.
    """
    arrow = recordset_schema(name, version=version)
    properties: dict[str, Any] = {}
    for field in arrow:
        typed = deepcopy(_TYPES[field.type])
        properties[field.name] = (
            {"anyOf": [typed, {"type": "null"}]} if field.nullable else typed
        )
    properties["domain"]["const"] = "health_appropriations"
    properties["recordset"]["const"] = name
    properties["schema_version"]["const"] = "archive-govt-nz.health-recordsets/v1"
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"urn:archive-govt-nz:health-recordsets:{version}:{name}",
        "type": "object",
        "description": (
            "Structural row representation only; not semantic source validation."
        ),
        "properties": properties,
        "required": arrow.names,
        "additionalProperties": False,
    }
