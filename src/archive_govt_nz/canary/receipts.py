"""Canary receipt models and serialization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CanaryExecutionReceipt:
    """Receipt documenting canary dual-execution and rollback proof."""

    receipt_id: str
    executed_at: str
    cycles_executed: int
    canary_sources_count: int
    donor_records_captured: int
    target_records_captured: int
    zero_divergence_verified: bool
    rollback_rehearsal_passed: bool
    status: str

    def to_dict(self) -> dict[str, Any]:
        """Convert receipt to JSON dictionary."""
        return {
            "receipt_id": self.receipt_id,
            "executed_at": self.executed_at,
            "cycles_executed": self.cycles_executed,
            "canary_sources_count": self.canary_sources_count,
            "donor_records_captured": self.donor_records_captured,
            "target_records_captured": self.target_records_captured,
            "zero_divergence_verified": self.zero_divergence_verified,
            "rollback_rehearsal_passed": self.rollback_rehearsal_passed,
            "status": self.status,
        }
