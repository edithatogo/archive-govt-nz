"""Historical batch merging, review, and verification pipeline."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path


def load_work_ids_from_batch_file(path: Path) -> list[str]:
    """Read clean work IDs from a period-sharded batch text file."""
    if not path.is_file():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]


def reconcile_historical_batches(
    batch_dir: Path,
) -> dict[str, Any]:
    """Reconcile all period-sharded batch files in the specified directory."""
    batches: dict[str, int] = {}
    all_work_ids: set[str] = set()

    for file in sorted(batch_dir.glob("historical-work-ids-*.txt")):
        ids = load_work_ids_from_batch_file(file)
        batches[file.name] = len(ids)
        all_work_ids.update(ids)

    return {
        "schema_version": "archive-govt-nz.legislation-bootstrap/v1",
        "total_batches_found": len(batches),
        "total_unique_work_ids": len(all_work_ids),
        "batch_breakdown": batches,
    }
