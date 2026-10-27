"""Validate immutable manifests and exact object-level publication decisions."""

from __future__ import annotations

import json
from importlib.resources import files
from typing import Any
from urllib.parse import urlsplit

from jsonschema import Draft202012Validator, ValidationError

PUBLIC_REPOSITORY = "edithatogo/archive-govt-nz-global"

SCHEMA = json.loads(
    files("archive_govt_nz.parliament")
    .joinpath("batch.schema.json")
    .read_text(encoding="utf-8")
)

SCHEMAS = {
    "parliament-batch/v1": SCHEMA,
    "parliament-batch/v2": json.loads(
        files("archive_govt_nz.parliament")
        .joinpath("batch-v2.schema.json")
        .read_text(encoding="utf-8")
    ),
}


def decision_for(
    decisions: dict[str, dict[str, str]], source_id: str, digest: str
) -> dict[str, str]:
    """Require a nonempty reuse basis and safe evidence URL for the exact hash."""
    decision = decisions.get(source_id + ":" + digest, decisions.get(source_id, {}))
    evidence = decision.get("evidence_url", "")
    url = urlsplit(evidence)
    if (
        decision.get("sha256") != digest
        or not decision.get("basis", "").strip()
        or url.scheme != "https"
        or not url.hostname
        or url.username
        or url.password
        or url.query
        or url.fragment
        or not evidence.isprintable()
    ):
        message = "publication_decision_required"
        raise ValueError(message)
    return decision


def validate_manifest(value: dict[str, Any]) -> None:
    """Reject malformed batches before any native upload can occur."""
    schema = (
        SCHEMAS.get(str(value.get("schema_version", "")))
        if isinstance(value, dict)
        else None
    )
    if schema is None:
        message = "invalid_batch_manifest"
        raise ValueError(message)
    try:
        Draft202012Validator(schema).validate(value)
    except ValidationError:
        message = "invalid_batch_manifest"
        raise ValueError(message) from None
    for row in value["records"]:
        decision_for(value["decisions"], row["source_id"], row["sha256"])


def validate_decisions(value: object) -> None:
    """Reject malformed decisions without logging potentially private text."""
    try:
        Draft202012Validator(
            SCHEMAS["parliament-batch/v2"]["properties"]["decisions"]
        ).validate(value)
    except ValidationError:
        message = "publication_decision_required"
        raise ValueError(message) from None
