"""Donor archival receipt data structures."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class DonorArchivalReceipt:
    """Evidence certifying donor repository freeze and archival signoff."""

    receipt_id: str
    evaluated_at: str
    donor_repo: str
    donor_commit_hash: str
    final_tag: str
    deprecation_banner_present: bool
    disaster_restore_rehearsal_passed: bool
    consecutive_successful_cycles: int
    status: str = "frozen_archived"

    def to_dict(self) -> dict[str, Any]:
        """Convert receipt to JSON dictionary."""
        return {
            "receipt_id": self.receipt_id,
            "evaluated_at": self.evaluated_at,
            "donor_repo": self.donor_repo,
            "donor_commit_hash": self.donor_commit_hash,
            "final_tag": self.final_tag,
            "deprecation_banner_present": self.deprecation_banner_present,
            "disaster_restore_rehearsal_passed": self.disaster_restore_rehearsal_passed,
            "consecutive_successful_cycles": self.consecutive_successful_cycles,
            "status": self.status,
        }
