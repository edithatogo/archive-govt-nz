"""GitHub Actions safety policy contracts."""

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
