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
    assert set(receipt["scope"]) == {path.as_posix() for path in _WORKFLOWS}
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
        "parent_reference",
        "Seal verified continuation lineage",
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
        assert "parent_reference" in content
        assert "uses: ./.github/actions/legislation-parent-state" in content
        assert "gh run download" not in content
        assert "gh run list" not in content
        assert "mkdir -p build/legislation-state" not in content


def test_all_restoration_precedes_state_consumers() -> None:
    """A failing shared action must prevent harvest, reconciliation and recovery."""
    for path in _WORKFLOWS:
        content = path.read_text(encoding="utf-8")
        assert content.index(
            "uses: ./.github/actions/legislation-parent-state"
        ) < content.index("uv run --locked python tools/run_legislation_")
        assert "continue-on-error" not in content
        assert "gh run download" not in content
        assert "gh run list" not in content
    helper = Path(".github/actions/legislation-parent-state/action.yml").read_text()
    assert 'tools/legislation_parent_state.py "${args[@]}"' in helper
    assert "restoration-receipt.json" in helper
    assert "if: always()" in helper
    harvest = _WORKFLOWS[0].read_text()
    assert harvest.index("Seal verified continuation lineage") < harvest.index(
        "Upload complete continuation state"
    )


def test_source_set_steady_state_configuration() -> None:
    """Validate source-set production operational configuration."""
    content = Path("config/source-sets/legislation.yml").read_text(encoding="utf-8")
    assert "mode: scheduled_and_dispatch" in content
    assert "descriptor: weekly" in content
    assert "rights_class: crown_copyright" in content
    assert "external_actions_enabled: false" in content
    assert content.count("activation: inactive") == 2
