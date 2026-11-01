"""P3.1: Independent closure and failure tests for native provenance."""

import copy

import pytest

from archive_govt_nz.provenance import ProvenanceError, build_manifest


def _base() -> dict:
    return {
        "archive_id": "test-archive",
        "observations": [{"observation_id": "o1"}],
        "objects": [{"object_id": "sha256:a"}],
        "versions": [{"version_id": "v1", "observation_id": "o1"}],
    }


def test_cycle_in_version_observation_rejected() -> None:
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="test",
            observations=[{"observation_id": "o1"}],
            objects=[{"object_id": "sha256:a"}],
            versions=[{"version_id": "v1", "observation_id": "v1"}],
        )
    assert raised.value.error_class == "dangling_observation"


def test_corrupt_source_object_rejected() -> None:
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="test",
            observations=[{"observation_id": "o1"}],
            objects=[{"object_id": "sha256:a"}],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
            derivatives=[
                {
                    "derivative_id": "d1",
                    "source_object_id": "sha256:corrupt",
                    "version_id": "v1",
                },
            ],
        )
    assert raised.value.error_class == "dangling_source_object"


def test_swapped_source_object_rejected() -> None:
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="test",
            observations=[{"observation_id": "o1"}],
            objects=[{"object_id": "sha256:a"}, {"object_id": "sha256:b"}],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
            derivatives=[
                {
                    "derivative_id": "d1",
                    "source_object_id": "sha256:nonexistent",
                    "version_id": "v1",
                },
            ],
        )
    assert raised.value.error_class == "dangling_source_object"


def test_multi_parent_derivation() -> None:
    manifest = build_manifest(
        archive_id="test",
        observations=[{"observation_id": "o1"}],
        objects=[
            {"object_id": "sha256:a"},
            {"object_id": "sha256:b"},
            {"object_id": "sha256:c"},
        ],
        versions=[{"version_id": "v1", "observation_id": "o1"}],
        derivatives=[
            {"derivative_id": "d1", "source_object_id": "sha256:a", "version_id": "v1"},
            {"derivative_id": "d2", "source_object_id": "sha256:b", "version_id": "v1"},
            {"derivative_id": "d3", "source_object_id": "sha256:c", "version_id": "v1"},
        ],
    )
    assert len(manifest.document["derivatives"]) == 3


def test_immutable_completed_records() -> None:
    kwargs = _base()
    first = build_manifest(**kwargs)
    second = build_manifest(**kwargs)
    assert first.sha256 == second.sha256
    assert first.canonical_json == second.canonical_json


def test_distinct_attempt_ids() -> None:
    kwargs1 = _base()
    kwargs2 = copy.deepcopy(kwargs1)
    kwargs2["archive_id"] = "test-archive-2"
    first = build_manifest(**kwargs1)
    second = build_manifest(**kwargs2)
    assert first.sha256 != second.sha256


def test_premature_qualified_status_prevented() -> None:
    manifest = build_manifest(
        archive_id="test",
        observations=[{"observation_id": "o1"}],
        objects=[{"object_id": "sha256:a"}],
        versions=[{"version_id": "v1", "observation_id": "o1"}],
    )
    assert "native_lineage_qualified" not in manifest.document
    assert "qualified" not in manifest.document


def test_dangling_warc_object_rejected() -> None:
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="test",
            observations=[{"observation_id": "o1"}],
            objects=[{"object_id": "sha256:a"}],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
            warc_records=[{"record_id": "w1", "object_id": "missing"}],
        )
    assert raised.value.error_class == "dangling_warc_object"


def test_unknown_receipt_type_rejected() -> None:
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="test",
            observations=[{"observation_id": "o1"}],
            objects=[{"object_id": "sha256:a"}],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
            receipts={"unknown_type": [{"receipt_id": "x"}]},
        )
    assert raised.value.error_class == "unknown_receipt_type"


def test_validation_receipt_missing_fields_rejected() -> None:
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="test",
            observations=[{"observation_id": "o1"}],
            objects=[{"object_id": "sha256:a"}],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
            receipts={"validations": [{"receipt_id": "only-an-id"}]},
        )
    assert raised.value.error_class == "incomplete_validation_receipt"


def test_publication_receipt_missing_fields_rejected() -> None:
    with pytest.raises(ProvenanceError) as raised:
        build_manifest(
            archive_id="test",
            observations=[{"observation_id": "o1"}],
            objects=[{"object_id": "sha256:a"}],
            versions=[{"version_id": "v1", "observation_id": "o1"}],
            receipts={"publications": [{"receipt_id": "only-an-id"}]},
        )
    assert raised.value.error_class == "incomplete_publication_receipt"
