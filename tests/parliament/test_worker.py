"""A complete fictional report stream proves bounded publication and resume."""

import asyncio
import json
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.parliament import worker
from archive_govt_nz.parliament.pipeline import Bounds, ParliamentArchive
from archive_govt_nz.parliament.publication import publish_batch
from archive_govt_nz.parliament.reports import ReportQuery

from .test_publication import Hub
from .test_reports import REPORT

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch


def test_stream_publishes_once_then_reconciles(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """A later observation of unchanged report data does not upload again."""
    original = httpx.AsyncClient

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        if request.url.path == "/api/data/search":
            return httpx.Response(
                200,
                json={"results": [REPORT], "page": 1, "pageSize": 1, "totalResults": 1},
            )
        return httpx.Response(
            200,
            content=b"%PDF-synthetic-original",
            headers={"content-type": "application/pdf"},
        )

    monkeypatch.setattr(
        worker.httpx,
        "AsyncClient",
        lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs),
    )
    monkeypatch.setattr(
        worker, "ParliamentArchive", lambda root: ParliamentArchive(root, delay=0)
    )
    hub = Hub()
    monkeypatch.setattr(
        worker,
        "publish_batch",
        lambda archive, batch: publish_batch(archive, batch, hub=hub),
    )
    first = worker.run_reports(tmp_path, mode="recent", bounds=Bounds(max_records=10))
    assert first["captured"] == 1
    publication = first["publication"]
    assert isinstance(publication, dict)
    assert publication["status"] == "verified"
    second = worker.run_reports(tmp_path, mode="recent", bounds=Bounds(max_records=10))
    assert second["captured"] == 0
    assert "publication" not in second
    assert hub.commits == 1


def test_worker_rejects_partial_page_budget(tmp_path: Path) -> None:
    """Fixed historical page strides cannot silently change with a smaller budget."""
    archive = ParliamentArchive(tmp_path, delay=0)
    with pytest.raises(ValueError, match="worker_record_bound_requires_complete_pages"):
        asyncio.run(
            worker.collect_reports(archive, "historical", Bounds(max_records=1))
        )


def test_metadata_only_original_response_is_publicly_packaged(tmp_path: Path) -> None:
    """A missing document yields a clearly labelled, byte-exact catalogue snapshot."""
    original = httpx.AsyncClient
    raw = (
        "  "
        + json.dumps(
            {
                "results": [
                    {
                        **REPORT,
                        "attachmentId": "",
                        "publicationDate": "0001-01-01T00:00:00Z",
                    }
                ],
                "page": 1,
                "pageSize": 1,
                "totalResults": 1,
            }
        )
        + "\n"
    ).encode()

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        assert request.url.path == "/api/data/search"
        return httpx.Response(200, content=raw)

    archive = ParliamentArchive(tmp_path, delay=0)

    async def run() -> None:
        async with original(transport=httpx.MockTransport(handle)) as http:
            await archive.reports(
                http, partition="tail", query=ReportQuery(page_size=1)
            )
            assert (await archive.capture(http, Bounds()))["captured"] == 0

    asyncio.run(run())
    assert archive.summary()["metadata_only"] == 1
    batch = archive.package(archive.report_decisions())
    root = tmp_path / "batches" / str(batch["batch"])
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["records"][0]["representation"] == "source_metadata"
    assert manifest["records"][0]["capture_state"] == "metadata_only"
    assert (root / "objects" / manifest["records"][0]["sha256"]).read_bytes() == raw
    hub = Hub()
    assert publish_batch(archive, str(batch["batch"]), hub=hub)["status"] == "verified"
