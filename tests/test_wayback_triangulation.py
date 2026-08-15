"""Tests for automated Wayback Machine CDX triangulation and recovery."""
# pyright: reportUnknownVariableType=false, reportUnknownMemberType=false, reportUnknownArgumentType=false

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, patch

import httpx

from archive_govt_nz.object_store import ContentAddressedStore, ObjectStoreReceipt
from archive_govt_nz.wayback_triangulation import (
    WaybackSnapshot,
    query_wayback_cdx,
    recover_broken_resource,
    run_wayback_triangulation,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_query_wayback_cdx_success() -> None:
    """CDX query returns formatted snapshot when 200 OK record found."""
    mock_response = httpx.Response(
        status_code=200,
        json=[
            [
                "urlkey",
                "timestamp",
                "original",
                "mimetype",
                "statuscode",
                "digest",
                "length",
            ],
            [
                "nz,govt,stats)/file.csv",
                "20240101120000",
                "https://stats.govt.nz/file.csv",
                "text/csv",
                "200",
                "DIGEST",
                "1024",
            ],
        ],
        request=httpx.Request("GET", "https://web.archive.org/cdx/search/cdx"),
    )

    with patch(
        "httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response
    ):
        snapshot = asyncio.run(query_wayback_cdx("https://stats.govt.nz/file.csv"))

    assert snapshot is not None
    assert snapshot.timestamp == "20240101120000"
    assert snapshot.original_url == "https://stats.govt.nz/file.csv"
    assert (
        snapshot.playback_url
        == "https://web.archive.org/web/20240101120000id_/https://stats.govt.nz/file.csv"
    )


def test_query_wayback_cdx_not_found() -> None:
    """CDX query returns None when no archived snapshot exists."""
    mock_response = httpx.Response(
        status_code=200,
        json=[
            [
                "urlkey",
                "timestamp",
                "original",
                "mimetype",
                "statuscode",
                "digest",
                "length",
            ],
        ],
        request=httpx.Request("GET", "https://web.archive.org/cdx/search/cdx"),
    )

    with patch(
        "httpx.AsyncClient.get", new_callable=AsyncMock, return_value=mock_response
    ):
        snapshot = asyncio.run(
            query_wayback_cdx("https://stats.govt.nz/nonexistent.csv")
        )

    assert snapshot is None


def test_run_wayback_triangulation(tmp_path: Path) -> None:
    """Triangulation recovers archived items and skips missing ones."""
    store = ContentAddressedStore(tmp_path / "objects")
    broken_urls = [
        {
            "resource_id": "res-1",
            "dataset_id": "ds-1",
            "url": "https://stats.govt.nz/historical.csv",
        },
        {
            "resource_id": "res-2",
            "dataset_id": "ds-2",
            "url": "https://stats.govt.nz/never-archived.csv",
        },
    ]

    async def mock_recover(
        item: dict[str, object], *_args: object, **_kwargs: object
    ) -> dict[str, object]:
        if item.get("resource_id") == "res-1":
            return {
                "resource_id": "res-1",
                "dataset_id": "ds-1",
                "original_url": "https://stats.govt.nz/historical.csv",
                "recovery_status": "recovered",
                "recovered": True,
                "source": "wayback_machine",
                "snapshot_timestamp": "20240101120000",
                "snapshot_url": "https://web.archive.org/web/20240101120000id_/https://stats.govt.nz/historical.csv",
                "object_id": "sha256:wayback123",
                "sha256": "wayback123",
                "blake3": "blake123",
                "byte_count": 2048,
            }
        return {
            "resource_id": "res-2",
            "dataset_id": "ds-2",
            "original_url": "https://stats.govt.nz/never-archived.csv",
            "recovery_status": "not_in_archive",
            "recovered": False,
        }

    with patch(
        "archive_govt_nz.wayback_triangulation.recover_broken_resource",
        side_effect=mock_recover,
    ):
        receipt = asyncio.run(
            run_wayback_triangulation(broken_urls, store, concurrency=2)
        )

    assert receipt["schema_version"] == "archive-govt-nz.wayback-recovery-receipt/v1"
    assert receipt["total_broken_evaluated"] == 2
    assert receipt["recovered_count"] == 1
    assert receipt["unrecovered_count"] == 1
    assert receipt["records"][0]["recovered"] is True
    assert receipt["records"][1]["recovered"] is False


def test_recover_broken_resource_direct(tmp_path: Path) -> None:
    """recover_broken_resource exercises hit, miss, and capture errors."""
    store = ContentAddressedStore(tmp_path / "objects")

    # 1. Miss
    with patch(
        "archive_govt_nz.wayback_triangulation.query_wayback_cdx",
        new_callable=AsyncMock,
        return_value=None,
    ):
        res_miss = asyncio.run(
            recover_broken_resource({"url": "https://test.nz/miss.csv"}, store)
        )
        assert res_miss["recovered"] is False
        assert res_miss["recovery_status"] == "not_in_archive"

    # 2. Hit
    fake_snapshot = WaybackSnapshot(
        original_url="https://test.nz/hit.csv",
        timestamp="20240101000000",
        status_code="200",
        mimetype="text/csv",
        playback_url="https://web.archive.org/web/20240101000000id_/https://test.nz/hit.csv",
    )
    mock_receipt = ObjectStoreReceipt(
        object_id="sha256:hit123",
        sha256="hit123",
        blake3="blake123",
        byte_count=512,
        path=tmp_path / "objects" / "hit123",
    )

    class MockResult:
        receipt = mock_receipt

    with (
        patch(
            "archive_govt_nz.wayback_triangulation.query_wayback_cdx",
            new_callable=AsyncMock,
            return_value=fake_snapshot,
        ),
        patch(
            "archive_govt_nz.wayback_triangulation.capture_url",
            new_callable=AsyncMock,
            return_value=MockResult(),
        ),
    ):
        res_hit = asyncio.run(
            recover_broken_resource(
                {"url": "https://test.nz/hit.csv", "resource_id": "r-1"}, store
            )
        )
        assert res_hit["recovered"] is True
        assert res_hit["sha256"] == "hit123"

    # 3. Capture Failure
    with (
        patch(
            "archive_govt_nz.wayback_triangulation.query_wayback_cdx",
            new_callable=AsyncMock,
            return_value=fake_snapshot,
        ),
        patch(
            "archive_govt_nz.wayback_triangulation.capture_url",
            new_callable=AsyncMock,
            side_effect=OSError("network drop"),
        ),
    ):
        res_err = asyncio.run(
            recover_broken_resource({"url": "https://test.nz/err.csv"}, store)
        )
        assert res_err["recovered"] is False
        assert "capture_failed" in res_err["recovery_status"]
