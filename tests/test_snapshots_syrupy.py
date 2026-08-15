"""Snapshot tests for RO-Crate and preservation structures using syrupy."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false, reportMissingTypeStubs=false

from __future__ import annotations

from typing import TYPE_CHECKING

from archive_govt_nz.huggingface_publisher import build_huggingface_dataset_card
from archive_govt_nz.preservation import build_ro_crate_metadata

if TYPE_CHECKING:
    from syrupy.assertion import SnapshotAssertion


def test_ro_crate_metadata_snapshot(snapshot: SnapshotAssertion) -> None:
    """Deterministic RO-Crate metadata matches canonical snapshot."""
    manifest = {
        "discovered_at": "2026-08-16T00:00:00Z",
        "datasets": [
            {
                "id": "ds-001",
                "title": "Treasury Dataset 1",
                "resources": [
                    {
                        "id": "res-001",
                        "name": "data.csv",
                        "url": "https://data.govt.nz/test.csv",
                        "format": "CSV",
                    }
                ],
            }
        ],
    }
    ro_crate = build_ro_crate_metadata(manifest)
    assert ro_crate == snapshot


def test_dataset_card_snapshot(snapshot: SnapshotAssertion) -> None:
    """Hugging Face dataset card matches canonical markdown snapshot."""
    summary = {
        "discovered_datasets": 10,
        "successful_captures": 25,
        "completed_at": "2026-08-16T00:00:00Z",
    }
    card = build_huggingface_dataset_card(summary)
    assert card == snapshot
