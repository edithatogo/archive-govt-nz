"""Tests for RO-Crate and BagIt preservation packaging generation."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from archive_govt_nz.preservation import validate_bagit, validate_ro_crate

_SPEC = importlib.util.spec_from_file_location(
    "generate_preservation_packages",
    Path(__file__).parents[1] / "tools" / "generate_preservation_packages.py",
)
assert _SPEC is not None
assert _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
build_bagit_package = _MODULE.build_bagit_package
build_ro_crate_metadata = _MODULE.build_ro_crate_metadata


def test_build_ro_crate_metadata(tmp_path: Path) -> None:
    """RO-Crate metadata conforms to CreativeWork graph structure."""
    scope = {
        "discovered_dataset_count": 1,
        "datasets": [
            {
                "id": "ds-1",
                "name": "ds-1",
                "title": "Dataset 1",
                "organization_title": "Org 1",
                "license_title": "Creative Commons Attribution 4.0",
                "resources": [
                    {
                        "id": "res-1",
                        "name": "Resource 1",
                        "url": "https://example.govt.nz/file1.csv",
                        "format": "CSV",
                        "size": 1024,
                    }
                ],
            }
        ],
    }
    capture_receipt = {
        "successful_captures": [
            {
                "dataset_id": "ds-1",
                "resource_id": "res-1",
                "sha256": "fake-sha256",
                "byte_count": 1024,
            }
        ]
    }
    ro_crate = build_ro_crate_metadata(scope, capture_receipt)
    metadata_file = tmp_path / "ro-crate-metadata.jsonld"
    metadata_file.write_text(json.dumps(ro_crate), encoding="utf-8")

    validation = validate_ro_crate(tmp_path)
    assert validation["valid"] is True
    assert validation["root_declared"] is True


def test_build_bagit_package(tmp_path: Path) -> None:
    """BagIt staging creates valid bagit.txt and payload manifest."""
    bag_dir = tmp_path / "bag"
    data_dir = bag_dir / "data"
    data_dir.mkdir(parents=True)
    sample_file = data_dir / "sample.csv"
    sample_file.write_bytes(b"col1,col2\nval1,val2\n")

    files = [sample_file]
    build_bagit_package(bag_dir, files)

    validation = validate_bagit(bag_dir)
    assert validation["valid"] is True
    assert validation["entries"] == 1
