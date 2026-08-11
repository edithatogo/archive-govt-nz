"""Scheduled redundancy workflow contracts."""

from pathlib import Path


def test_scheduled_redundancy_workflow_is_bounded_and_retained() -> None:
    """The hosted lane is scheduled, least privilege, bounded, and evidenced."""
    workflow = Path(__file__).parents[2] / ".github/workflows/scheduled-redundancy.yml"
    text = workflow.read_text(encoding="utf-8")
    assert "schedule:" in text
    assert "workflow_dispatch:" in text
    assert "contents: read" in text
    assert "timeout-minutes:" in text
    assert "concurrency:" in text
    assert "discover_replacement_urls.py" in text
    assert "capture_internet_archive_backups.py" in text
    assert "verify_internet_archive_backups.py" in text
    assert "submit_save_page_now.py" in text
    assert "retention-days: 90" in text
    assert "continue-on-error: true" not in text
