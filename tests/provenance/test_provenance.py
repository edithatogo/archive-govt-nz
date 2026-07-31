"""Provenance closure and deterministic serialization contracts."""

from typing import Any

import pytest

from archive_govt_nz.provenance import ProvenanceError, build_manifest


def test_manifest_is_closed_sorted_and_hashed() -> None:
    """Relationships close and equivalent input order yields one receipt."""
    kwargs: dict[str, Any] = {
        "archive_id": "treasury-20260731",
        "observations": [{"observation_id": "o1"}],
        "objects": [{"object_id": "sha256:a"}],
        "versions": [{"version_id": "v1", "observation_id": "o1"}],
        "derivatives": [
            {"derivative_id": "d1", "source_object_id": "sha256:a", "version_id": "v1"}
        ],
    }
    first = build_manifest(**kwargs)
    kwargs["observations"] = list(reversed(kwargs["observations"]))
    second = build_manifest(**kwargs)
    assert first.sha256 == second.sha256
    assert first.canonical_json == second.canonical_json


def test_manifest_rejects_dangling_relationships() -> None:
    """A derivative cannot silently escape the manifest closure."""
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="treasury",
            observations=[],
            objects=[],
            versions=[],
            derivatives=[
                {"derivative_id": "d", "source_object_id": "missing", "version_id": "v"}
            ],
        )
    assert raised.value.error_class == "dangling_source_object"


def test_manifest_rejects_warc_without_captured_object() -> None:
    """A WARC receipt cannot become detached preservation evidence."""
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="treasury",
            observations=[{"observation_id": "o1"}],
            objects=[],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
            warc_records=[{"record_id": "w1", "object_id": "missing"}],
        )
    assert raised.value.error_class == "dangling_warc_object"
