"""Tests for source alternative and tombstone scheduling policy."""

from datetime import UTC, datetime, timedelta
from typing import Any, cast

import pytest

from archive_govt_nz.source_policy import (
    classify_metadata_fallback,
    load_allowlist,
    schedule_tombstone_reprobe,
    validate_tombstone_reprobe_receipt,
)


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
    row = cast("list[dict[str, Any]]", receipt["tombstones"])[0]
    assert row["next_probe_at"] == "2026-08-08T00:00:00+00:00"
    assert row["retention"] == "preserve-prior-history"
    assert row["attempt_count"] == 1
    assert row["retry_state"] == "scheduled"
    validate_tombstone_reprobe_receipt(receipt, expected_count=1)


def test_reprobe_preserves_attempt_count_from_prior_receipt() -> None:
    """Retries remain bounded and auditable across scheduler runs."""
    now = datetime(2026, 8, 1, tzinfo=UTC)
    receipt = schedule_tombstone_reprobe(
        {"results": [{"resource_id": "r1", "state": "tombstone-required"}]},
        now=now,
        prior={"tombstones": [{"resource_id": "r1", "attempt_count": 4}]},
    )
    row = cast("list[dict[str, Any]]", receipt["tombstones"])[0]
    assert row["attempt_count"] == 5


def test_reprobe_validator_rejects_duplicate_or_wrong_state() -> None:
    """Malformed evidence cannot be published as a valid schedule."""
    with pytest.raises(ValueError, match="unique"):
        validate_tombstone_reprobe_receipt(
            {
                "schema_version": "archive-govt-nz.tombstone-reprobe/v1",
                "tombstones": [
                    {
                        "resource_id": "r1",
                        "state": "tombstone-required",
                        "retry_state": "scheduled",
                        "attempt_count": 1,
                    },
                    {
                        "resource_id": "r1",
                        "state": "tombstone-required",
                        "retry_state": "scheduled",
                        "attempt_count": 1,
                    },
                ],
            }
        )


def test_metadata_and_datastore_success_never_promote_payload() -> None:
    """Diagnostic API success remains ineligible for payload capture."""
    result = classify_metadata_fallback(
        {"resource_id": "r1"}, package_status=200, datastore_status=200
    )
    assert result["state"] == "datastore-diagnostic-available"
    assert result["payload_eligible"] is False


def test_reprobe_rejects_unbounded_interval_and_deduplicates_ids() -> None:
    """Reject unsafe schedules and emit one receipt per resource."""
    now = datetime(2026, 8, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="365 days"):
        schedule_tombstone_reprobe({}, now=now, interval=timedelta(days=366))
    receipt = schedule_tombstone_reprobe(
        {
            "results": [
                {"resource_id": "r1", "state": "tombstone-required"},
                {"resource_id": "r1", "state": "tombstone-required"},
            ]
        },
        now=now,
    )
    rows = cast("list[dict[str, Any]]", receipt["tombstones"])
    assert [row["resource_id"] for row in rows] == ["r1"]


"""Tests for source alternative and tombstone scheduling policy."""
"""Tests for source alternative and tombstone scheduling policy."""
