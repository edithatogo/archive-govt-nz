"""Tests for global concurrent capture runner."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import patch

from archive_govt_nz.global_capture import (
    GlobalBatchCaptureConfig,
    run_global_batch_capture,
)
from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreReceipt

if TYPE_CHECKING:
    from pathlib import Path


def test_global_batch_capture_runner(tmp_path: Path) -> None:
    """Batch capture streams eligible items and logs outcomes."""
    store = ContentAddressedStore(tmp_path / "objects")
    candidates = [
        {
            "dataset_id": "ds-1",
            "resource_id": "res-1",
            "url": "https://example.govt.nz/file1.csv",
            "classification": "eligible",
            "download_authorized": True,
        },
        {
            "dataset_id": "ds-2",
            "resource_id": "res-2",
            "url": "https://example.govt.nz/file2.csv",
            "classification": "rights_restricted",
            "download_authorized": False,
        },
    ]

    mock_receipt = ObjectStoreReceipt(
        object_id="sha256:fake-sha256",
        sha256="fake-sha256",
        blake3="fake-blake3",
        byte_count=100,
        path=tmp_path / "objects" / "fake-sha256",
    )

    async def mock_capture(*_args: object, **_kwargs: object) -> object:
        class MockResult:
            receipt = mock_receipt
            status_code = 200
            content_type = "text/csv"
            elapsed_seconds = 0.1

        return MockResult()

    with patch("archive_govt_nz.global_capture.capture_url", side_effect=mock_capture):
        config = GlobalBatchCaptureConfig(
            max_workers=2, requests_per_second_per_host=10.0
        )
        report = asyncio.run(run_global_batch_capture(candidates, store, config))

    assert report["total_candidates"] == 2
    assert report["admitted_for_capture"] == 1
    assert report["skipped_tombstones"] == 1
    assert len(report["successful_captures"]) == 1
    assert report["successful_captures"][0]["resource_id"] == "res-1"
