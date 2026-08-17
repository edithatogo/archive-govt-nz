"""Donor freeze prerequisite validator and receipt generator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from archive_govt_nz.archival.receipts import DonorArchivalReceipt

MIN_SUCCESSFUL_CYCLES = 2


@dataclass(frozen=True, slots=True)
class DonorEvaluationParams:
    """Parameters for evaluating donor repository freeze readiness."""

    donor_repo: str
    donor_commit: str
    final_tag: str
    readme_content: str
    disaster_restore_passed: bool = True
    consecutive_successful_cycles: int = 2
    receipt_id: str | None = None


class DonorFreezeValidator:
    """Validates prerequisites before donor repository archival and freeze."""

    @classmethod
    def evaluate_freeze_readiness(
        cls,
        params: DonorEvaluationParams,
    ) -> DonorArchivalReceipt:
        """Verify all archival criteria and return verified receipt."""
        has_banner = (
            "DEPRECATED" in params.readme_content.upper()
            and "ARCHIVE-GOVT-NZ" in params.readme_content.upper()
        )
        cycles_ok = params.consecutive_successful_cycles >= MIN_SUCCESSFUL_CYCLES
        all_passed = has_banner and params.disaster_restore_passed and cycles_ok

        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        rid = params.receipt_id or f"freeze:donor-{int(datetime.now(UTC).timestamp())}"
        status = "frozen_archived" if all_passed else "failed"

        return DonorArchivalReceipt(
            receipt_id=rid,
            evaluated_at=now_iso,
            donor_repo=params.donor_repo,
            donor_commit_hash=params.donor_commit,
            final_tag=params.final_tag,
            deprecation_banner_present=has_banner,
            disaster_restore_rehearsal_passed=params.disaster_restore_passed,
            consecutive_successful_cycles=params.consecutive_successful_cycles,
            status=status,
        )
