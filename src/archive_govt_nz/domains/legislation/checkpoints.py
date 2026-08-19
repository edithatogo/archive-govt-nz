"""Period-sharded checkpoint management and resumable synchronisation state."""

from __future__ import annotations

import contextlib
import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


class LegislationCheckpointCorruptError(RuntimeError):
    """Raised when a checkpoint file contains invalid or unparseable JSON."""


class LegislationCheckpointManager:
    """Manages persistent batch checkpoints for resumable acquisition."""

    def __init__(self, checkpoint_path: Path) -> None:
        """Initialize checkpoint manager with target file path."""
        self.checkpoint_path = checkpoint_path
        self.staging_path = checkpoint_path.with_suffix(".staging.tmp")

    def _initial_state(self) -> dict[str, Any]:
        """Return clean initial state without fabricated default timestamps."""
        return {
            "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
            "last_updated": None,
            "completed_batches": [],
            "processed_work_ids": [],
            "last_processed_index": 0,
            "total_records_preserved": 0,
        }

    def load(self, *, strict: bool = False) -> dict[str, Any]:
        """Load checkpoint state from disk or return initial state."""
        if self.checkpoint_path.is_file():
            try:
                data = json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                if strict:
                    msg = f"Failed to read checkpoint at {self.checkpoint_path}: {e}"
                    raise LegislationCheckpointCorruptError(msg) from e
                return self._initial_state()
            else:
                if not isinstance(data, dict):
                    if strict:
                        msg = (
                            f"Checkpoint at {self.checkpoint_path} is "
                            "not a valid JSON object"
                        )
                        raise LegislationCheckpointCorruptError(msg)
                    return self._initial_state()
                return data
        return self._initial_state()

    def stage(
        self,
        completed_batches: list[str],
        processed_work_ids: list[str],
        total_records: int,
        metadata: dict[str, Any] | None = None,
    ) -> Path:
        """Stage new checkpoint state to a temporary file before promotion."""
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        payload = {
            "schema_version": "archive-govt-nz.legislation-checkpoint/v1",
            "last_updated": now_iso,
            "completed_batches": completed_batches,
            "processed_work_ids": processed_work_ids,
            "last_processed_index": len(processed_work_ids),
            "total_records_preserved": total_records,
        }
        if metadata:
            payload["metadata"] = metadata
        self.staging_path.parent.mkdir(parents=True, exist_ok=True)
        self.staging_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return self.staging_path

    def promote(self) -> None:
        """Atomically promote staged checkpoint to active checkpoint path."""
        if not self.staging_path.is_file():
            msg = f"No staged checkpoint found at {self.staging_path}"
            raise FileNotFoundError(msg)
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        self.staging_path.replace(self.checkpoint_path)

    def discard_staging(self) -> None:
        """Discard staged checkpoint if it exists."""
        if self.staging_path.is_file():
            with contextlib.suppress(OSError):
                self.staging_path.unlink()

    def save(
        self,
        completed_batches: list[str],
        processed_work_ids: list[str],
        total_records: int,
    ) -> None:
        """Save current checkpoint state to disk atomically."""
        self.stage(completed_batches, processed_work_ids, total_records)
        self.promote()
