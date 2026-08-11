"""Bounded concurrent capture planning and budget accounting."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BatchBudget:
    """Total transfer and concurrency limits for one capture run."""

    max_total_bytes: int = 10 * 1024 * 1024 * 1024
    max_resources: int = 1000
    concurrency: int = 4
    max_requests_per_second: float = 4.0

    def __post_init__(self) -> None:
        if (
            self.max_total_bytes < 1
            or self.max_resources < 1
            or self.concurrency < 1
            or self.max_requests_per_second <= 0
        ):
            raise ValueError("invalid_batch_budget")


@dataclass(frozen=True, slots=True)
class BatchDecision:
    """Decision before starting a bounded batch."""

    allowed: bool
    reason: str
    remaining_bytes: int
    remaining_resources: int


def admit_batch(
    budget: BatchBudget,
    *,
    planned_resources: int,
    planned_bytes: int,
    used_bytes: int = 0,
) -> BatchDecision:
    """Admit a batch only when count and byte budgets remain."""
    remaining_bytes = budget.max_total_bytes - used_bytes
    remaining_resources = budget.max_resources - planned_resources
    if planned_resources > budget.max_resources:
        return BatchDecision(
            False, "resource_budget_exceeded", remaining_bytes, remaining_resources
        )
    if planned_bytes > remaining_bytes:
        return BatchDecision(
            False, "byte_budget_exceeded", remaining_bytes, remaining_resources
        )
    return BatchDecision(True, "within_budget", remaining_bytes, remaining_resources)


def select_eligible_outcomes(
    outcomes: list[dict[str, Any]],
    *,
    securely_observed_ids: set[object] | None = None,
) -> list[dict[str, Any]]:
    """Select only policy-eligible resources; transport evidence cannot grant rights."""
    selected = [
        item
        for item in outcomes
        if item.get("decision", {}).get("disposition") == "eligible"
    ]
    if securely_observed_ids is None:
        return selected
    return [
        item for item in selected if item.get("resource_id") in securely_observed_ids
    ]
