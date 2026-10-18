"""Read-only inspection of two closed, hash-pinned native workbook bundles."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import pyarrow as pa
from jsonschema import Draft202012Validator

from archive_govt_nz.domains.health_appropriations import (
    forecast_detail_source_adapter as adapters,
)
from archive_govt_nz.domains.health_appropriations.adapter_dispatch import (
    dispatch_native_bronze,
)
from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
    CompoundAdapterOutput,
)
from archive_govt_nz.domains.health_appropriations.schema_drift import (
    schema_fingerprint,
)
from archive_govt_nz.domains.health_appropriations.workbook_common import (
    encode_json,
    verified_snapshot,
)

if TYPE_CHECKING:
    from archive_govt_nz.domains.health_appropriations.adapter_protocol import (
        NativeProfileContract,
        NativeProfileOutput,
    )

VERSION = "archive-govt-nz.health-native-workbook-inspection/v1"
TOOL_NAME = "health_appropriations_inspect_native_workbook"
_ERROR = "invalid_native_workbook_inspection"
_COMMON = {
    "schema_version": VERSION,
    "read_only": True,
    "observation_scope": "caller_supplied_normalization_context",
    "rights_state": "not_evaluated",
    "canonical_promotion": "not_performed",
    "publication": "not_performed",
}
_DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_TEXT = {"type": "string", "minLength": 1, "maxLength": 4096}
_COUNT = {"type": "integer", "minimum": 0, "maximum": 100000}
_IDS = [s.adapter_id for s in adapters.SOURCES]
_CONTRACTS = tuple(c for s in adapters.SOURCES for c in adapters.profile_contracts(s))


def _closed(properties: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": list(properties),
        "properties": properties,
    }


INPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    **_closed(
        {
            "cas_root": {"type": "string", "minLength": 1, "maxLength": 2048},
            "source_id": {"enum": _IDS},
            "observed_at": {"type": "string", "minLength": 1, "maxLength": 128},
        }
    ),
}
_SELECTION = _closed(
    {
        "schema_version": {"const": "archive-govt-nz.health-adapter-selection/v1"},
        "source_sha256": _DIGEST,
        "declared_media_type": {"const": adapters.MEDIA_TYPE},
        "detected_media_type": {"const": adapters.MEDIA_TYPE},
        "adapter": _closed({"id": {"enum": _IDS}, "version": {"const": "2"}}),
        "status": {"const": "selected"},
        "reason": {"type": "null"},
        "considered_adapter_ids": {
            "type": "array",
            "minItems": 1,
            "maxItems": 1,
            "items": {"enum": _IDS},
        },
        "matched_adapter_ids": {
            "type": "array",
            "minItems": 1,
            "maxItems": 1,
            "items": {"enum": _IDS},
        },
        "receipt_sha256": _DIGEST,
    }
)
_PROFILE = _closed(
    {
        "profile_id": {"enum": [c.profile_id for c in _CONTRACTS]},
        "metadata_schema_version": {
            "enum": sorted({c.metadata_schema_version for c in _CONTRACTS})
        },
        "native_manifest_sha256": _DIGEST,
        "counts": _closed(
            dict.fromkeys(
                ("facts", "lineage", "dispositions", "excluded_sheets"), _COUNT
            )
        ),
        "recordsets": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": _closed(
                {
                    "name": _TEXT,
                    "schema_id": _TEXT,
                    "schema_version": {"const": "v1"},
                    "schema_sha256": _DIGEST,
                    "rows": _COUNT,
                    "output_sha256": _DIGEST,
                }
            ),
        },
        "excluded_sheets": {
            "type": "array",
            "maxItems": 256,
            "items": _closed({"sheet": _TEXT, "reason": _TEXT}),
        },
    }
)
_SOURCE_PROPERTIES = {
    "source_id": {"enum": _IDS},
    "source_object_sha256": _DIGEST,
    "source_vintage": {"enum": [s.source_vintage for s in adapters.SOURCES]},
    "observed_at": INPUT_SCHEMA["properties"]["observed_at"],
    "selection": _SELECTION,
    "native_kind": {"const": "health-native-compound/v1"},
    "profiles": {"type": "array", "maxItems": 2, "items": _PROFILE},
    "source_losses": {
        "type": "array",
        "maxItems": 64,
        "items": _closed(
            {
                "source_coordinate": {
                    "type": "string",
                    "pattern": "^bronze:sha256:[0-9a-f]{64}$",
                },
                "disposition": {"const": "preserved_only"},
                "reason": _TEXT,
            }
        ),
    },
}
OUTPUT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": [*_COMMON, "status"],
    "properties": {
        **{k: {"const": v} for k, v in _COMMON.items()},
        **_SOURCE_PROPERTIES,
        "status": {"enum": ["inspected", "preserved_only", "failed"]},
        "error": {"const": _ERROR},
    },
    "oneOf": [
        {
            "properties": {"status": {"const": "failed"}},
            "required": ["error"],
            "maxProperties": len(_COMMON) + 2,
        },
        {
            "properties": {
                "status": {"const": "inspected"},
                "profiles": {"minItems": 2},
                "source_losses": {"maxItems": 0},
            },
            "required": list(_SOURCE_PROPERTIES),
            "not": {"required": ["error"]},
        },
        {
            "properties": {
                "status": {"const": "preserved_only"},
                "profiles": {"maxItems": 0},
                "source_losses": {"minItems": 1},
            },
            "required": list(_SOURCE_PROPERTIES),
            "not": {"required": ["error"]},
        },
    ],
}
MCP_TOOL = {
    "name": TOOL_NAME,
    "description": (
        "Inspect both reviewed native profiles of one known workbook from local "
        "Bronze CAS. Return bounded schema/count/hash and held-source evidence "
        "without rows, caller paths, output writes, capture or publication."
    ),
    "inputSchema": INPUT_SCHEMA,
    "outputSchema": OUTPUT_SCHEMA,
    "annotations": {
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
}


def _require(condition: object) -> None:
    if not condition:
        raise ValueError(_ERROR)


def _profile(
    profile: NativeProfileOutput, contract: NativeProfileContract
) -> dict[str, Any]:
    hashes = profile.metadata["output_sha256"]
    _require(isinstance(hashes, Mapping))
    hashes = cast("Mapping[str, str]", hashes)
    tables = {r.name: r.table for r in profile.recordsets}
    return {
        "profile_id": profile.profile_id,
        "metadata_schema_version": contract.metadata_schema_version,
        "native_manifest_sha256": hashlib.sha256(
            (encode_json(dict(profile.metadata)) + "\n").encode()
        ).hexdigest(),
        "counts": {
            "facts": tables[contract.facts].num_rows,
            "lineage": tables[contract.lineage].num_rows,
            "dispositions": tables[contract.dispositions].num_rows,
            "excluded_sheets": len(profile.excluded_sheets),
        },
        "recordsets": [
            {
                "name": r.name,
                "schema_id": r.schema_id,
                "schema_version": r.schema_version,
                "schema_sha256": schema_fingerprint(r.table.schema),
                "rows": r.table.num_rows,
                "output_sha256": hashes[r.name],
            }
            for r in profile.recordsets
        ],
        "excluded_sheets": [dict(row) for row in profile.excluded_sheets],
    }


def inspect_native_workbook(
    cas_root: Path, *, source_id: str, observed_at: str
) -> dict[str, Any]:
    """Resolve one known CAS object; return descriptors without creating state."""
    try:
        _require(isinstance(cas_root, Path))
        arguments = {
            "cas_root": str(cas_root),
            "source_id": source_id,
            "observed_at": observed_at,
        }
        _require(not any(Draft202012Validator(INPUT_SCHEMA).iter_errors(arguments)))
        spec = next(s for s in adapters.SOURCES if s.adapter_id == source_id)
        registration = adapters.forecast_detail_source_registration(
            source_locator=spec.source_locator,
            source_vintage=spec.source_vintage,
            observed_at=observed_at,
        )
        _require(".." not in cas_root.parts)
        root = cas_root.absolute()
        source = root / spec.source_sha256[:2] / spec.source_sha256
        _require(
            not any(
                p.is_symlink() or p.is_junction() for p in (source, *source.parents)
            )
        )
        _require(root.is_dir())
        payload = verified_snapshot(
            source, spec.source_sha256, max_bytes=spec.max_bytes
        )
        result = dispatch_native_bronze(
            payload,
            source_sha256=spec.source_sha256,
            media_type=adapters.MEDIA_TYPE,
            registrations=(registration,),
        )
        _require(
            result.selection.status == "selected"
            and result.selection.adapter_id == source_id
            and result.selection.adapter_version == "2"
        )
        packet = result.output
        _require(type(packet) is CompoundAdapterOutput)
        packet = cast("CompoundAdapterOutput", packet)
        profiles = (
            [
                _profile(p, c)
                for p, c in zip(
                    packet.profiles, registration.profile_contracts, strict=True
                )
            ]
            if packet.status == "admitted"
            else []
        )
        response = {
            **_COMMON,
            "status": "inspected" if packet.status == "admitted" else "preserved_only",
            "source_id": source_id,
            "source_object_sha256": spec.source_sha256,
            "source_vintage": spec.source_vintage,
            "observed_at": observed_at,
            "selection": result.selection.to_receipt(),
            "native_kind": packet.kind,
            "profiles": profiles,
            "source_losses": [asdict(row) for row in packet.source_losses],
        }
        _require(not any(Draft202012Validator(OUTPUT_SCHEMA).iter_errors(response)))
    except (
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        StopIteration,
        OSError,
        pa.ArrowException,
    ):
        return {**_COMMON, "status": "failed", "error": _ERROR}
    return response


def mcp_call(arguments: dict[str, Any]) -> dict[str, Any]:
    """Reject extra or malformed MCP arguments before constructing a path."""
    if any(Draft202012Validator(INPUT_SCHEMA).iter_errors(arguments)):
        raise ValueError(_ERROR)
    return inspect_native_workbook(
        Path(arguments["cas_root"]),
        source_id=arguments["source_id"],
        observed_at=arguments["observed_at"],
    )
