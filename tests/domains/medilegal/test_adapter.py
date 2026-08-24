"""Tests for Medico-Legal Bronze acquisition adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.bronze.attestation import Ed25519Signer
from archive_govt_nz.domains.medilegal.adapter import MedicoLegalBronzeAdapter
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path

SAMPLE_CASE_JSON = {
    "schema_version": "archive-govt-nz.medilegal-case/v1",
    "case_id": "HDC-21HDC01234",
    "tribunal": "HDC",
    "decision_date": "2023-05-12",
    "title": "Breach of Right 4(1)",
    "findings_summary": "Finding of breach.",
    "full_text": "Decision under the Health and Disability Commissioner Act 1994.",
    "statutory_provisions": ["Health and Disability Commissioner Act 1994"],
    "is_anonymized": True,
}


def test_medilegal_bronze_adapter_ingest_json(tmp_path: Path) -> None:
    """MedicoLegalBronzeAdapter ingests JSON case into CAS and signs batch manifest."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = MedicoLegalBronzeAdapter(
        store=store, base_dir=tmp_path / "bronze_medilegal"
    )

    payload = json.dumps(SAMPLE_CASE_JSON).encode("utf-8")
    outcome = adapter.ingest_document(
        payload_bytes=payload,
        source_url="https://www.hdc.org.nz/decisions/21HDC01234",
        observed_at="2026-08-24T12:00:00Z",
    )

    assert outcome.case_id == "HDC-21HDC01234"
    assert outcome.tribunal == "HDC"
    assert outcome.record.domain == "medilegal"
    assert outcome.record.record_id == "HDC-21HDC01234"
    receipt = store.verify(f"sha256:{outcome.record.fixity.sha256}")
    assert receipt.byte_count == len(payload)

    signer = Ed25519Signer.generate()
    batch_res = adapter.finalize_batch(
        batch_id="batch-medilegal-001",
        records=[outcome.record],
        signer=signer,
    )
    assert batch_res.records_synced == 1
    assert batch_res.manifest_path is not None
    assert batch_res.signature_path is not None


def test_medilegal_bronze_adapter_ingest_raw_text(tmp_path: Path) -> None:
    """MedicoLegalBronzeAdapter ingests raw text decision with explicit metadata."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = MedicoLegalBronzeAdapter(
        store=store, base_dir=tmp_path / "bronze_medilegal"
    )

    raw_text = b"Finding of professional breach under HPCA Act 2003 regarding Dr B."
    outcome = adapter.ingest_document(
        payload_bytes=raw_text,
        source_url="https://www.hpdt.org.nz/decisions/123",
        case_id="HPDT-123",
        tribunal="HPDT",
        decision_date="2022-04-15",
    )

    assert outcome.case_id == "HPDT-123"
    assert outcome.tribunal == "HPDT"
    assert outcome.decision_date == "2022-04-15"
    assert outcome.record.domain == "medilegal"


def test_medilegal_bronze_adapter_raw_text_missing_metadata(
    tmp_path: Path,
) -> None:
    """Bronze adapter raises ValueError if raw text lacks required metadata."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = MedicoLegalBronzeAdapter(store=store)

    with pytest.raises(ValueError, match="required for raw text ingest"):
        adapter.ingest_document(
            payload_bytes=b"raw text without case_id",
            source_url="https://example.com/raw",
        )
