"""Tests for HathiTrust Bronze acquisition adapter."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from archive_govt_nz.bronze.attestation import Ed25519Signer
from archive_govt_nz.domains.hathi.adapter import HathiBronzeAdapter
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path

SAMPLE_HATHI_JSON = {
    "schema_version": "archive-govt-nz.hathi-volume/v1",
    "volume_id": "nyp.33433012345678",
    "title": "Ordinances of the Province of Auckland",
    "author": "Auckland Provincial Council",
    "publication_year": 1865,
    "rights_attributes": "pd",
    "source_institution": "New York Public Library",
    "page_count": 1,
    "ocr_pages": [
        {
            "page_seq": 1,
            "page_number": "1",
            "page_text": "An Ordinance for establishing a Police Force.",
        }
    ],
}


def test_hathi_bronze_adapter_ingest(tmp_path: Path) -> None:
    """HathiBronzeAdapter ingests volume into CAS and creates signed manifest."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = HathiBronzeAdapter(store=store, base_dir=tmp_path / "bronze_hathi")

    payload = json.dumps(SAMPLE_HATHI_JSON).encode("utf-8")
    outcome = adapter.ingest_document(
        payload_bytes=payload,
        source_url="https://catalog.hathitrust.org/Record/001",
        observed_at="2026-08-24T12:00:00Z",
    )

    assert outcome.volume_id == "nyp.33433012345678"
    assert outcome.title == "Ordinances of the Province of Auckland"
    assert outcome.page_count == 1
    assert outcome.record.domain == "hathi"
    assert outcome.record.record_id == "nyp.33433012345678"
    receipt = store.verify(f"sha256:{outcome.record.fixity.sha256}")
    assert receipt.byte_count == len(payload)

    signer = Ed25519Signer.generate()
    batch_res = adapter.finalize_batch(
        batch_id="batch-hathi-001",
        records=[outcome.record],
        signer=signer,
    )
    assert batch_res.records_synced == 1
    assert batch_res.manifest_path is not None
    assert batch_res.signature_path is not None
