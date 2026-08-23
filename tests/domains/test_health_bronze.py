"""Tests for Health domain Bronze ingestion adapters (COVID-19 & Pae Ora)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.domains.health.covid_data import CovidDataIngestor
from archive_govt_nz.domains.health.pae_ora import PaeOraReformIngestor
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


def test_covid_data_ingestor(tmp_path: Path) -> None:
    """Test historical pandemic dataset ingestion into Bronze CAS."""
    store = ContentAddressedStore(tmp_path / "cas")
    out_dir = tmp_path / "covid_bronze"
    ingestor = CovidDataIngestor(store=store, base_dir=out_dir)

    csv_data = b"date,region,cases\n2022-01-01,Auckland,12\n"
    rec = ingestor.ingest_dataset_release(
        dataset_id="moh-covid-case-counts-2022",
        title="COVID-19 Case Counts by District",
        release_date="2022-01-02T00:00:00Z",
        payload_bytes=csv_data,
        source_url="https://health.govt.nz/covid-data/case-counts.csv",
        media_type="text/csv",
    )

    assert rec.record_id == "rec-covid-moh-covid-case-counts-2022"
    res = ingestor.finalize(batch_id="covid-batch-001", records=[rec])
    assert res.status == "success"
    assert res.records_synced == 1


def test_pae_ora_reform_ingestor(tmp_path: Path) -> None:
    """Test Pae Ora health system reform publication ingestion into Bronze CAS."""
    store = ContentAddressedStore(tmp_path / "cas")
    out_dir = tmp_path / "pae_ora_bronze"
    ingestor = PaeOraReformIngestor(store=store, base_dir=out_dir)

    pdf_data = b"%PDF-1.4 sample policy document content"
    rec = ingestor.ingest_publication(
        document_id="policy-transition-framework-2022",
        title="Pae Ora Health System Operating Framework",
        entity="Health New Zealand / Te Whatu Ora",
        published_at="2022-07-01T09:00:00Z",
        payload_bytes=pdf_data,
        source_url="https://health.govt.nz/publications/pae-ora-operating-framework.pdf",
    )

    assert rec.record_id == "rec-pae-ora-policy-transition-framework-2022"
    assert (
        rec.custom_metadata["statutory_context"] == "Pae Ora (Healthy Futures) Act 2022"
    )

    res = ingestor.finalize(batch_id="pae-ora-batch-001", records=[rec])
    assert res.status == "success"
    assert res.records_synced == 1
