"""Unit tests for Bronze Hansard acquisition adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.bronze.attestation import Ed25519Signer
from archive_govt_nz.domains.hansard.adapter import HansardBronzeAdapter
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path

SAMPLE_XML = (
    b'<?xml version="1.0" encoding="utf-8"?>\n'
    b'<debate id="HANSARD-20260820-01" date="2026-08-20" '
    b'parliament="54" session="1" volume="776">\n'
    b"    <heading>Parliamentary Question Time</heading>\n"
    b'    <speech id="SPCH-001" speaker="Hon Nicola Willis" '
    b'role="Minister of Finance" type="speech">\n'
    b"        <p>I move that the Budget Measures Bill 2026 be read.</p>\n"
    b"    </speech>\n"
    b"</debate>\n"
)


def test_hansard_bronze_adapter_ingest_and_finalize(tmp_path: Path) -> None:
    """HansardBronzeAdapter ingests sitting XML into CAS and signs manifest."""
    store = ContentAddressedStore(tmp_path / "cas")
    adapter = HansardBronzeAdapter(store=store, base_dir=tmp_path / "bronze")

    outcome = adapter.ingest_document(
        xml_bytes=SAMPLE_XML,
        source_url="https://www.parliament.nz/en/pb/hansard-debates/rhr/document/HANSARD-20260820-01",
        custom_metadata={"provenance_source": "parliament_portal"},
    )

    assert outcome.document_id == "HANSARD-20260820-01"
    assert outcome.sitting_date == "2026-08-20"
    assert outcome.speech_count == 1
    assert outcome.record.domain == "hansard"
    assert outcome.record.fixity.sha256 is not None
    assert outcome.record.custom_metadata is not None
    assert outcome.record.custom_metadata["title"] == "Parliamentary Question Time"

    signer = Ed25519Signer(b"s" * 32)
    batch_res = adapter.finalize_batch(
        batch_id="batch-hansard-001",
        records=[outcome.record],
        manifest_id="001",
        signer=signer,
    )

    assert batch_res.status == "success"
    assert batch_res.records_synced == 1
    assert batch_res.signature_path is not None
    assert (tmp_path / "bronze" / "manifest-001.json").is_file()
    assert (tmp_path / "bronze" / "manifest-001.sig").is_file()
