"""Period-sharded checkpoint management and resumable synchronisation state."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class LegislationCheckpointManager:
    """Manages persistent batch checkpoints for resumable acquisition."""

    def __init__(self, checkpoint_path: Path) -> None:
        """Initialize checkpoint manager with target file path."""
        self.checkpoint_path = checkpoint_path

    def load(self) -> dict[str, Any]:
        """Load checkpoint state from disk or return default initial state."""
        if self.checkpoint_path.is_file():
            try:
                return json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError, OSError:
                pass
        return {
            "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
            "last_updated": "2026-08-18T11:13:00Z",
            "completed_batches": [],
            "processed_work_ids": [],
            "last_processed_index": 0,
            "total_records_preserved": 0,
        }

    def save(
        self,
        completed_batches: list[str],
        processed_work_ids: list[str],
        total_records: int,
    ) -> None:
        """Save current checkpoint state to disk."""
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {
            "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
            "last_updated": now_iso,
            "completed_batches": completed_batches,
            "processed_work_ids": processed_work_ids,
            "last_processed_index": len(processed_work_ids),
            "total_records_preserved": total_records,
        }
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.checkpoint_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
