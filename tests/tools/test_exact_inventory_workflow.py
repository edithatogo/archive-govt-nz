"""Contracts for the governed exact-inventory revalidation lane."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from archive_govt_nz.source_sets import SourceSetConfig, parse_source_set_config

ROOT = Path(__file__).parents[2]
WORKFLOW = ROOT / ".github/workflows/exact-inventory.yml"
CONFIG = ROOT / "config/source-sets/legislation-exact-inventory.yml"
SEED_ID = "historical-work-ids-0001"
SEED_HASH = "59923176fa34796d7673a20b880af9abe5520fe484595edb220f2bbc0e3b33e7"


def workflow() -> dict[str, object]:
    """Load the workflow despite PyYAML's YAML 1.1 `on` coercion."""
    value = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_exact_inventory_config_selects_only_the_governed_seed() -> None:
    """Bind the 500-work lane to the registry identity and exact bytes."""
    config = parse_source_set_config(CONFIG)
    assert isinstance(config, SourceSetConfig)
    assert config.execution.mode == "dispatch_only"
    assert config.execution.lane_type == "exact_inventory"
    assert config.schedule.active is False
    assert config.scope.type == "exact_inventory"
    assert config.scope.seed_id == SEED_ID
    assert config.scope.identifier == SEED_ID
    assert config.scope.inventory_sha256 == SEED_HASH
    assert config.scope.candidate_count == 500
    assert config.scope.coverage_claim is False
    assert config.limits.max_works == 500
    assert config.limits.max_concurrency == 1
    assert config.limits.overlap_policy == "reject"
    assert config.publication.external_actions_enabled is False


def test_workflow_is_manual_least_privilege_and_globally_serialized() -> None:
    """Keep state mutation operator-gated and serialized with sibling lanes."""
    text = WORKFLOW.read_text(encoding="utf-8")
    data = workflow()
    assert "schedule:" not in text
    assert data["permissions"] == {"actions": "read", "contents": "read"}
    assert "group: legislation-canonical-state" in text
    sibling = (ROOT / ".github/workflows/scheduled-legislation-harvest.yml").read_text()
    assert "group: legislation-canonical-state" in sibling
    assert "cancel-in-progress: false" in text
    assert "timeout-minutes: 360" in text
    assert "confirmed_execution" in text
    assert "persist-credentials: false" in text
    assert "fetch-depth: 0" in text
    assert "HF_TOKEN" not in text
    assert "ZENODO" not in text
    assert "contents: write" not in text


def test_workflow_authenticates_seed_and_parent_before_source_access() -> None:
    """Reject missing or corrupt custody inputs before exposing the API key."""
    text = WORKFLOW.read_text(encoding="utf-8")
    seed = text.index("Resolve governed reviewed inventory")
    parent = text.index("Restore and authenticate selected parent")
    source = text.index("Revalidate every governed work ID")
    assert seed < parent < source
    assert "tools/seed_registry.py historical-work-ids-0001" in text
    assert "seed-id: historical-work-ids-0001" in text
    assert "mode: continuation" in text
    assert "--force-resync" in text
    assert "--work-ids-file seeds/reviewed/historical-work-ids-0001.txt" in text
    assert "--max-works 500" in text
    assert "LEGISLATION_API_KEY" in text


def test_workflow_reconciles_seals_and_retains_every_attempt() -> None:
    """Require exact accounting, fixity, lineage and success/failure evidence."""
    text = WORKFLOW.read_text(encoding="utf-8")
    acquisition = text.index("Revalidate every governed work ID")
    reconcile = text.index("Reconcile exact inventory and cumulative state")
    verify = text.index("Verify accounting and bounded output")
    seal = text.index("Seal verified continuation lineage")
    assert acquisition < reconcile < verify < seal
    assert "--expected-batch-sha256" in text
    assert SEED_HASH in text
    reconciliation_path = "build/legislation-attempt/reconciliation.json"
    assert text.count(reconciliation_path) == 3
    assert "build/legislation-state/receipts/reconciliation.json" not in text
    assert "receipts/continuation.json" in text
    assert text.count("!inputs.preflight_only && always()") >= 2
    assert "legislation-exact-inventory-attempt-" in text


def test_parent_preflight_cannot_acquire_or_upload() -> None:
    """The first hosted run verifies only the durable parent and exposes no secret."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "preflight_only:" in text
    assert (
        "Restore and verify the parent without source acquisition or state upload"
        in text
    )
    assert "default: false" in text
    assert "if: inputs.preflight_only" in text
    assert text.count("if: ${{ !inputs.preflight_only") >= 6
    preflight = text[
        text.index("Verify no-write parent preflight") : text.index(
            "Revalidate every governed work ID"
        )
    ]
    assert "NZ_LEGISLATION_API_KEY" not in preflight
    assert "upload-artifact" not in preflight
    assert "if-no-files-found: error" in text
    assert 'MAX_STATE_BYTES: "134217728"' in text
    assert 'MAX_CAS_BYTES: "67108864"' in text
    assert 'MAX_CAS_OBJECTS: "4096"' in text
    assert 'MAX_RETRIES_PER_WORK: "3"' in text


@pytest.mark.parametrize(
    "forbidden",
    ["--search-term", "--search-terms-file", "gh run list", "latest successful"],
)
def test_workflow_cannot_fall_back_to_discovery_or_implicit_parent(
    forbidden: str,
) -> None:
    """Prevent false completion through search or latest-run selection."""
    assert forbidden not in WORKFLOW.read_text(encoding="utf-8")


def test_parent_reference_input_is_required_and_canonical() -> None:
    """Require the operator to select one committed parent reference."""
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "parent_reference:" in text
    assert "required: true" in text
    assert "config/legislation/parents/" in text
    assert "current.json" not in text


def test_operational_receipt_fixture_has_all_terminal_dispositions() -> None:
    """Characterize the v3 accounting contract consumed by this workflow."""
    receipt = json.loads(
        (ROOT / "tests/fixtures/legislation-harvest-receipt-v3.json").read_text()
    )
    for field in (
        "newly_preserved",
        "changed_preserved",
        "unchanged_revalidated",
        "unavailable",
        "partial",
        "failed",
        "already_processed_skipped",
    ):
        assert field in receipt
