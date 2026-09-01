"""Fail-closed identity and operation contract for Zenodo publication metadata."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

SCHEMA_PATH = (
    Path(__file__).parents[2] / "schemas/zenodo-publication-identity-v1.schema.json"
)


class ZenodoIdentityError(ValueError):
    """Raised when Zenodo identity or publication state is contradictory."""


def _record_id(doi: str) -> str:
    return doi.rsplit(".", maxsplit=1)[-1]


def _validate_operation(operation: dict[str, Any]) -> None:
    kind = operation["kind"]
    if kind == "observe_existing":
        if operation["external_action_authorized"] or operation["approval_reference"]:
            msg = "observation cannot carry publication authority"
            raise ZenodoIdentityError(msg)
        if operation["status"] != "observed_immutable_version":
            msg = "observation cannot claim draft or publication state"
            raise ZenodoIdentityError(msg)
    elif (
        not operation["external_action_authorized"]
        or not operation["approval_reference"]
    ):
        msg = "mutating Zenodo operation requires explicit approval"
        raise ZenodoIdentityError(msg)

    if operation["status"] == "published" and not operation["remote_receipt_path"]:
        msg = "published status requires independent remote receipt"
        raise ZenodoIdentityError(msg)


def validate_zenodo_identity(document: dict[str, Any]) -> None:
    """Validate typed identity, lineage, and non-fabricated operation state."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(document),
        key=lambda error: list(error.path),
    )
    if errors:
        location = ".".join(str(item) for item in errors[0].absolute_path)
        msg = f"Zenodo identity schema violation at {location or 'document'}"
        raise ZenodoIdentityError(msg)

    identity = document["identity"]
    concept_id = _record_id(identity["concept_doi"])
    version_id = _record_id(identity["version_doi"])
    if concept_id == version_id:
        msg = "concept and version DOI must be distinct"
        raise ZenodoIdentityError(msg)
    if concept_id != identity["concept_record_id"]:
        msg = "concept DOI and record ID disagree"
        raise ZenodoIdentityError(msg)
    if version_id != identity["version_record_id"]:
        msg = "version DOI and record ID disagree"
        raise ZenodoIdentityError(msg)

    _validate_operation(document["operation"])
