"""Batch capture budget contracts."""

import pytest

from archive_govt_nz.batch_capture import BatchBudget, admit_batch


def test_batch_budget_admits_bounded_work() -> None:
    """A bounded batch records remaining capacity before transfer."""
    decision = admit_batch(
        BatchBudget(max_total_bytes=100),
        planned_resources=2,
        planned_bytes=80,
        used_bytes=10,
    )
    assert decision.allowed is True
    assert decision.remaining_bytes == 90


@pytest.mark.parametrize(
    "planned_resources,planned_bytes,reason",
    [(11, 1, "resource_budget_exceeded"), (1, 101, "byte_budget_exceeded")],
)
def test_batch_budget_fails_closed(
    planned_resources: int, planned_bytes: int, reason: str
) -> None:
    """Count and byte overruns never start a partial unbounded batch."""
    decision = admit_batch(
        BatchBudget(max_total_bytes=100, max_resources=10),
        planned_resources=planned_resources,
        planned_bytes=planned_bytes,
    )
    assert decision.allowed is False
    assert decision.reason == reason


def test_batch_budget_rejects_non_positive_source_rate() -> None:
    """Source-rate budgets fail closed before any transfer."""
    with pytest.raises(ValueError, match="invalid_batch_budget"):
        BatchBudget(max_requests_per_second=0)
