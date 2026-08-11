"""Health package preparation and rights-gate contracts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

import pytest

from archive_govt_nz.health_package import HealthPackageError, prepare_health_package


def _write_inputs(root: Path, *, authorized: bool = False) -> tuple[Path, Path]:
    resources = root / "resources.json"
    classifications = root / "classifications.json"
    resources.write_text(
        json.dumps(
            {
                "observed_at": "2026-08-02T00:00:00Z",
                "resources": [
                    {
                        "dataset_id": "dataset",
                        "resource_id": "resource",
                        "url": "https://example.test/data.csv",
                        "format": "CSV",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    classifications.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "dataset_id": "dataset",
                        "classification": "eligible"
                        if authorized
                        else "decision-required",
                        "download_authorized": authorized,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return resources, classifications


def test_unknown_resource_rights_create_tombstone_without_capture(
    tmp_path: Path,
) -> None:
    """Dataset metadata cannot silently promote a resource into payload capture."""
    resources, classifications = _write_inputs(tmp_path)
    output = tmp_path / "package"
    manifest = prepare_health_package(resources, classifications, output)
    assert manifest["counts"] == {
        "resources": 1,
        "eligible": 0,
        "rights_restricted": 1,
        "captured": 0,
    }
    assert manifest["payload_transfer"] is False
    assert manifest["publication_authorized"] is False
    tombstone = json.loads((output / "tombstones.jsonl").read_text())
    assert tombstone["state"] == "rights-restricted"


def test_package_is_deterministic_for_identical_evidence(tmp_path: Path) -> None:
    """Repeated preparation yields identical manifests and transformed bytes."""
    resources, classifications = _write_inputs(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    prepare_health_package(resources, classifications, first)
    prepare_health_package(resources, classifications, second)
    for name in (
        "manifest.json",
        "resources.jsonl",
        "resources.parquet",
        "tombstones.jsonl",
    ):
        assert (first / name).read_bytes() == (second / name).read_bytes()


def test_eligible_resource_and_capture_receipt_are_reported(tmp_path: Path) -> None:
    """A resource needs explicit authorization before captured evidence can appear."""
    resources, classifications = _write_inputs(tmp_path, authorized=True)
    output = tmp_path / "package"
    output.mkdir()
    (output / "capture-run.json").write_text(
        json.dumps(
            {
                "payload_transfer": True,
                "results": [{"resource_id": "resource", "state": "captured"}],
            }
        ),
        encoding="utf-8",
    )
    manifest = prepare_health_package(resources, classifications, output)
    assert manifest["counts"] == {
        "resources": 1,
        "eligible": 1,
        "rights_restricted": 0,
        "captured": 1,
    }
    assert manifest["payload_transfer"] is True
    assert (output / "tombstones.jsonl").read_bytes() == b""
    artifacts = cast("list[dict[str, object]]", manifest["artifacts"])
    assert any(artifact["role"] == "capture-receipt" for artifact in artifacts)


def test_missing_dataset_classification_fails_closed(tmp_path: Path) -> None:
    """Every resource must resolve to an explicit classification record."""
    resources, classifications = _write_inputs(tmp_path)
    classifications.write_text('{"records": []}', encoding="utf-8")
    with pytest.raises(HealthPackageError, match="missing_dataset_classification"):
        prepare_health_package(resources, classifications, tmp_path / "package")


@pytest.mark.parametrize(
    ("metadata", "classifications", "error_class"),
    [
        ({}, {"records": []}, "invalid_resource_metadata"),
        ({"resources": []}, {}, "invalid_classification_records"),
        ({"resources": []}, {"records": [None]}, "invalid_classification_record"),
        (
            {"resources": []},
            {"records": [{"dataset_id": "d"}, {"dataset_id": "d"}]},
            "duplicate_dataset_classification",
        ),
        (
            {"resources": [None]},
            {"records": []},
            "invalid_resource_record",
        ),
        (
            {"resources": [{"dataset_id": "d", "resource_id": None}]},
            {"records": [{"dataset_id": "d"}]},
            "invalid_resource_identifier",
        ),
        (
            {
                "resources": [
                    {"dataset_id": "d", "resource_id": "r"},
                    {"dataset_id": "d", "resource_id": "r"},
                ]
            },
            {"records": [{"dataset_id": "d"}]},
            "duplicate_resource",
        ),
    ],
)
def test_malformed_package_evidence_fails_closed(
    tmp_path: Path,
    metadata: object,
    classifications: object,
    error_class: str,
) -> None:
    """Malformed or ambiguous source evidence never produces a package."""
    resources = tmp_path / "resources.json"
    classification_path = tmp_path / "classifications.json"
    resources.write_text(json.dumps(metadata), encoding="utf-8")
    classification_path.write_text(json.dumps(classifications), encoding="utf-8")
    with pytest.raises(HealthPackageError, match=error_class):
        prepare_health_package(resources, classification_path, tmp_path / "package")


@pytest.mark.parametrize("capture_receipt", [[], {"results": "invalid"}])
def test_malformed_capture_receipt_fails_closed(
    tmp_path: Path, capture_receipt: object
) -> None:
    """Capture counts cannot be inferred from a malformed receipt."""
    resources, classifications = _write_inputs(tmp_path)
    output = tmp_path / "package"
    output.mkdir()
    (output / "capture-run.json").write_text(
        json.dumps(capture_receipt), encoding="utf-8"
    )
    with pytest.raises(HealthPackageError, match="invalid_capture"):
        prepare_health_package(resources, classifications, output)


def test_prepared_moh_package_is_closed_and_checksum_pinned() -> None:
    """Committed handoff evidence contains no payload or publication claim."""
    root = Path(__file__).parents[2]
    package = (
        root
        / "conductor/tracks/health_payload_capture_20260802/evidence/prepared-package"
    )
    manifest = json.loads((package / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "prepared-not-published"
    assert manifest["publication_authorized"] is False
    assert manifest["payload_transfer"] is False
    assert manifest["counts"] == {
        "captured": 0,
        "eligible": 0,
        "resources": 158,
        "rights_restricted": 158,
    }
    for artifact in manifest["artifacts"]:
        payload = (package / artifact["path"]).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == artifact["sha256"]
