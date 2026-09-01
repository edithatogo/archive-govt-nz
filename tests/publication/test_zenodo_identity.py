"""Typed Zenodo concept/version and operation-state contract tests."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.zenodo_identity import (
    ZenodoIdentityError,
    validate_zenodo_identity,
)

CONFIG = Path("config/legislation/zenodo-publication.json")


def _config() -> dict[str, Any]:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def test_governed_zenodo_identity_is_valid_and_observation_only() -> None:
    """Accept the exact observed identity without granting remote authority."""
    document = _config()
    validate_zenodo_identity(document)
    assert document["identity"]["concept_doi"] == "10.5281/zenodo.20592539"
    assert document["identity"]["version_doi"] == "10.5281/zenodo.20592540"
    assert document["operation"]["external_action_authorized"] is False


@pytest.mark.parametrize(
    ("path", "value", "match"),
    [
        (("identity", "concept_doi"), "10.5281/zenodo.20592540", "distinct"),
        (("identity", "concept_record_id"), "20592538", "disagree"),
        (("identity", "version_record_id"), "20592541", "disagree"),
        (("operation", "status"), "published", "observation cannot"),
        (("operation", "external_action_authorized"), True, "observation cannot"),
    ],
)
def test_identity_and_observation_contradictions_fail_closed(
    path: tuple[str, str], value: object, match: str
) -> None:
    """Reject swaps, fabricated publication, and observation authority."""
    document = _config()
    document[path[0]][path[1]] = value
    with pytest.raises(ZenodoIdentityError, match=match):
        validate_zenodo_identity(document)


@given(value=st.text().filter(lambda item: not item.startswith("10.5281/zenodo.")))
def test_noncanonical_concept_dois_are_rejected(value: str) -> None:
    """Reject every generated DOI outside the canonical Zenodo namespace."""
    document = _config()
    document["identity"]["concept_doi"] = value
    with pytest.raises(ZenodoIdentityError):
        validate_zenodo_identity(document)


def test_mutating_operation_requires_approval_and_published_receipt() -> None:
    """Require both explicit approval and remote evidence for publication."""
    document = copy.deepcopy(_config())
    document["operation"].update(
        {"kind": "publish_version", "status": "published", "remote_receipt_path": None}
    )
    with pytest.raises(ZenodoIdentityError, match="explicit approval"):
        validate_zenodo_identity(document)
    document["operation"].update(
        {"external_action_authorized": True, "approval_reference": "DEC-ZENODO-001"}
    )
    with pytest.raises(ZenodoIdentityError, match="remote receipt"):
        validate_zenodo_identity(document)
