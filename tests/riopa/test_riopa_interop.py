"""Test suite for RiopaInteropBridge and cross-corpus export receipts."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from archive_govt_nz.riopa.interop import RiopaInteropBridge
from archive_govt_nz.riopa.receipts import RiopaExportReceipt

SCHEMA_PATH = Path("schemas/riopa/v1/riopa-export-receipt.schema.json")


def test_riopa_generate_export_success() -> None:
    """Validate successful RIOPA export manifest generation."""
    receipt = RiopaInteropBridge.generate_export(
        records_count=500,
        export_formats=("parquet", "jsonld"),
        target_corpus="archive-govt-nz",
    )
    assert receipt.status == "exported"
    assert receipt.boundary_integrity_verified is True
    assert receipt.records_exported == 500
    assert receipt.riopa_spec_version == "v1"


def test_riopa_generate_export_boundary_rejection() -> None:
    """Validate that foreign corpora are strictly rejected for boundary preservation."""
    receipt = RiopaInteropBridge.generate_export(
        records_count=100,
        export_formats=("jsonld",),
        target_corpus="corpus-nz-hansard",
    )
    assert receipt.status == "failed"
    assert receipt.boundary_integrity_verified is False


def test_riopa_export_receipt_schema_conformance() -> None:
    """Validate serialized RiopaExportReceipt against JSON schema."""
    receipt = RiopaExportReceipt(
        receipt_id="riopa:test-001",
        exported_at="2026-08-17T00:00:00Z",
        riopa_spec_version="v1",
        target_corpus="archive-govt-nz",
        export_formats=("parquet", "jsonld"),
        records_exported=100,
        boundary_integrity_verified=True,
        status="exported",
    )
    data = receipt.to_dict()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
