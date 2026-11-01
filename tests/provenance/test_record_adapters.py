"""Provenance P2/P3 gap tests - SourceManifest and record adapters."""

import pytest

from archive_govt_nz.core.manifests import SourceManifest
from archive_govt_nz.provenance import (
    ProvenanceError,
    build_receipts_from_records,
    publication_record_to_receipt,
    transformation_record_to_receipt,
    validation_record_to_receipt,
)


def test_source_manifest_accepts_native_web_uri() -> None:
    manifest = SourceManifest(
        source_id="test-1",
        source_uri="web://www.treasury.govt.nz",
        source_type="web",
        agency_slug="treasury",
    )
    assert manifest.source_uri == "web://www.treasury.govt.nz"


def test_source_manifest_rejects_bare_https_uri() -> None:
    with pytest.raises(ValueError, match="unknown native URI scheme"):
        SourceManifest(
            source_id="test-1",
            source_uri="https://www.treasury.govt.nz",
            source_type="web",
            agency_slug="treasury",
        )


def test_source_manifest_rejects_unknown_scheme() -> None:
    with pytest.raises(ValueError, match="unknown native URI scheme"):
        SourceManifest(
            source_id="test-1",
            source_uri="custom://example.com",
            source_type="custom",
            agency_slug="treasury",
        )


def test_source_manifest_rejects_mismatched_scheme() -> None:
    with pytest.raises(ValueError, match="does not match source_type"):
        SourceManifest(
            source_id="test-1",
            source_uri="web://www.treasury.govt.nz",
            source_type="ckan",
            agency_slug="treasury",
        )


def test_transformation_record_to_receipt_valid() -> None:
    record = {
        "receipt_id": "t1",
        "name": "extract_workbook",
        "version": "1",
        "implementation_revision": "abc123",
        "input_object_ids": ["sha256:a"],
        "output_object_ids": ["sha256:b"],
        "parameters": {"sheet": "Sheet1"},
        "environment_sbom_id": "sbom-1",
        "started_at": "2026-10-29T00:00:00Z",
        "ended_at": "2026-10-29T00:01:00Z",
        "information_loss": "none",
        "deterministic": True,
    }
    receipt = transformation_record_to_receipt(record)
    assert receipt["receipt_id"] == "t1"
    assert receipt["name"] == "extract_workbook"
    assert set(receipt.keys()) == set(record.keys())


def test_transformation_record_to_receipt_rejects_incomplete() -> None:
    record = {"receipt_id": "t1", "name": "extract"}
    with pytest.raises(ProvenanceError) as raised:
        transformation_record_to_receipt(record)
    assert raised.value.error_class == "incomplete_transformation_receipt"


def test_transformation_record_to_receipt_rejects_missing_id() -> None:
    record = {
        "receipt_id": "",
        "name": "extract",
        "version": "1",
        "implementation_revision": "abc123",
        "input_object_ids": ["sha256:a"],
        "output_object_ids": ["sha256:b"],
        "parameters": {},
        "environment_sbom_id": "sbom-1",
        "started_at": "2026-10-29T00:00:00Z",
        "ended_at": "2026-10-29T00:01:00Z",
        "information_loss": "none",
        "deterministic": True,
    }
    with pytest.raises(ProvenanceError) as raised:
        transformation_record_to_receipt(record)
    assert raised.value.error_class == "missing_transformation_receipt_id"


def test_validation_record_to_receipt_valid() -> None:
    record = {
        "receipt_id": "v1",
        "validator_name": "cell_parity",
        "validator_version": "1",
        "subject_ids": ["sha256:a", "sha256:b"],
        "checks": ["16 exact year/value pairs"],
        "findings": [],
        "started_at": "2026-10-29T00:00:00Z",
        "ended_at": "2026-10-29T00:01:00Z",
    }
    receipt = validation_record_to_receipt(record)
    assert receipt["receipt_id"] == "v1"
    assert receipt["validator_name"] == "cell_parity"


def test_publication_record_to_receipt_valid() -> None:
    record = {
        "receipt_id": "p1",
        "target": "zenodo",
        "local_version_id": "v1",
        "manifest_sha256": "sha256:abc",
        "requested_at": "2026-10-29T00:00:00Z",
        "remote_identifier": "12345",
        "remote_revision": "rev1",
        "verified_at": "2026-10-29T00:02:00Z",
        "doi": "10.5281/zenodo.12345",
    }
    receipt = publication_record_to_receipt(record)
    assert receipt["receipt_id"] == "p1"
    assert receipt["target"] == "zenodo"
    assert receipt["doi"] == "10.5281/zenodo.12345"


def test_build_receipts_from_records() -> None:
    transformations = [
        {
            "receipt_id": "t1",
            "name": "extract",
            "version": "1",
            "implementation_revision": "abc123",
            "input_object_ids": ["sha256:a"],
            "output_object_ids": ["sha256:b"],
            "parameters": {},
            "environment_sbom_id": "sbom-1",
            "started_at": "2026-10-29T00:00:00Z",
            "ended_at": "2026-10-29T00:01:00Z",
            "information_loss": "none",
            "deterministic": True,
        }
    ]
    validations = [
        {
            "receipt_id": "v1",
            "validator_name": "test",
            "validator_version": "1",
            "subject_ids": ["sha256:b"],
            "checks": ["check"],
            "findings": [],
            "started_at": "2026-10-29T00:00:00Z",
            "ended_at": "2026-10-29T00:01:00Z",
        }
    ]

    receipts = build_receipts_from_records(
        transformations=transformations,
        validations=validations,
        publications=None,
    )
    assert "transformations" in receipts
    assert "validations" in receipts
    assert "publications" not in receipts
    assert receipts["transformations"][0]["receipt_id"] == "t1"
    assert receipts["validations"][0]["receipt_id"] == "v1"
