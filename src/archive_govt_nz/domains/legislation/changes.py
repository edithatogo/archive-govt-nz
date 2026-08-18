"""Change detection and freshness monitoring for official legislation feeds."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class LegislationChangeEvent:
    """Event representing detected change in statutory text or status."""

    work_id: str
    event_type: str  # "new_enactment", "amendment", "repeal", "updated_metadata"
    timestamp: str
    previous_cas_hash: str | None = None
    new_cas_hash: str | None = None
    details: str = ""


@dataclass
class LegislationChangeReport:
    """Summary report of changes detected during a sync cycle."""

    detected_at: str = field(
        default_factory=lambda: datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    events: list[LegislationChangeEvent] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        """Check if any change events were recorded."""
        return len(self.events) > 0

    def to_dict(self) -> dict[str, Any]:
        """Convert change report to dictionary."""
        return {
            "schema_version": "archive-govt-nz.legislation-changes/v1",
            "detected_at": self.detected_at,
            "total_changes": len(self.events),
            "events": [
                {
                    "work_id": e.work_id,
                    "event_type": e.event_type,
                    "timestamp": e.timestamp,
                    "previous_cas_hash": e.previous_cas_hash,
                    "new_cas_hash": e.new_cas_hash,
                    "details": e.details,
                }
                for e in self.events
            ],
        }
