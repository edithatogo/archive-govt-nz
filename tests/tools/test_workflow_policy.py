"""GitHub Actions safety policy contracts."""

import re
from pathlib import Path


def test_workflows_have_read_only_permissions_and_concurrency() -> None:
    """All workflows expose least privilege and bounded concurrency."""
    root = Path(__file__).parents[2]
    workflows = list((root / ".github/workflows").glob("*.yml"))
    assert workflows
    for workflow in workflows:
        text = workflow.read_text(encoding="utf-8")
        assert "permissions:" in text
        assert "contents: read" in text
        assert "concurrency:" in text
        assert "uses: actions/checkout@" in text
        assert "uses: actions/checkout@v" not in text


def test_workflows_use_immutable_action_refs() -> None:
    """Workflow action references must be pinned to full commit SHAs."""
    root = Path(__file__).parents[2]
    workflows = list((root / ".github/workflows").glob("*.yml"))
    assert workflows

    pinned_reference = re.compile(
        r"^\\s*uses:\\s+[^@\\s]+@([0-9a-f]{40})\\s*(\\s+#.*)?$"
    )
    non_local_reference = re.compile(r"^\\s*uses:\\s+[^@\\s]+@([0-9a-f]{5,})")
    for workflow in workflows:
        for line in workflow.read_text(encoding="utf-8").splitlines():
            if "uses:" not in line:
                continue
            match = non_local_reference.match(line)
            if not match:
                continue
            assert pinned_reference.match(line), line
    capture = (root / ".github/workflows/scheduled-capture.yml").read_text(
        encoding="utf-8"
    )
    assert "enable_capture" in capture
    assert "exit 1" in capture
    ci = (root / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "coverage xml" in ci
    assert "codecov/codecov-action@" in ci
    assert "fail_ci_if_error: true" in ci
    assert "id-token: write" in ci
    assert "use_oidc: true" in ci


def test_health_discovery_preserves_failure_receipts() -> None:
    """Hosted source failures must still upload the bounded discovery receipt."""
    root = Path(__file__).parents[2]
    workflow = (root / ".github/workflows/scheduled-health-discovery.yml").read_text(
        encoding="utf-8"
    )
    upload = workflow.split("uses: actions/upload-artifact@", maxsplit=1)[1]
    assert "if: always()" in upload
    assert "build/live/health-discovery.json" in upload
    assert "if-no-files-found: error" in upload


def test_optional_workflow_arguments_use_shell_arrays() -> None:
    """Optional CLI values must preserve argument boundaries and empty state."""
    root = Path(__file__).parents[2]
    cases = (
        (
            root / ".github/workflows/scheduled-gazette-harvest.yml",
            "BACKFILL_ARGS=()",
            '"${BACKFILL_ARGS[@]}"',
            "$BACKFILL_FLAG",
        ),
        (
            root / ".github/workflows/global-ckan-harvest-huggingface.yml",
            "EXTRA_ARGS=()",
            '"${EXTRA_ARGS[@]}"',
            "$EXTRA_ARGS",
        ),
    )
    for path, declaration, expansion, unsafe_expansion in cases:
        workflow = path.read_text(encoding="utf-8")
        assert declaration in workflow
        assert expansion in workflow
        assert unsafe_expansion not in workflow
