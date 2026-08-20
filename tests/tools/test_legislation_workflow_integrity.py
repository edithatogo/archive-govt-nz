"""Static fail-closed controls for legislation GitHub workflows."""

from pathlib import Path

_WORKFLOWS = (
    Path(".github/workflows/scheduled-legislation-harvest.yml"),
    Path(".github/workflows/monthly-legislation-reconciliation.yml"),
    Path(".github/workflows/quarterly-legislation-recovery.yml"),
)


def test_legislation_workflows_are_dispatch_only_without_oidc() -> None:
    """Keep recurring and publication authority disabled before later gates."""
    for path in _WORKFLOWS:
        content = path.read_text(encoding="utf-8")
        assert "  schedule:" not in content
        assert "id-token: write" not in content
        assert "workflow_dispatch:" in content
        assert "contents: read" in content
        gate = content.index("exit 3")
        first_external_step = content.index("actions/checkout@")
        assert gate < first_external_step


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
        assert "legislation-state-$STATE_RUN_ID" in content


def test_source_set_does_not_claim_schedule_publication_or_rights() -> None:
    """Keep later external authorities explicitly disabled in configuration."""
    content = Path("config/source-sets/legislation.yml").read_text(encoding="utf-8")
    assert 'execution_mode: "dispatch_only"' in content
    assert 'rights_class: "review_required"' in content
    assert content.count("enabled: false") == 2
    assert "disabled_pending_one_batch_canary_and_weekly_authority" in content
