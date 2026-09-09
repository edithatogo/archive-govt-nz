"""Fail-closed local release-readiness contracts."""

from __future__ import annotations

from typing import Any

import pytest

from archive_govt_nz.domains.health_appropriations.candidate_inventory import (
    assess_release_readiness,
)


@pytest.fixture
def ready_receipt() -> dict[str, Any]:
    return {
        "rights_state": "cleared",
        "source_disposition": "complete",
        "parity_state": "passed",
        "recovery_state": "passed",
        "source_revision": "a" * 40,
        "candidate_manifest_sha256": "b" * 64,
        "restricted_content": False,
    }


def test_ready_receipt_remains_unpublished(ready_receipt: dict[str, Any]) -> None:
    """All local prerequisites can pass without granting publication approval."""
    result = assess_release_readiness(ready_receipt)
    assert result == {
        "schema_version": "archive-govt-nz.health-release-readiness/v1",
        "status": "ready_for_explicit_gate",
        "publication_approval": "not_granted",
        "blockers": [],
    }


@pytest.mark.parametrize(
    ("field", "value", "blocker"),
    [
        ("rights_state", "not_evaluated", "rights_missing_or_uncleared"),
        ("source_disposition", "partial", "source_disposition_incomplete"),
        ("parity_state", "failed", "parity_not_passed"),
        ("recovery_state", "failed", "recovery_not_passed"),
        ("source_revision", "main", "source_revision_not_pinned"),
        ("candidate_manifest_sha256", "bad", "candidate_manifest_mismatch"),
        ("restricted_content", True, "restricted_content_present"),
    ],
)
def test_each_unresolved_gate_blocks_readiness(
    ready_receipt: dict[str, Any], field: str, value: object, blocker: str
) -> None:
    """Every missing or unsafe prerequisite produces an explicit blocker."""
    ready_receipt[field] = value
    result = assess_release_readiness(ready_receipt)
    assert result["status"] == "blocked"
    assert blocker in result["blockers"]
    assert result["publication_approval"] == "not_granted"
