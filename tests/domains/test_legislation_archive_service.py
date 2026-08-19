"""Comprehensive tests for bounded, resumable LegislationArchiveService."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.domains.legislation.api import NZLegislationApiClient
from archive_govt_nz.domains.legislation.checkpoints import (
    LegislationCheckpointCorruptError,
    LegislationCheckpointManager,
)
from archive_govt_nz.domains.legislation.corpus import (
    ExpressionTarget,
    LegislationArchiveService,
    ManifestationTarget,
    WorkTarget,
)
from archive_govt_nz.domains.legislation.models import (
    LegislationType,
    VersionStatus,
)
from archive_govt_nz.object_store import ContentAddressedStore

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.anyio
async def test_first_sync_and_repeated_no_change(tmp_path: Path) -> None:
    """Validate first sync cold-start and repeated idempotent no-change sync."""
    cas_dir = tmp_path / "cas"
    chk_path = tmp_path / "checkpoints" / "weekly.json"
    store = ContentAddressedStore(cas_dir)

    xml_content = (
        b'<?xml version="1.0" encoding="utf-8"?>\n'
        b'<act id="DLM100" status="in-force">\n'
        b"  <title>Ombudsmen Act 1975</title>\n"
        b'  <section id="DLM101"><heading>Title</heading>'
        b"<text>An Act...</text></section>\n"
        b"</act>"
    )

    def handler(req: httpx.Request) -> httpx.Response:
        if "whole.xml" in req.url.path:
            return httpx.Response(
                200,
                headers={"content-type": "application/xml"},
                content=xml_content,
            )
        return httpx.Response(404, content=b"Not Found")

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(async_client=async_client)
    service = LegislationArchiveService(store=store, api_client=api_client)

    target = WorkTarget(
        work_id="act-1975-9",
        title="Ombudsmen Act 1975",
        canonical_uri="https://www.legislation.govt.nz/act/public/1975/0009/latest/whole.xml",
        expression_targets=[
            ExpressionTarget(
                version_date="2026-01-01",
                manifestations=[
                    ManifestationTarget(
                        target_url="https://www.legislation.govt.nz/act/public/1975/0009/latest/whole.xml",
                        media_type="application/xml",
                    )
                ],
            )
        ],
    )

    # 1. First Sync
    res1 = await service.sync_works(
        targets=[target],
        checkpoint_path=chk_path,
        batch_id="batch-2026-01",
    )

    assert res1.status == "success"
    assert res1.works_attempted == 1
    assert res1.works_synced == 1
    assert res1.records_preserved == 1
    assert len(res1.records) == 1
    assert res1.records[0].legislation_type == LegislationType.ACT
    assert res1.records[0].status == VersionStatus.IN_FORCE
    assert res1.manifest["total_records"] == 1
    assert res1.coverage.coverage_percent == 100.0
    assert chk_path.is_file()
    assert res1.checkpoint is not None
    assert res1.checkpoint["last_updated"] is not None
    assert res1.checkpoint["processed_work_ids"] == ["act-1975-9"]

    # 2. Repeated No-Change Sync
    res2 = await service.sync_works(
        targets=[target],
        checkpoint_path=chk_path,
        batch_id="batch-2026-01",
    )

    assert res2.status == "no_change"
    assert res2.works_attempted == 1
    assert res2.works_synced == 0
    assert res2.records_preserved == 0
    assert len(res2.records) == 0


@pytest.mark.anyio
async def test_end_to_end_multi_expression_fixture(tmp_path: Path) -> None:
    """Test one work with two expressions and XML/HTML manifestations."""
    cas_dir = tmp_path / "cas"
    chk_path = tmp_path / "checkpoints" / "e2e_chk.json"
    store = ContentAddressedStore(cas_dir)

    exp1_xml = (
        b'<act id="DLM1" status="repealed"><title>Historic Act</title>'
        b'<section id="s1"><text>Old</text></section></act>'
    )
    exp1_html = (
        b"<html><head><title>Historic Act</title></head>"
        b"<body><h1>Historic Act</h1><p>Old</p></body></html>"
    )
    exp2_xml = (
        b'<act id="DLM1" status="in-force"><title>Historic Act</title>'
        b'<section id="s1"><text>New</text></section></act>'
    )
    exp2_html = (
        b"<html><head><title>Historic Act</title></head>"
        b"<body><h1>Historic Act</h1><p>New</p></body></html>"
    )

    def handler(req: httpx.Request) -> httpx.Response:
        path = req.url.path
        if "/v1/whole.xml" in path:
            return httpx.Response(
                200,
                headers={"content-type": "application/xml"},
                content=exp1_xml,
            )
        if "/v1/whole.html" in path:
            return httpx.Response(
                200, headers={"content-type": "text/html"}, content=exp1_html
            )
        if "/v2/whole.xml" in path:
            return httpx.Response(
                200,
                headers={"content-type": "application/xml"},
                content=exp2_xml,
            )
        if "/v2/whole.html" in path:
            return httpx.Response(
                200, headers={"content-type": "text/html"}, content=exp2_html
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(async_client=async_client)
    service = LegislationArchiveService(store=store, api_client=api_client)

    target = WorkTarget(
        work_id="act-1990-1",
        title="Historic Act",
        canonical_uri="https://example.com/act/1990/1",
        expression_targets=[
            ExpressionTarget(
                version_date="1990-01-01",
                version_label="1990-initial",
                manifestations=[
                    ManifestationTarget(
                        target_url="https://example.com/act/1990/1/v1/whole.xml",
                        media_type="application/xml",
                    ),
                    ManifestationTarget(
                        target_url="https://example.com/act/1990/1/v1/whole.html",
                        media_type="text/html",
                    ),
                ],
            ),
            ExpressionTarget(
                version_date="2026-01-01",
                version_label="2026-reprint",
                manifestations=[
                    ManifestationTarget(
                        target_url="https://example.com/act/1990/1/v2/whole.xml",
                        media_type="application/xml",
                    ),
                    ManifestationTarget(
                        target_url="https://example.com/act/1990/1/v2/whole.html",
                        media_type="text/html",
                    ),
                ],
            ),
        ],
    )

    res = await service.sync_works(
        targets=[target],
        checkpoint_path=chk_path,
        batch_id="batch-e2e",
    )

    assert res.status == "success"
    assert res.records_preserved == 4
    assert len(res.records) == 4
    assert res.coverage.xml_manifestations_count == 2
    assert res.coverage.html_fallback_count == 2

    statuses = [r.status for r in res.records]
    assert VersionStatus.REPEALED in statuses
    assert VersionStatus.IN_FORCE in statuses

    rerun = await service.sync_works(
        targets=[target],
        checkpoint_path=chk_path,
        batch_id="batch-e2e",
    )
    assert rerun.status == "no_change"
    assert rerun.records_preserved == 0


@pytest.mark.anyio
async def test_resumption_after_interruption(tmp_path: Path) -> None:
    """Validate resuming sync across multi-work batch skips already completed works."""
    cas_dir = tmp_path / "cas"
    chk_path = tmp_path / "checkpoints" / "resume_chk.json"
    store = ContentAddressedStore(cas_dir)

    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/xml"},
            content=f"<act><title>{req.url.path}</title></act>".encode(),
        )

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(async_client=async_client)
    service = LegislationArchiveService(store=store, api_client=api_client)

    target1 = WorkTarget(
        work_id="act-1",
        title="Act One",
        expression_targets=[
            ExpressionTarget(
                manifestations=[
                    ManifestationTarget(target_url="https://example.com/act1/whole.xml")
                ]
            )
        ],
    )
    target2 = WorkTarget(
        work_id="act-2",
        title="Act Two",
        expression_targets=[
            ExpressionTarget(
                manifestations=[
                    ManifestationTarget(target_url="https://example.com/act2/whole.xml")
                ]
            )
        ],
    )

    res1 = await service.sync_works(
        targets=[target1],
        checkpoint_path=chk_path,
    )
    assert res1.status == "success"
    assert res1.works_synced == 1

    res2 = await service.sync_works(
        targets=[target1, target2],
        checkpoint_path=chk_path,
    )
    assert res2.status == "success"
    assert res2.works_synced == 1
    assert res2.records_preserved == 1
    assert res2.records[0].work_id == "act-2"
    assert res2.checkpoint is not None
    assert res2.checkpoint["processed_work_ids"] == ["act-1", "act-2"]


@pytest.mark.anyio
async def test_fail_fast_no_checkpoint_promotion(tmp_path: Path) -> None:
    """Validate failure under fail_fast discards staging and halts promotion."""
    cas_dir = tmp_path / "cas"
    chk_path = tmp_path / "checkpoints" / "fail_chk.json"
    store = ContentAddressedStore(cas_dir)

    def handler(_req: httpx.Request) -> httpx.Response:
        return httpx.Response(500, content=b"Server Error")

    transport = httpx.MockTransport(handler)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(async_client=async_client)
    service = LegislationArchiveService(store=store, api_client=api_client)

    target = WorkTarget(
        work_id="act-failing",
        title="Failing Act",
        expression_targets=[
            ExpressionTarget(
                manifestations=[
                    ManifestationTarget(target_url="https://example.com/fail/whole.xml")
                ]
            )
        ],
    )

    res = await service.sync_works(
        targets=[target],
        checkpoint_path=chk_path,
        fail_fast=True,
    )

    assert res.status == "failed"
    assert len(res.errors) > 0
    assert not chk_path.is_file()
    assert not chk_path.with_suffix(".staging.tmp").is_file()


@pytest.mark.anyio
async def test_corrupt_checkpoint_detection_and_non_dict(
    tmp_path: Path,
) -> None:
    """Corrupt JSON or non-dict in checkpoint must be detected cleanly."""
    chk_path = tmp_path / "corrupt.json"
    chk_path.write_text("{ unclosed invalid json", encoding="utf-8")

    mgr = LegislationCheckpointManager(chk_path)
    with pytest.raises(LegislationCheckpointCorruptError):
        mgr.load(strict=True)

    chk_path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(LegislationCheckpointCorruptError):
        mgr.load(strict=True)
    assert mgr.load(strict=False)["total_records_preserved"] == 0

    non_existent = LegislationCheckpointManager(tmp_path / "non_existent.json")
    init_state = non_existent.load()
    assert init_state["last_updated"] is None
    assert init_state["total_records_preserved"] == 0

    with pytest.raises(FileNotFoundError):
        non_existent.promote()

    # discard_staging on non-existent file is a no-op
    non_existent.discard_staging()

    # discard_staging when file exists removes it
    stg_path = non_existent.stage(["b1"], ["w1"], 1)
    assert stg_path.is_file()
    non_existent.discard_staging()
    assert not stg_path.is_file()


@pytest.mark.anyio
async def test_target_resolution_and_partial_sync(tmp_path: Path) -> None:
    """Validate target resolution by work IDs, search terms, and partial failures."""
    cas_dir = tmp_path / "cas"
    chk_path = tmp_path / "checkpoints" / "partial.json"
    store = ContentAddressedStore(cas_dir)

    def handler(req: httpx.Request) -> httpx.Response:
        path = req.url.path
        if "works" in path:
            return httpx.Response(
                200,
                json=[
                    {"work_id": "act-disc-1", "title": "Discovered Act 1"},
                    {"work_id": "act-disc-2", "title": "Discovered Act 2"},
                ],
            )
        if "act-disc-1" in path or "act-work-1" in path:
            return httpx.Response(
                200,
                headers={"content-type": "application/xml"},
                content=b"<act><title>OK Act</title></act>",
            )
        if "act-fail" in path:
            return httpx.Response(500, content=b"Server Error")
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    async_client = httpx.AsyncClient(transport=transport)
    api_client = NZLegislationApiClient(client=client, async_client=async_client)
    chk_mgr = LegislationCheckpointManager(chk_path)
    service = LegislationArchiveService(
        store=store, api_client=api_client, checkpoint_mgr=chk_mgr
    )

    # 1. Resolve targets via work_ids
    res_work_ids = await service.sync_works(
        work_ids=["act-work-1"],
        max_works=5,
    )
    assert res_work_ids.status == "success"
    assert res_work_ids.records_preserved == 1

    # 2. Resolve targets via search_terms
    res_search = await service.sync_works(
        search_terms=["finance"],
        force_resync=True,
        max_works=1,
    )
    assert res_search.status == "success"
    assert res_search.works_attempted == 1

    # 3. Partial failure (1 success, 1 failure with fail_fast=False)
    partial_target_ok = WorkTarget(
        work_id="act-work-1",
        title="OK Act",
        expression_targets=[
            ExpressionTarget(
                manifestations=[
                    ManifestationTarget(
                        target_url="https://example.com/act-work-1/whole.xml"
                    )
                ]
            )
        ],
    )
    partial_target_fail = WorkTarget(
        work_id="act-fail",
        title="Fail Act",
        expression_targets=[
            ExpressionTarget(
                manifestations=[
                    ManifestationTarget(
                        target_url="https://example.com/act-fail/whole.xml"
                    )
                ]
            )
        ],
    )

    res_partial = await service.sync_works(
        targets=[partial_target_ok, partial_target_fail],
        force_resync=True,
        fail_fast=False,
    )
    assert res_partial.status == "partial"
    assert res_partial.records_preserved == 1
    assert len(res_partial.errors) == 1

    # 4. Total failure (0 preserved records)
    res_all_failed = await service.sync_works(
        targets=[partial_target_fail],
        force_resync=True,
        fail_fast=False,
    )
    assert res_all_failed.status == "failed"
    assert res_all_failed.records_preserved == 0

    # 5. Empty targets
    res_empty = await service.sync_works()
    assert res_empty.status == "success"
    assert res_empty.works_attempted == 0

    # 6. No checkpoint manager configured
    no_chk_service = LegislationArchiveService(store=store, api_client=api_client)
    res_no_chk = await no_chk_service.sync_works(
        targets=[partial_target_ok],
        force_resync=True,
    )
    assert res_no_chk.status == "success"
    assert res_no_chk.checkpoint == {}
