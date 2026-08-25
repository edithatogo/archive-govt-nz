"""Integration tests for zero-copy cross-repository federated views in GoldAnalyticsEngine."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pyarrow as pa
import pyarrow.parquet as pq

from archive_govt_nz.core.urn import CanonicalURN
from archive_govt_nz.gold.analytics import GoldAnalyticsEngine
from archive_govt_nz.gold.federation import FederationManager
from archive_govt_nz.silver.base import SILVER_ARROW_SCHEMA

if TYPE_CHECKING:
    from pathlib import Path


def test_zero_copy_federation_views(tmp_path: Path) -> None:
    """GoldAnalyticsEngine and FederationManager create zero-copy joins with external datasets."""
    silver_dir = tmp_path / "silver"
    health_dir = silver_dir / "health"
    leg_dir = silver_dir / "legislation"
    health_dir.mkdir(parents=True, exist_ok=True)
    leg_dir.mkdir(parents=True, exist_ok=True)

    health_urn = CanonicalURN.format("health", "pae_ora", "moh-paracetamol-notice-01")
    health_rows = [
        {
            "nz_canonical_urn": health_urn,
            "nz_source_record_id": "moh-paracetamol-notice-01",
            "nz_acquisition_id": "acq-h-1",
            "nz_content_id": "sha256-h-1",
            "nz_content_cidv1": "bafkreih1",
            "nz_observed_at": "2026-08-24T00:00:00Z",
            "nz_schema_fingerprint": "fp_0123456789abcdef",
            "domain": "health",
            "entity_type": "pae_ora",
            "canonical_uri": "nzhealth:pae_ora/moh-paracetamol-notice-01",
            "title": "Paracetamol 500mg Pharmac Schedule Update",
            "body_text": "Schedule details",
            "body_format": "text",
            "valid_from": "2026-08-24",
            "valid_to": None,
            "source_observed_at": "2026-08-24T00:00:00Z",
            "is_current": True,
            "source_url": "https://health.govt.nz/item",
            "cas_path": "data/cas/1",
            "sha256_payload": "sha256-h-1",
            "blake3_payload": "blake3-h-1",
            "byte_size": 128,
            "metadata_json": json.dumps({"active_ingredient": "Paracetamol"}),
        }
    ]
    t_health = pa.Table.from_pylist(health_rows, schema=SILVER_ARROW_SCHEMA)
    pq.write_table(t_health, health_dir / "corpus.parquet")

    leg_urn = CanonicalURN.format("legislation", "act", "act-public-2026-0001")
    leg_rows = [
        {
            "nz_canonical_urn": leg_urn,
            "nz_source_record_id": "act-public-2026-0001",
            "nz_acquisition_id": "acq-l-1",
            "nz_content_id": "sha256-l-1",
            "nz_content_cidv1": "bafkreil1",
            "nz_observed_at": "2026-08-24T00:00:00Z",
            "nz_schema_fingerprint": "fp_fedcba9876543210",
            "domain": "legislation",
            "entity_type": "act",
            "canonical_uri": "legislation:act/act-public-2026-0001",
            "title": "Medicines and OIA Governance Act 2026",
            "body_text": "Full statutory provisions",
            "body_format": "xml",
            "valid_from": "2026-08-24",
            "valid_to": None,
            "source_observed_at": "2026-08-24T00:00:00Z",
            "is_current": True,
            "source_url": "https://legislation.govt.nz/act/2026/1",
            "cas_path": "data/cas/2",
            "sha256_payload": "sha256-l-1",
            "blake3_payload": "blake3-l-1",
            "byte_size": 256,
            "metadata_json": json.dumps({"act_number": "2026/1"}),
        }
    ]
    t_leg = pa.Table.from_pylist(leg_rows, schema=SILVER_ARROW_SCHEMA)
    pq.write_table(t_leg, leg_dir / "corpus.parquet")

    fed_dir = tmp_path / "fed"
    fed_dir.mkdir(parents=True, exist_ok=True)

    gma_path = fed_dir / "global_medicines.parquet"
    gma_schema = pa.schema(
        [
            pa.field("nz_canonical_urn", pa.string(), nullable=True),
            pa.field("inn_name", pa.string(), nullable=False),
            pa.field("atc_code", pa.string(), nullable=False),
            pa.field("global_status", pa.string(), nullable=False),
        ]
    )
    gma_rows = [
        {
            "nz_canonical_urn": health_urn,
            "inn_name": "paracetamol",
            "atc_code": "N02BE01",
            "global_status": "APPROVED",
        }
    ]
    pq.write_table(pa.Table.from_pylist(gma_rows, schema=gma_schema), gma_path)

    fyi_path = fed_dir / "fyi_requests.parquet"
    fyi_schema = pa.schema(
        [
            pa.field("referenced_urn", pa.string(), nullable=True),
            pa.field("request_id", pa.string(), nullable=False),
            pa.field("public_body", pa.string(), nullable=False),
            pa.field("request_status", pa.string(), nullable=False),
            pa.field("requested_at", pa.string(), nullable=False),
            pa.field("summary", pa.string(), nullable=False),
        ]
    )
    fyi_rows = [
        {
            "referenced_urn": leg_urn,
            "request_id": "FYI-REQ-2026-99",
            "public_body": "Ministry of Justice",
            "request_status": "RELEASED_IN_FULL",
            "requested_at": "2026-08-24",
            "summary": "OIA regarding Medicines and OIA Governance Act implementation",
        }
    ]
    pq.write_table(pa.Table.from_pylist(fyi_rows, schema=fyi_schema), fyi_path)

    # Test direct GoldAnalyticsEngine
    engine = GoldAnalyticsEngine(silver_base_dir=silver_dir)
    engine.register_federation_partner("global-medicines-atlas", gma_path)
    engine.register_federation_partner("fyi-archive", fyi_path)

    res_gma = engine.query(
        "SELECT nz_canonical_urn, inn_name, atc_code, global_status FROM v_fed_health_medicines"
    )
    assert res_gma.row_count == 1

    # Create reimbursement schema & table
    reimb_path = fed_dir / "reimbursement.parquet"
    reimb_schema = pa.schema(
        [
            pa.field("nz_canonical_urn", pa.string(), nullable=False),
            pa.field("scheme_id", pa.string(), nullable=False),
            pa.field("item_code", pa.string(), nullable=False),
            pa.field("reimbursement_amount", pa.float64(), nullable=False),
            pa.field("currency", pa.string(), nullable=False),
        ]
    )
    reimb_rows = [
        {
            "nz_canonical_urn": health_urn,
            "scheme_id": "PHARMAC-SCHED-A",
            "item_code": "PARA-500",
            "reimbursement_amount": 4.50,
            "currency": "NZD",
        }
    ]
    pq.write_table(pa.Table.from_pylist(reimb_rows, schema=reimb_schema), reimb_path)

    # Test FederationManager wrapper
    fed_mgr = FederationManager(engine=engine)
    assert fed_mgr.attach_reimbursement_atlas(reimb_path) == "fed_reimbursement_atlas"

    q_health = fed_mgr.query_statutes_and_medicines()
    assert q_health.row_count == 1

    q_foi = fed_mgr.query_legislation_and_foi()
    assert q_foi.row_count == 1

    engine.close()
