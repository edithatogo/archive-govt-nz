"""Data models for differential parity evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class ParityComparisonResult:
    """Outcome of one adapter or record differential comparison."""

    source_id: str
    adapter_name: str
    donor_sha256: str
    target_sha256: str
    is_identical: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Serialize comparison to JSON-compatible dictionary."""
        d: dict[str, Any] = {
            "source_id": self.source_id,
            "adapter_name": self.adapter_name,
            "donor_sha256": self.donor_sha256,
            "target_sha256": self.target_sha256,
            "is_identical": self.is_identical,
        }
        if self.notes:
            d["notes"] = self.notes
        return d


@dataclass(frozen=True, slots=True)
class ParityReceipt:
    """Cryptographic evidence certifying zero-divergence parity."""

    receipt_id: str
    evaluated_at: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    divergence_count: int
    status: str
    comparisons: tuple[ParityComparisonResult, ...] = field(default_factory=tuple)

    @classmethod
    def from_comparisons(
        cls,
        comparisons: list[ParityComparisonResult],
        receipt_id: str | None = None,
    ) -> ParityReceipt:
        """Construct ParityReceipt from a list of test results."""
        total = len(comparisons)
        passed = sum(1 for c in comparisons if c.is_identical)
        failed = total - passed
        status = "passed" if failed == 0 and total > 0 else "failed"
        rid = receipt_id or f"par:eval-{int(datetime.now(UTC).timestamp())}"
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

        return cls(
            receipt_id=rid,
            evaluated_at=now_iso,
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            divergence_count=failed,
            status=status,
            comparisons=tuple(comparisons),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize receipt to JSON-compatible dictionary matching JSON schema."""
        return {
            "receipt_id": self.receipt_id,
            "evaluated_at": self.evaluated_at,
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "divergence_count": self.divergence_count,
            "status": self.status,
            "comparisons": [c.to_dict() for c in self.comparisons],
        }
