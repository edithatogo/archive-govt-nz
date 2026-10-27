"""Synthetic crash, limit, robots and publication integrity contracts."""

import asyncio
import hashlib
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.parliament.discovery import Record
from archive_govt_nz.parliament.pipeline import Bounds, ParliamentArchive

if TYPE_CHECKING:
    from pathlib import Path

URL = "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/example"


def record() -> Record:
    """Return a fictional report record."""
    return Record(
        "example",
        URL,
        "Example",
        "report",
        "Example Bill",
        "Committee",
        "2026-10-01",
        (URL,),
    )


def client(
    robots: str = "User-agent: *\nAllow: /", payload: bytes = b"example"
) -> httpx.AsyncClient:
    """Return deterministic HTTP transport without production credentials."""

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text=robots)
        return httpx.Response(
            200, content=payload, headers={"content-type": "application/pdf"}
        )

    return httpx.AsyncClient(transport=httpx.MockTransport(handle))


def test_durable_queue_idempotency_and_lease(tmp_path: Path) -> None:
    """Repeated candidates do not reset complete work; writers are fenced."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="historical", evidence=b"synthetic")
    archive.enqueue((record(),), partition="historical", evidence=b"synthetic")
    assert archive.summary()["pending"] == 1
    with (
        archive.lease(),
        pytest.raises(ValueError, match="writer_busy"),
        ParliamentArchive(tmp_path).lease(),
    ):
        pass
    assert ParliamentArchive(tmp_path).summary()["pending"] == 1


def test_capture_bounds_and_resume(tmp_path: Path) -> None:
    """Capture promotes verified objects and persists its state independently."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="historical", evidence=b"synthetic")

    async def run() -> dict[str, object]:
        async with client() as http:
            return await archive.capture(http, Bounds(max_records=1, max_bytes=100))

    result = asyncio.run(run())
    assert result["captured"] == 1
    assert archive.summary()["captured"] == 1
    assert ParliamentArchive(tmp_path).summary()["pending"] == 0
    assert archive.verify()["verified"] == 1


def test_robots_denial_blocks_capture(tmp_path: Path) -> None:
    """A denial cannot be worked around with a different crawler identity."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="historical", evidence=b"synthetic")

    async def run() -> dict[str, object]:
        async with client("User-agent: *\nDisallow: /") as http:
            return await archive.capture(http, Bounds())

    result = asyncio.run(run())
    assert result["captured"] == 0
    assert result["failed"] == 1
    assert archive.summary()["last_error"] == "robots_denied"


def test_size_limit_does_not_promote_partial_object(tmp_path: Path) -> None:
    """Too-large bodies remain failures and cannot count as captures."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="historical", evidence=b"synthetic")

    async def run() -> dict[str, object]:
        async with client(payload=b"x" * 20) as http:
            return await archive.capture(http, Bounds(max_bytes=10))

    result = asyncio.run(run())
    assert result["captured"] == 0
    assert archive.summary()["captured"] == 0


def test_publication_requires_hash_bound_decision(tmp_path: Path) -> None:
    """No payload is published merely because it is publicly downloadable."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="historical", evidence=b"synthetic")

    async def run() -> None:
        async with client() as http:
            await archive.capture(http, Bounds())

    asyncio.run(run())
    with pytest.raises(ValueError, match="publication_decision_required"):
        archive.package({})
    digest = hashlib.sha256(b"example").hexdigest()
    package = archive.package(
        {
            "example": {
                "sha256": digest,
                "basis": "Public-domain select committee report",
                "evidence_url": "https://www3.parliament.nz/en/footer/copyright/",
            }
        }
    )
    assert package["object_count"] == 1
    assert archive.summary()["published"] == 0
