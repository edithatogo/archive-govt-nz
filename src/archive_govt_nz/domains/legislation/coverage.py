"""Coverage, completeness auditing, and gap analysis for legislation corpus."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class LegislationCoverageReport:
    """Statistical summary of corpus completeness and gaps."""

    total_seed_works: int = 0
    works_attempted: int = 0
    works_retrieved: int = 0
    xml_manifestations_count: int = 0
    html_fallback_count: int = 0
    failures_count: int = 0
    unresolved_gaps: list[str] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    @property
    def coverage_percent(self) -> float:
        """Calculate percentage of seed inventory covered."""
        if self.total_seed_works == 0:
            return 0.0
        return round((self.works_retrieved / self.total_seed_works) * 100, 2)

    def to_dict(self) -> dict[str, Any]:
        """Convert coverage report to dictionary."""
        return {
            "schema_version": "archive-govt-nz.legislation-coverage/v1",
            "generated_at": self.generated_at,
            "total_seed_works": self.total_seed_works,
            "works_attempted": self.works_attempted,
            "works_retrieved": self.works_retrieved,
            "xml_manifestations_count": self.xml_manifestations_count,
            "html_fallback_count": self.html_fallback_count,
            "failures_count": self.failures_count,
            "coverage_percent": self.coverage_percent,
            "unresolved_gaps_count": len(self.unresolved_gaps),
            "unresolved_gaps": self.unresolved_gaps,
        }
