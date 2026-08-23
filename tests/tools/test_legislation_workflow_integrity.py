"""Static fail-closed controls for legislation GitHub workflows."""

import json
from pathlib import Path

_WORKFLOWS = (
    Path(".github/workflows/scheduled-legislation-harvest.yml"),
    Path(".github/workflows/monthly-legislation-reconciliation.yml"),
    Path(".github/workflows/quarterly-legislation-recovery.yml"),
)


def test_legislation_workflows_steady_state_cadence_and_permissions() -> None:
    """Verify steady-state weekly harvest, monthly checks, and operator recovery."""
    harvest_content = _WORKFLOWS[0].read_text(encoding="utf-8")
    assert "0 18 * * 0" in harvest_content
    assert "workflow_dispatch:" in harvest_content
    assert "id-token: write" not in harvest_content
    assert "contents: read" in harvest_content

    reconciliation_content = _WORKFLOWS[1].read_text(encoding="utf-8")
    assert "0 6 1 * *" in reconciliation_content
    assert "workflow_dispatch:" in reconciliation_content
    assert "id-token: write" not in reconciliation_content
    assert "contents: read" in reconciliation_content

    recovery_content = _WORKFLOWS[2].read_text(encoding="utf-8")
    assert "  schedule:" not in recovery_content
    assert "workflow_dispatch:" in recovery_content
    assert "id-token: write" not in recovery_content
    assert "contents: read" in recovery_content


def test_operational_gates_opened_only_with_recorded_authorization() -> None:
    """Gate removal must be backed by the maintainer authorization receipt."""
    receipt = json.loads(
        Path(
            "evidence/migrations/corpus-legislation-nz/"
            "operational-gate-authorization.json"
        ).read_text(encoding="utf-8")
    )
    assert receipt["schema_version"] == (
        "archive-govt-nz.operational-gate-authorization/v1"
    )
    assert receipt["decision"] == "OPEN_GATES"
    assert set(receipt["scope"]) == {str(path) for path in _WORKFLOWS}
    assert len(receipt["authorities_granted"]) >= 5
    assert receipt["retained_controls"], "fail-closed controls must be listed"


def test_harvest_requires_scope_and_carries_complete_state() -> None:
    """Require confirmation and persist all linked continuation evidence."""
    content = _WORKFLOWS[0].read_text(encoding="utf-8")
    for required in (
        "confirmed_execution",
        "batch_id",
        "search_terms",
        "max_works",
        "prior_state_run_id",
        "legislation-state/checkpoint.json",
        "legislation-state/manifest.json",
        "legislation-state/cas",
        "legislation-state-${{ github.run_id }}",
    ):
        assert required in content
    assert "backfill_limit" not in content


def test_reconciliation_and_recovery_require_selected_state() -> None:
    """Do not reconcile or recover implicit empty runner-local state."""
    for path in _WORKFLOWS[1:]:
        content = path.read_text(encoding="utf-8")
        assert "state_run_id" in content
        assert "gh run download" in content
        has_state_dir = (
            "legislation-state-$TARGET_RUN_ID" in content
            or "legislation-state-$STATE_RUN_ID" in content
        )
        assert has_state_dir


def test_source_set_steady_state_configuration() -> None:
    """Validate source-set production operational configuration."""
    content = Path("config/source-sets/legislation.yml").read_text(encoding="utf-8")
    assert 'execution_mode: "scheduled_and_dispatch"' in content
    assert 'schedule: "weekly"' in content
    assert 'rights_class: "crown_copyright"' in content
    assert content.count("enabled: true") >= 3
