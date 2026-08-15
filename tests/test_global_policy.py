"""Tests for global CKAN rights and resource policy classification."""

from __future__ import annotations

from archive_govt_nz.global_policy import (
    GlobalResourceClassification,
    classify_dataset_resource,
    classify_global_manifest,
    is_open_license,
)


def test_is_open_license_detection() -> None:
    """Detect standard open licenses common on NZ data.govt.nz."""
    assert (
        is_open_license("cc-by", "Creative Commons Attribution 4.0 International")
        is True
    )
    assert is_open_license("cc-by-4.0", None) is True
    assert is_open_license("cc-zero", "Creative Commons CCZero") is True
    assert (
        is_open_license("nzgoal", "New Zealand Government Open Access Licensing")
        is True
    )
    assert is_open_license("odc-pddl", None) is True
    assert is_open_license("other-pd", "Public Domain") is True

    # Closed or unknown
    assert is_open_license(None, None) is False
    assert is_open_license("other-closed", "All Rights Reserved") is False
    assert is_open_license("notspecified", None) is False
    assert is_open_license("proprietary", "Commercial License") is False


def test_classify_dataset_resource_eligible() -> None:
    """An open HTTPS resource within size limits is classified as eligible."""
    dataset = {
        "id": "ds-1",
        "name": "ds-1",
        "license_id": "cc-by",
        "license_title": "Creative Commons Attribution 4.0",
    }
    resource = {
        "id": "res-1",
        "url": "https://stats.govt.nz/data.csv",
        "format": "CSV",
        "size": 1024 * 1024,
        "license_id": None,
        "datastore_active": False,
    }
    result = classify_dataset_resource(dataset, resource)
    assert result.disposition == GlobalResourceClassification.ELIGIBLE
    assert result.download_authorized is True
    assert result.reason == "open_license_https_within_budget"


def test_classify_dataset_resource_rights_restricted() -> None:
    """A resource with closed or missing license is classified as restricted."""
    dataset = {
        "id": "ds-2",
        "name": "ds-2",
        "license_id": "other-closed",
        "license_title": "All Rights Reserved",
    }
    resource = {
        "id": "res-2",
        "url": "https://agency.govt.nz/restricted.pdf",
        "format": "PDF",
        "size": 2048,
        "license_id": None,
        "datastore_active": False,
    }
    result = classify_dataset_resource(dataset, resource)
    assert result.disposition == GlobalResourceClassification.RIGHTS_RESTRICTED
    assert result.download_authorized is False


def test_classify_dataset_resource_unsafe_scheme() -> None:
    """Insecure HTTP URLs fail closed with unsafe_scheme."""
    dataset = {
        "id": "ds-3",
        "name": "ds-3",
        "license_id": "cc-by",
    }
    resource = {
        "id": "res-3",
        "url": "http://insecure.example.govt.nz/data.csv",
        "format": "CSV",
    }
    result = classify_dataset_resource(dataset, resource)
    assert result.disposition == GlobalResourceClassification.UNSAFE_SCHEME
    assert result.download_authorized is False


def test_classify_global_manifest_aggregates_counts() -> None:
    """Classifying a full manifest produces complete classification receipts."""
    manifest = {
        "schema_version": "archive-govt-nz.global-ckan-scope/v1",
        "discovered_dataset_count": 2,
        "discovered_resource_count": 2,
        "datasets": [
            {
                "id": "ds-1",
                "name": "ds-1",
                "license_id": "cc-by",
                "resources": [
                    {
                        "id": "res-1",
                        "url": "https://agency.govt.nz/file1.csv",
                        "format": "CSV",
                        "size": 500,
                    }
                ],
            },
            {
                "id": "ds-2",
                "name": "ds-2",
                "license_id": None,
                "resources": [
                    {
                        "id": "res-2",
                        "url": "https://agency.govt.nz/file2.csv",
                        "format": "CSV",
                        "size": 500,
                    }
                ],
            },
        ],
    }
    receipt = classify_global_manifest(manifest)
    assert (
        receipt["schema_version"] == "archive-govt-nz.global-rights-classification/v1"
    )
    assert receipt["counts"]["eligible"] == 1
    assert receipt["counts"]["unknown_rights"] == 1
    assert len(receipt["records"]) == 2
