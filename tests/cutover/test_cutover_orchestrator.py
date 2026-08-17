"""Test suite for CutoverOrchestrator and release continuity."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from archive_govt_nz.cutover.orchestrator import CutoverOrchestrator
from archive_govt_nz.cutover.receipts import (
    CutoverPackageItem,
    ReleaseCutoverReceipt,
)

SCHEMA_PATH = Path("schemas/cutover/v1/cutover-receipt.schema.json")


def test_coordinate_release_cutover_success(tmp_path: Path) -> None:
    """Validate full release cutover packaging and receipt generation."""
    f1 = tmp_path / "dataset.parquet"
    f2 = tmp_path / "metadata.json"
    f1.write_bytes(b"data-parquet")
    f2.write_bytes(b"{}")

    receipt = CutoverOrchestrator.coordinate_release_cutover(
        huggingface_repo="edithatogo/corpus-social-media-government-nz",
        zenodo_concept_doi="10.5281/zenodo.20991132",
        package_files=[f1, f2],
    )

    assert receipt.status == "completed"
    assert len(receipt.packages_published) == 3
    assert len(receipt.fixity_root_sha256) == 64
    assert receipt.huggingface_repo == "edithatogo/corpus-social-media-government-nz"


def test_release_cutover_receipt_schema_conformance() -> None:
    """Validate serialized ReleaseCutoverReceipt against JSON schema."""
    item = CutoverPackageItem(
        platform="huggingface",
        identifier="edithatogo/repo:file.parquet",
        sha256="0" * 64,
    )
    receipt = ReleaseCutoverReceipt(
        receipt_id="cutover:test-001",
        executed_at="2026-08-17T00:00:00Z",
        huggingface_repo="edithatogo/repo",
        zenodo_concept_doi="10.5281/zenodo.123",
        fixity_root_sha256="1" * 64,
        packages_published=(item,),
        status="completed",
    )
    data = receipt.to_dict()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
