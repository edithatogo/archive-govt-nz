"""Tests for source alternative and tombstone scheduling policy."""

from datetime import UTC, datetime, timedelta

import pytest

from archive_govt_nz.source_policy import load_allowlist, schedule_tombstone_reprobe


def test_allowlist_accepts_only_https() -> None:
    """Reject insecure alternatives while accepting explicit HTTPS."""
    assert load_allowlist({"alternatives": {"r1": ["https://example.test/a"]}})["r1"]
    with pytest.raises(ValueError, match="absolute HTTPS"):
        load_allowlist({"alternatives": {"r1": ["http://example.test/a"]}})


def test_tombstone_receipt_schedules_retry_and_preserves_history() -> None:
    """Schedule a bounded retry without deleting prior history."""
    now = datetime(2026, 8, 1, tzinfo=UTC)
    receipt = schedule_tombstone_reprobe(
        {"results": [{"resource_id": "r1", "state": "tombstone-required"}]},
        now=now,
        interval=timedelta(days=7),
    )
    row = receipt["tombstones"][0]
    assert row["next_probe_at"] == "2026-08-08T00:00:00+00:00"
    assert row["retention"] == "preserve-prior-history"


"""Tests for source alternative and tombstone scheduling policy."""
"""Tests for source alternative and tombstone scheduling policy."""
