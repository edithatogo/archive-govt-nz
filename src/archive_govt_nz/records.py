"""Strict versioned archive records and canonical JSON serialization."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass
from typing import TYPE_CHECKING, NotRequired, TypedDict, cast

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError, ValidationError

if TYPE_CHECKING:
    from collections.abc import Mapping

type JsonObject = dict[str, object]

RECORD_KINDS = (
    "capability",
    "scope",
    "dataset",
    "resource",
    "attempt",
    "object",
    "version",
    "transformation",
    "validation",
    "publication",
)
_SCHEMA_PREFIX = "archive-govt-nz."
_SCHEMA_SUFFIX = "/v1"
_ERROR_CANONICALIZATION = "canonicalization"
_ERROR_MISSING_SCHEMA_VERSION = "missing_schema_version"
_ERROR_SCHEMA_VALIDATION = "schema_validation"
_ERROR_UNKNOWN_SCHEMA = "unknown_schema"
_DRAFT = "https://json-schema.org/draft/2020-12/schema"
_UTC_TIMESTAMP = {
    "type": "string",
    "format": "date-time",
    "pattern": "Z$",
}
_SHA256 = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
_IDENTIFIER = {"type": "string", "minLength": 1}
_URL = {"type": "string", "format": "uri", "pattern": "^https?://"}
_NULLABLE_IDENTIFIER = {"oneOf": [_IDENTIFIER, {"type": "null"}]}
_NULLABLE_TIMESTAMP = {"oneOf": [_UTC_TIMESTAMP, {"type": "null"}]}
_STRING_ARRAY = {
    "type": "array",
    "items": _IDENTIFIER,
    "uniqueItems": True,
}


class ArchiveRecordError(ValueError):
    """A bounded archive record or canonicalization failure."""

    def __init__(self, error_class: str) -> None:
        """Create a stable diagnostic without retaining record payload detail."""
        self.error_class = error_class
        super().__init__(f"Archive record failed: {error_class}")


@dataclass(frozen=True, slots=True)
class RecordHeader:
    """Typed common identity shared by every archive record."""

    schema_version: str
    record_id: str
    observed_at: str
    state: str
    evidence: tuple[JsonObject, ...] = ()


class CommonRecord(TypedDict):
    """Required typed fields shared by persisted archive records."""

    schema_version: str
    record_id: str
    observed_at: str
    state: str
    evidence: list[JsonObject]


class CapabilityRecord(CommonRecord):
    """Typed capability observation input."""

    catalogue_url: str
    action_api_version: str
    ckan_version: str
    site_url: str
    raw_sha256: str
    attempt_ids: list[str]


class ScopeRecord(CommonRecord):
    """Typed organization-filtered scope input."""

    catalogue_url: str
    organization_id: str
    organization_name: str
    dataset_ids: list[str]
    page_sha256: list[str]
    reported_counts: list[int]
    observation_started_at: str
    observation_ended_at: str


class DatasetRecord(CommonRecord):
    """Typed CKAN dataset observation input."""

    dataset_id: str
    name: str
    organization_id: str
    raw_metadata_object_id: str
    source_modified_at: NotRequired[str | None]
    resource_ids: list[str]
    tombstone: bool


class ResourceRecord(CommonRecord):
    """Typed CKAN resource observation input."""

    resource_id: str
    dataset_id: str
    source_url: str
    source_filename: str | None
    declared_format: str | None
    declared_media_type: str | None
    independent_type: NotRequired[str | None]
    declared_bytes: NotRequired[int | None]
    rights_evidence: NotRequired[list[JsonObject]]
    policy_version: str
    disposition: str


class AttemptRecord(CommonRecord):
    """Typed bounded transport attempt input."""

    target_record_id: str
    ordinal: int
    error_class: str | None
    started_at: str
    ended_at: str
    status_code: int | None
    safe_request: JsonObject
    safe_response: JsonObject
    byte_count: int
    retry_disposition: str
    object_id: str | None


class ObjectRecord(CommonRecord):
    """Typed immutable object input."""

    object_id: str
    sha256: str
    blake3: str
    byte_count: int
    media_type: str
    role: str
    verified_at: str
    source_record_id: str


class VersionRecord(CommonRecord):
    """Typed change-driven archive version input."""

    dataset_id: str
    version_id: str
    comparison_sha256: str
    predecessor_version_id: str | None
    change_reasons: list[str]
    metadata_object_ids: list[str]
    resource_object_ids: list[str]
    policy_version: str
    created_at: str
    tombstone: bool


class TransformationRecord(CommonRecord):
    """Typed transformation provenance input."""

    name: str
    version: str
    implementation_revision: str
    input_object_ids: list[str]
    output_object_ids: list[str]
    parameters: JsonObject
    environment_sbom_id: str
    started_at: str
    ended_at: str
    information_loss: str
    deterministic: bool


class ValidationRecord(CommonRecord):
    """Typed validation evidence input."""

    validator_name: str
    validator_version: str
    subject_ids: list[str]
    checks: list[str]
    findings: list[JsonObject]
    started_at: str
    ended_at: str


class PublicationRecord(CommonRecord):
    """Typed gated external publication input."""

    target: str
    local_version_id: str
    manifest_sha256: str
    requested_at: str
    remote_identifier: str | None
    remote_revision: str | None
    verified_at: str | None
    doi: str | None


type ArchiveRecord = (
    CapabilityRecord
    | ScopeRecord
    | DatasetRecord
    | ResourceRecord
    | AttemptRecord
    | ObjectRecord
    | VersionRecord
    | TransformationRecord
    | ValidationRecord
    | PublicationRecord
)


def _array(items: Mapping[str, object]) -> JsonObject:
    return {"type": "array", "items": dict(items)}


def _nullable(schema: Mapping[str, object]) -> JsonObject:
    return {"oneOf": [dict(schema), {"type": "null"}]}


def _object(
    kind: str,
    states: tuple[str, ...],
    properties: Mapping[str, object],
    required: tuple[str, ...],
    *,
    all_of: list[object] | None = None,
) -> JsonObject:
    common: JsonObject = {
        "schema_version": {"const": f"{_SCHEMA_PREFIX}{kind}{_SCHEMA_SUFFIX}"},
        "record_id": _IDENTIFIER,
        "observed_at": _UTC_TIMESTAMP,
        "state": {"enum": list(states)},
        "evidence": _array({"type": "object"}),
    }
    common.update(properties)
    schema: JsonObject = {
        "$schema": _DRAFT,
        "$id": (
            "https://github.com/edithatogo/archive-govt-nz/"
            f"schemas/archive/v1/{kind}.schema.json"
        ),
        "title": f"Archive Govt NZ {kind} record v1",
        "type": "object",
        "additionalProperties": False,
        "properties": common,
        "required": [
            "schema_version",
            "record_id",
            "observed_at",
            "state",
            "evidence",
            *required,
        ],
    }
    if all_of is not None:
        schema["allOf"] = all_of
    return schema


def _schemas() -> dict[str, JsonObject]:
    safe_map: JsonObject = {
        "type": "object",
        "additionalProperties": {"type": ["string", "integer", "null"]},
    }
    schemas = {
        "capability": _object(
            "capability",
            ("observed", "unavailable", "invalid"),
            {
                "catalogue_url": _URL,
                "action_api_version": _IDENTIFIER,
                "ckan_version": _IDENTIFIER,
                "site_url": _URL,
                "raw_sha256": _SHA256,
                "attempt_ids": _STRING_ARRAY,
            },
            (
                "catalogue_url",
                "action_api_version",
                "ckan_version",
                "site_url",
                "raw_sha256",
                "attempt_ids",
            ),
        ),
        "scope": _object(
            "scope",
            ("reconciled", "drifted", "incomplete"),
            {
                "catalogue_url": _URL,
                "organization_id": _IDENTIFIER,
                "organization_name": _IDENTIFIER,
                "dataset_ids": _STRING_ARRAY,
                "page_sha256": _array(_SHA256),
                "reported_counts": _array({"type": "integer", "minimum": 0}),
                "observation_started_at": _UTC_TIMESTAMP,
                "observation_ended_at": _UTC_TIMESTAMP,
            },
            (
                "catalogue_url",
                "organization_id",
                "organization_name",
                "dataset_ids",
                "page_sha256",
                "reported_counts",
                "observation_started_at",
                "observation_ended_at",
            ),
        ),
        "dataset": _object(
            "dataset",
            ("discovered", "observed", "unavailable", "restricted", "tombstoned"),
            {
                "dataset_id": _IDENTIFIER,
                "name": _IDENTIFIER,
                "organization_id": _IDENTIFIER,
                "raw_metadata_object_id": _IDENTIFIER,
                "source_modified_at": _nullable(_UTC_TIMESTAMP),
                "resource_ids": _STRING_ARRAY,
                "tombstone": {"type": "boolean"},
            },
            (
                "dataset_id",
                "name",
                "organization_id",
                "raw_metadata_object_id",
                "resource_ids",
                "tombstone",
            ),
        ),
        "resource": _object(
            "resource",
            (
                "eligible",
                "unavailable",
                "restricted",
                "oversized",
                "quarantined",
                "retryable",
                "terminal",
            ),
            {
                "resource_id": _IDENTIFIER,
                "dataset_id": _IDENTIFIER,
                "source_url": _URL,
                "source_filename": {"type": ["string", "null"]},
                "declared_format": {"type": ["string", "null"]},
                "declared_media_type": {"type": ["string", "null"]},
                "independent_type": {"type": ["string", "null"]},
                "declared_bytes": {"type": ["integer", "null"], "minimum": 0},
                "rights_evidence": _array({"type": "object"}),
                "policy_version": _IDENTIFIER,
                "disposition": _IDENTIFIER,
            },
            (
                "resource_id",
                "dataset_id",
                "source_url",
                "source_filename",
                "declared_format",
                "declared_media_type",
                "policy_version",
                "disposition",
            ),
        ),
        "attempt": _object(
            "attempt",
            ("succeeded", "retryable", "terminal"),
            {
                "target_record_id": _IDENTIFIER,
                "ordinal": {"type": "integer", "minimum": 1},
                "error_class": {"type": ["string", "null"]},
                "started_at": _UTC_TIMESTAMP,
                "ended_at": _UTC_TIMESTAMP,
                "status_code": {
                    "type": ["integer", "null"],
                    "minimum": 100,
                    "maximum": 599,
                },
                "safe_request": safe_map,
                "safe_response": safe_map,
                "byte_count": {"type": "integer", "minimum": 0},
                "retry_disposition": _IDENTIFIER,
                "object_id": _NULLABLE_IDENTIFIER,
            },
            (
                "target_record_id",
                "ordinal",
                "error_class",
                "started_at",
                "ended_at",
                "status_code",
                "safe_request",
                "safe_response",
                "byte_count",
                "retry_disposition",
                "object_id",
            ),
        ),
        "object": _object(
            "object",
            ("verified", "quarantined"),
            {
                "object_id": _IDENTIFIER,
                "sha256": _SHA256,
                "blake3": _SHA256,
                "byte_count": {"type": "integer", "minimum": 0},
                "media_type": _IDENTIFIER,
                "role": {
                    "enum": [
                        "source_metadata",
                        "source_resource",
                        "warc_receipt",
                        "manifest",
                        "derivative",
                    ]
                },
                "verified_at": _UTC_TIMESTAMP,
                "source_record_id": _IDENTIFIER,
            },
            (
                "object_id",
                "sha256",
                "blake3",
                "byte_count",
                "media_type",
                "role",
                "verified_at",
                "source_record_id",
            ),
        ),
        "version": _object(
            "version",
            ("material", "unchanged_evidence", "tombstone"),
            {
                "dataset_id": _IDENTIFIER,
                "version_id": _IDENTIFIER,
                "comparison_sha256": _SHA256,
                "predecessor_version_id": _NULLABLE_IDENTIFIER,
                "change_reasons": _STRING_ARRAY,
                "metadata_object_ids": _STRING_ARRAY,
                "resource_object_ids": _STRING_ARRAY,
                "policy_version": _IDENTIFIER,
                "created_at": _UTC_TIMESTAMP,
                "tombstone": {"type": "boolean"},
            },
            (
                "dataset_id",
                "version_id",
                "comparison_sha256",
                "predecessor_version_id",
                "change_reasons",
                "metadata_object_ids",
                "resource_object_ids",
                "policy_version",
                "created_at",
                "tombstone",
            ),
        ),
        "transformation": _object(
            "transformation",
            ("succeeded", "failed", "not_applicable"),
            {
                "name": _IDENTIFIER,
                "version": _IDENTIFIER,
                "implementation_revision": _IDENTIFIER,
                "input_object_ids": _STRING_ARRAY,
                "output_object_ids": _STRING_ARRAY,
                "parameters": {"type": "object"},
                "environment_sbom_id": _IDENTIFIER,
                "started_at": _UTC_TIMESTAMP,
                "ended_at": _UTC_TIMESTAMP,
                "information_loss": {"type": "string"},
                "deterministic": {"type": "boolean"},
            },
            (
                "name",
                "version",
                "implementation_revision",
                "input_object_ids",
                "output_object_ids",
                "parameters",
                "environment_sbom_id",
                "started_at",
                "ended_at",
                "information_loss",
                "deterministic",
            ),
        ),
        "validation": _object(
            "validation",
            ("passed", "failed", "partial"),
            {
                "validator_name": _IDENTIFIER,
                "validator_version": _IDENTIFIER,
                "subject_ids": _STRING_ARRAY,
                "checks": _STRING_ARRAY,
                "findings": _array({"type": "object"}),
                "started_at": _UTC_TIMESTAMP,
                "ended_at": _UTC_TIMESTAMP,
            },
            (
                "validator_name",
                "validator_version",
                "subject_ids",
                "checks",
                "findings",
                "started_at",
                "ended_at",
            ),
        ),
    }
    remote_required: JsonObject = {
        "if": {"properties": {"state": {"enum": ["remotely_verified", "released"]}}},
        "then": {
            "properties": {
                "remote_identifier": _IDENTIFIER,
                "remote_revision": _IDENTIFIER,
                "verified_at": _UTC_TIMESTAMP,
            }
        },
    }
    doi_released: JsonObject = {
        "if": {"properties": {"doi": {"type": "string"}}},
        "then": {
            "properties": {
                "state": {"const": "released"},
                "target": {"const": "zenodo"},
            }
        },
    }
    schemas["publication"] = _object(
        "publication",
        ("prepared", "uploaded", "remotely_verified", "released", "failed"),
        {
            "target": {"enum": ["hugging_face", "zenodo"]},
            "local_version_id": _IDENTIFIER,
            "manifest_sha256": _SHA256,
            "requested_at": _UTC_TIMESTAMP,
            "remote_identifier": _NULLABLE_IDENTIFIER,
            "remote_revision": _NULLABLE_IDENTIFIER,
            "verified_at": _NULLABLE_TIMESTAMP,
            "doi": _nullable({"type": "string", "pattern": "^10\\."}),
        },
        (
            "target",
            "local_version_id",
            "manifest_sha256",
            "requested_at",
            "remote_identifier",
            "remote_revision",
            "verified_at",
            "doi",
        ),
        all_of=[remote_required, doi_released],
    )
    return schemas


_ARCHIVE_SCHEMAS = _schemas()


def archive_schema_documents() -> dict[str, JsonObject]:
    """Return defensive copies of every immutable v1 schema document."""
    return deepcopy(_ARCHIVE_SCHEMAS)


def load_archive_schema(kind: str) -> JsonObject:
    """Load one schema by its closed record-kind identifier."""
    schema = _ARCHIVE_SCHEMAS.get(kind)
    if schema is None:
        raise ArchiveRecordError(_ERROR_UNKNOWN_SCHEMA)
    return deepcopy(schema)


def _record_kind(record: Mapping[str, object]) -> str:
    schema_version = record.get("schema_version")
    if not isinstance(schema_version, str):
        raise ArchiveRecordError(_ERROR_MISSING_SCHEMA_VERSION)
    if not schema_version.startswith(_SCHEMA_PREFIX) or not schema_version.endswith(
        _SCHEMA_SUFFIX
    ):
        raise ArchiveRecordError(_ERROR_UNKNOWN_SCHEMA)
    kind = schema_version.removeprefix(_SCHEMA_PREFIX).removesuffix(_SCHEMA_SUFFIX)
    if kind not in RECORD_KINDS:
        raise ArchiveRecordError(_ERROR_UNKNOWN_SCHEMA)
    return kind


def validate_archive_record(record: Mapping[str, object]) -> None:
    """Validate one record without exposing its payload in diagnostics."""
    kind = _record_kind(record)
    schema = _ARCHIVE_SCHEMAS[kind]
    try:
        Draft202012Validator.check_schema(schema)
        Draft202012Validator(  # pyright: ignore[reportUnknownMemberType]
            schema,
            format_checker=FormatChecker(),
        ).validate(record)
    except SchemaError, ValidationError:
        raise ArchiveRecordError(_ERROR_SCHEMA_VALIDATION) from None


def canonical_record_bytes(record: Mapping[str, object]) -> bytes:
    """Validate and serialize one archive record as stable exact JSON bytes."""
    validate_archive_record(record)
    try:
        document = json.dumps(
            cast("object", record),
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except TypeError, ValueError:
        raise ArchiveRecordError(_ERROR_CANONICALIZATION) from None
    return f"{document}\n".encode()
