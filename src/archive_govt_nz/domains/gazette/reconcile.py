"""Cross-source Gazette reconciliation across official and archival sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class GazetteSourceReconciliationReport:
    """Report comparing gazette notice coverage across multi-source repositories."""

    official_notices_count: int = 0
    digitalnz_matches_count: int = 0
    historical_archive_count: int = 0
    reconciled_canonical_count: int = 0
    unresolved_discrepancies: list[str] = field(default_factory=list)
    generated_at: str = field(
        default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "schema_version": "archive-govt-nz.gazette-reconciliation/v1",
            "generated_at": self.generated_at,
            "official_notices_count": self.official_notices_count,
            "digitalnz_matches_count": self.digitalnz_matches_count,
            "historical_archive_count": self.historical_archive_count,
            "reconciled_canonical_count": self.reconciled_canonical_count,
            "discrepancies_count": len(self.unresolved_discrepancies),
            "unresolved_discrepancies": self.unresolved_discrepancies,
        }
