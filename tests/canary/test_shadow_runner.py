"""Test suite for ShadowPipelineRunner and canary rehearsals."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from archive_govt_nz.canary.receipts import CanaryExecutionReceipt
from archive_govt_nz.canary.shadow_runner import ShadowPipelineRunner
from archive_govt_nz.core.identity import SourceIdentity, SourceType
from archive_govt_nz.object_store import ContentAddressedStore

SCHEMA_PATH = Path("schemas/canary/v1/canary-receipt.schema.json")


def test_canary_dual_run_success(tmp_path: Path) -> None:
    """Validate 2-cycle dual shadow run success."""
    donor_store = ContentAddressedStore(tmp_path / "donor")
    shadow_store = ContentAddressedStore(tmp_path / "shadow")

    source = SourceIdentity(
        source_type=SourceType.FEED,
        agency_slug="moh",
        target="https://health.govt.nz/feed",
        source_id="feed:moh:news",
        uri="https://health.govt.nz/feed",
    )

    receipt = ShadowPipelineRunner.execute_canary_dual_run(
        sources=[source],
        donor_store=donor_store,
        shadow_store=shadow_store,
        cycles=2,
    )

    assert receipt.status == "passed"
    assert receipt.cycles_executed == 2
    assert receipt.zero_divergence_verified is True
    assert receipt.rollback_rehearsal_passed is True
    assert receipt.donor_records_captured == 2
    assert receipt.target_records_captured == 2


def test_canary_receipt_schema_conformance() -> None:
    """Validate serialized CanaryExecutionReceipt against JSON schema."""
    receipt = CanaryExecutionReceipt(
        receipt_id="canary:test-001",
        executed_at="2026-08-17T00:00:00Z",
        cycles_executed=2,
        canary_sources_count=1,
        donor_records_captured=2,
        target_records_captured=2,
        zero_divergence_verified=True,
        rollback_rehearsal_passed=True,
        status="passed",
    )
    data = receipt.to_dict()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
