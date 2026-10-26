"""Failure contracts for state, source changes, limits and drift."""

import asyncio
import hashlib
import json
import subprocess
import sys
from contextlib import suppress
from dataclasses import replace
from pathlib import Path
from typing import Any

import httpx
import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.parliament.discovery import (
    attachment_links,
    parse_listing,
    safe_url,
)
from archive_govt_nz.parliament.pipeline import Bounds, ParliamentArchive

from .test_pipeline import URL, client, record


def run_capture(
    archive: ParliamentArchive, http: httpx.AsyncClient, bounds: Bounds | None = None
) -> dict[str, object]:
    """Close each fictional HTTP client after its single bounded operation."""

    async def run() -> dict[str, object]:
        async with http:
            return await archive.capture(http, bounds or Bounds())

    return asyncio.run(run())


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_records": 0},
        {"max_bytes": 0},
        {"max_seconds": 0},
        {"max_file_bytes": 0},
        {"max_spool_bytes": 0},
    ],
)
def test_nonpositive_bounds(kwargs: dict[str, int]) -> None:
    """Every run dimension must have a positive limit."""
    with pytest.raises(ValueError, match="invalid_bounds"):
        Bounds(**kwargs)


def test_invalid_delay(tmp_path: Path) -> None:
    """Invalid rate settings fail before creating operational state."""
    with pytest.raises(ValueError, match="invalid_delay"):
        ParliamentArchive(tmp_path, delay=-1)


def test_metadata_change_and_refresh_preserve_versions(tmp_path: Path) -> None:
    """Changed metadata and explicit refresh create new observations."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="history", evidence=b"first")
    run_capture(archive, client(payload=b"first"))
    archive.enqueue(
        (replace(record(), title="Updated"),), partition="history", evidence=b"second"
    )
    run_capture(archive, client(payload=b"second"))
    archive.requeue("example", refresh=True)
    run_capture(archive, client(payload=b"third"))
    assert archive.verify()["verified"] == 3
    decisions = {
        "example:" + hashlib.sha256(payload).hexdigest(): {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "basis": "Synthetic permission",
            "evidence_url": "https://example.org/permission",
        }
        for payload in (b"first", b"second", b"third")
    }
    staged = archive.package(decisions)
    manifest = json.loads((Path(str(staged["path"])) / "manifest.json").read_text())
    titles = {
        row["sha256"]: json.loads(row["record"])["title"] for row in manifest["records"]
    }
    assert titles[hashlib.sha256(b"first").hexdigest()] == "Example"
    assert titles[hashlib.sha256(b"second").hexdigest()] == "Updated"
    with pytest.raises(ValueError, match="unknown_source_id"):
        archive.requeue("absent")


def test_retry_skips_verified_partial_segment(tmp_path: Path) -> None:
    """An incomplete record resumes from preserved HTML and its attachment links."""
    archive = ParliamentArchive(tmp_path, delay=0)
    source = "https://selectcommittees.parliament.nz/v/6/example"
    archive.enqueue(
        (replace(record(), url=source, kind="submission", attachments=()),),
        partition="history",
        evidence=b"first",
    )
    attempts: list[str] = []
    fail = True

    def handle(request: httpx.Request) -> httpx.Response:
        attempts.append(request.url.path)
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        if request.url.path.startswith("/v/"):
            return httpx.Response(
                200,
                text=f'<a href="{URL}">Original</a>',
                headers={"content-type": "text/html"},
            )
        return httpx.Response(500 if fail else 200, content=b"original")

    run_capture(archive, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
    assert archive.summary()["failed"] == 1
    archive.requeue("example")
    fail = False
    result = run_capture(
        archive, httpx.AsyncClient(transport=httpx.MockTransport(handle))
    )
    assert result["captured"] == 1
    assert attempts.count("/v/6/example") == 1
    assert archive.verify()["verified"] == 2


@pytest.mark.parametrize(
    ("robots", "status", "error"),
    [
        ("User-agent: *\nDisallow: /", 200, "robots_denied"),
        ("", 404, "robots_unavailable"),
        ("x" * 131073, 200, "robots_oversize"),
    ],
    ids=["denied", "unavailable", "oversize"],
)
def test_robots_fail_closed(
    tmp_path: Path, robots: str, status: int, error: str
) -> None:
    """Unknown, denied and oversized crawler policies never admit payload requests."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="history", evidence=b"first")
    requested: list[str] = []

    def handle(request: httpx.Request) -> httpx.Response:
        requested.append(request.url.path)
        return httpx.Response(status, text=robots)

    run_capture(archive, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
    assert requested == ["/robots.txt"]
    assert archive.summary()["last_error"] == error


def test_retry_after_persists_without_automatic_retry(tmp_path: Path) -> None:
    """Rate limiting fences later runs and does not retry the native request."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="history", evidence=b"first")

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(429, headers={"Retry-After": "3600"})

    run_capture(archive, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
    archive.requeue("example")
    run_capture(archive, client())
    assert archive.summary()["last_error"] == "source_cooldown"


@pytest.mark.parametrize("limit", [{"max_spool_bytes": 1}, {"max_seconds": 0.000001}])
def test_run_bounds_do_not_acknowledge_unprocessed_record(
    tmp_path: Path, limit: dict[str, Any]
) -> None:
    """No record is marked complete solely because the run budget expired."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="history", evidence=b"first")
    with suppress(TimeoutError):
        run_capture(archive, client(), Bounds(**limit))
    assert archive.summary()["captured"] == 0
    assert archive.summary()["pending"] == 1


def test_html_attachment_error_is_not_an_original(tmp_path: Path) -> None:
    """A 200 HTML login/error page cannot pass as a submission attachment."""
    archive = ParliamentArchive(tmp_path, delay=0)
    source = "https://selectcommittees.parliament.nz/v/6/example"
    archive.enqueue(
        (replace(record(), url=source),), partition="history", evidence=b"first"
    )

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(200, text="error", headers={"content-type": "text/html"})

    run_capture(archive, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
    assert archive.summary()["captured"] == 0
    assert archive.summary()["last_error"] == "attachment_contract_unqualified"


def test_discovery_checkpoint_and_app_shell(tmp_path: Path) -> None:
    """Only parsed/persisted candidates can advance the discovery checkpoint."""
    archive = ParliamentArchive(tmp_path, delay=0)
    html = "Displaying 0-0 of 0<table></table>"

    async def discover() -> dict[str, object]:
        async with client(payload=html.encode()) as http:
            return await archive.discover(
                http,
                "https://selectcommittees.parliament.nz/reports",
                partition="recent",
            )

    assert asyncio.run(discover())["discovered"] == 0
    assert list((tmp_path / "candidates").glob("*.json"))
    html = "Loading..."
    with pytest.raises(ValueError, match="unrecognized_listing"):
        asyncio.run(discover())


def test_missing_next_page_is_not_exhaustion() -> None:
    """A lost pagination selector cannot truncate a partition silently."""
    with pytest.raises(ValueError, match="pagination_contract_unqualified"):
        parse_listing(
            'Displaying 1-1 of 2<tr><td><a href="/v/6/example">Example</a></td></tr>',
            "https://selectcommittees.parliament.nz/reports",
        )


def test_attachment_host_allowlist() -> None:
    """Links to unsupported external attachment hosts need a qualified route."""
    with pytest.raises(ValueError, match="unsafe_parliament_url"):
        attachment_links('<a href="https://evil.test/file.pdf">file</a>', URL)
    assert attachment_links('<a href="/download/file">file</a>', URL) == (
        "https://selectcommittees.parliament.nz/download/file",
    )


@given(
    st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=1, max_size=30)
)
def test_url_identity_drops_fragment_only(name: str) -> None:
    """Canonicalization preserves source paths while discarding fragments."""
    url = "https://selectcommittees.parliament.nz/v/" + name
    assert safe_url(url + "#fragment") == url


def test_crashed_writer_is_recovered_without_deleting_lock(tmp_path: Path) -> None:
    """OS lock release permits recovery while stale SQL ownership is retained."""
    script = (
        "import os,sys; from pathlib import Path; "
        "from archive_govt_nz.parliament.pipeline import ParliamentArchive; "
        "a=ParliamentArchive(Path(sys.argv[1])); "
        "lease=a.lease(); lease.__enter__(); os._exit(0)"
    )
    result = subprocess.run(
        [sys.executable, "-c", script, str(tmp_path)],
        check=False,
        timeout=15,
    )
    assert result.returncode == 0
    with ParliamentArchive(tmp_path).lease():
        assert (tmp_path / "writer.lock").exists()
