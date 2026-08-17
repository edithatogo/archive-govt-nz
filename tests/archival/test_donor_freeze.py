"""Test suite for DonorFreezeValidator and archival receipts."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from archive_govt_nz.archival.donor_freeze import (
    DonorEvaluationParams,
    DonorFreezeValidator,
)
from archive_govt_nz.archival.receipts import DonorArchivalReceipt

SCHEMA_PATH = Path("schemas/archival/v1/donor-archival-receipt.schema.json")


def test_donor_freeze_evaluation_success() -> None:
    """Validate successful donor freeze evaluation."""
    readme = "# sm-govt-nz (DEPRECATED)\nMigrated to archive-govt-nz."
    params = DonorEvaluationParams(
        donor_repo="edithatogo/sm-govt-nz",
        donor_commit="24df5f2dea7cfcd85fecaa1a18845339f987eeec",
        final_tag="v0.9.0-archived",
        readme_content=readme,
        disaster_restore_passed=True,
        consecutive_successful_cycles=2,
    )
    receipt = DonorFreezeValidator.evaluate_freeze_readiness(params)
    assert receipt.status == "frozen_archived"
    assert receipt.deprecation_banner_present is True
    assert receipt.disaster_restore_rehearsal_passed is True


def test_donor_freeze_evaluation_missing_banner() -> None:
    """Validate failure when deprecation banner is missing."""
    params = DonorEvaluationParams(
        donor_repo="edithatogo/sm-govt-nz",
        donor_commit="24df5f2dea7cfcd85fecaa1a18845339f987eeec",
        final_tag="v0.9.0-archived",
        readme_content="Normal untouched readme",
        disaster_restore_passed=True,
        consecutive_successful_cycles=2,
    )
    receipt = DonorFreezeValidator.evaluate_freeze_readiness(params)
    assert receipt.status == "failed"
    assert receipt.deprecation_banner_present is False


def test_donor_archival_receipt_schema_conformance() -> None:
    """Validate serialized DonorArchivalReceipt against JSON schema."""
    receipt = DonorArchivalReceipt(
        receipt_id="freeze:test-001",
        evaluated_at="2026-08-17T00:00:00Z",
        donor_repo="edithatogo/sm-govt-nz",
        donor_commit_hash="24df5f2dea7cfcd85fecaa1a18845339f987eeec",
        final_tag="v0.9.0-archived",
        deprecation_banner_present=True,
        disaster_restore_rehearsal_passed=True,
        consecutive_successful_cycles=2,
        status="frozen_archived",
    )
    data = receipt.to_dict()
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=data, schema=schema)
