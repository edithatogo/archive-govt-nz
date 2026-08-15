"""Tests for continuous catalogue drift detection engine."""

from __future__ import annotations

from archive_govt_nz.drift_engine import detect_catalogue_drift, serialize_drift_report


def test_detect_catalogue_drift_stable() -> None:
    """Identical manifests report as stable with zero deltas."""
    manifest = {
        "observed_at": "2026-08-01T00:00:00Z",
        "datasets": [
            {
                "id": "ds-1",
                "metadata_modified": "2026-08-01T00:00:00Z",
                "license_id": "cc-by",
                "resources": [{"id": "res-1"}],
            }
        ],
    }

    report = detect_catalogue_drift(manifest, manifest)
    assert report.is_stable is True
    assert len(report.added_dataset_ids) == 0
    assert len(report.removed_dataset_ids) == 0
    assert len(report.modified_dataset_ids) == 0


def test_detect_catalogue_drift_mutations() -> None:
    """Additions, modifications, and license changes are accurately tracked."""
    prev_manifest = {
        "observed_at": "2026-08-01T00:00:00Z",
        "datasets": [
            {
                "id": "ds-1",
                "metadata_modified": "2026-08-01T00:00:00Z",
                "license_id": "cc-by",
                "resources": [{"id": "res-1"}],
            },
            {
                "id": "ds-old",
                "metadata_modified": "2026-08-01T00:00:00Z",
                "license_id": "cc-by",
                "resources": [{"id": "res-old-1"}],
            },
        ],
    }
    curr_manifest = {
        "observed_at": "2026-08-08T00:00:00Z",
        "datasets": [
            {
                "id": "ds-1",
                "metadata_modified": "2026-08-07T00:00:00Z",
                "license_id": "cc0",
                "resources": [{"id": "res-1"}, {"id": "res-2"}],
            },
            {
                "id": "ds-new",
                "metadata_modified": "2026-08-08T00:00:00Z",
                "license_id": "cc-by",
                "resources": [{"id": "res-new-1"}],
            },
        ],
    }

    report = detect_catalogue_drift(prev_manifest, curr_manifest)
    assert report.is_stable is False
    assert report.added_dataset_ids == ("ds-new",)
    assert report.removed_dataset_ids == ("ds-old",)
    assert report.modified_dataset_ids == ("ds-1",)
    assert report.added_resource_ids == ("res-2", "res-new-1")
    assert report.removed_resource_ids == ("res-old-1",)
    assert len(report.license_mutations) == 1
    assert report.license_mutations[0]["dataset_id"] == "ds-1"

    receipt = serialize_drift_report(report)
    assert receipt["schema_version"] == "archive-govt-nz.catalogue-drift/v1"
    assert receipt["is_stable"] is False
    assert receipt["summary"]["added_datasets_count"] == 1
