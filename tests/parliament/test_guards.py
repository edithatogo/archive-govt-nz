"""Negative contracts for integrity, authority, source drift and run boundaries."""

import asyncio
import json
import sqlite3
from dataclasses import replace
from typing import TYPE_CHECKING, Any

import httpx
import pytest
from jsonschema import Draft202012Validator

from archive_govt_nz.parliament import pipeline
from archive_govt_nz.parliament.contracts import (
    SCHEMA,
    decision_for,
    validate_decisions,
    validate_manifest,
)
from archive_govt_nz.parliament.discovery import parse_listing
from archive_govt_nz.parliament.pipeline import Bounds, ParliamentArchive
from archive_govt_nz.parliament.reports import ReportQuery, parse_reports

from .test_pipeline import client, record
from .test_recovery import run_capture
from .test_reports import REPORT

if TYPE_CHECKING:
    from pathlib import Path

    from _pytest.monkeypatch import MonkeyPatch


def test_schema_and_malformed_decisions() -> None:
    """Neither malformed manifests nor whitespace-only authority can publish."""
    Draft202012Validator.check_schema(SCHEMA)
    with pytest.raises(ValueError, match="invalid_batch_manifest"):
        validate_manifest({})
    for value in ([], {"bad": {"basis": "missing identity"}}):
        with pytest.raises(ValueError, match="publication_decision_required"):
            validate_decisions(value)
    for evidence, basis in [
        ("https://www.parliament.nz/Copyright", " "),
        # Fictional negative fixture verifies credentials are rejected.
        ("https://user:secret@example.test/", "basis"),  # pragma: allowlist secret
        ("https://example.test/?token=secret", "basis"),
        ("https://example.test/#secret", "basis"),
    ]:
        with pytest.raises(ValueError, match="publication_decision_required"):
            decision_for(
                {
                    "example": {
                        "sha256": "a" * 64,
                        "basis": basis,
                        "evidence_url": evidence,
                    }
                },
                "example",
                "a" * 64,
            )


def test_candidate_collision_and_corrupt_capture_ledger(tmp_path: Path) -> None:
    """Immutable shards and persisted byte counts detect local corruption."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="test", evidence=b"synthetic")
    shard = next((tmp_path / "candidates").glob("*.json"))
    shard.write_text("corrupt")
    with pytest.raises(ValueError, match="immutable_batch_conflict"):
        archive.enqueue((record(),), partition="test", evidence=b"synthetic")
    run_capture(archive, client())
    with sqlite3.connect(tmp_path / "state.sqlite3") as connection:
        connection.execute("UPDATE captures SET size=999")
    with pytest.raises(ValueError, match="capture_size_mismatch"):
        archive.verify()


def test_package_selection_and_publication_status(tmp_path: Path) -> None:
    """A valid decision for an absent source cannot produce an empty batch."""
    archive = ParliamentArchive(tmp_path, delay=0)
    with pytest.raises(ValueError, match="no_captured_records"):
        archive.package(
            {
                "absent": {
                    "sha256": "a" * 64,
                    "basis": "fictional",
                    "evidence_url": "https://www.parliament.nz/Copyright",
                }
            }
        )
    with pytest.raises(ValueError, match="invalid_publication_status"):
        archive.note_publication("batch", "repo", "revision", "arbitrary")


def test_partial_record_defers_at_byte_boundary_then_resumes(tmp_path: Path) -> None:
    """Exhausting a normal run budget does not classify the source as failed."""
    archive = ParliamentArchive(tmp_path, delay=0)
    first = "https://selectcommittees.parliament.nz/download/a"
    second = "https://selectcommittees.parliament.nz/download/b"
    archive.enqueue(
        (replace(record(), url=first, kind="submission", attachments=(second,)),),
        partition="test",
        evidence=b"synthetic",
    )
    result = run_capture(archive, client(payload=b"12345"), Bounds(max_bytes=5))
    assert result["captured"] == 0
    assert result["failed"] == 0
    assert archive.summary()["pending"] == 1
    assert (
        run_capture(archive, client(payload=b"12345"), Bounds(max_bytes=5))["captured"]
        == 1
    )


@pytest.mark.parametrize("retry_after", ["Wed, 21 Oct 2030 07:28:00 GMT", "not-a-date"])
def test_retry_after_date_and_invalid_value(tmp_path: Path, retry_after: str) -> None:
    """Date-based and malformed rate limits both defer later requests safely."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue((record(),), partition="test", evidence=b"synthetic")

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(503, headers={"Retry-After": retry_after})

    run_capture(archive, httpx.AsyncClient(transport=httpx.MockTransport(handle)))
    archive.requeue("example")
    run_capture(archive, client())
    assert archive.summary()["last_error"] == "source_cooldown"


@pytest.mark.parametrize(
    ("status", "body", "reason"),
    [
        (503, b"busy", "report_search_failed"),
        (200, b"x" * (4 * 1024 * 1024 + 1), "report_response_oversize"),
    ],
)
def test_api_failure_does_not_advance_cursor(
    tmp_path: Path, status: int, body: bytes, reason: str
) -> None:
    """Unusable API responses cannot acknowledge any records or page cursor."""
    archive = ParliamentArchive(tmp_path, delay=0)

    def handle(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(status, content=body)

    async def run() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as http:
            await archive.reports(http, partition="test", query=ReportQuery())

    with pytest.raises(ValueError, match=reason):
        asyncio.run(run())
    assert archive.summary()["pending"] == 0


def test_worker_rejects_narrowed_cursor(tmp_path: Path) -> None:
    """An exhausted keyword pilot cannot stand in for the all-report history."""
    archive = ParliamentArchive(tmp_path, delay=0)
    with sqlite3.connect(tmp_path / "state.sqlite3") as connection:
        connection.execute(
            "INSERT INTO control VALUES(?,?)",
            (
                "reports:historical",
                json.dumps({"page": None, "keyword": "narrow pilot", "page_size": 10}),
            ),
        )

    async def run() -> None:
        async with client() as http:
            await archive.reports(http, partition="historical", require_unfiltered=True)

    with pytest.raises(ValueError, match="worker_cursor_scope_mismatch"):
        asyncio.run(run())


def test_report_eligibility_and_stage_bounds(
    tmp_path: Path, monkeypatch: MonkeyPatch
) -> None:
    """Only validated report candidates enter a bounded public batch."""
    archive = ParliamentArchive(tmp_path, delay=0)
    archive.enqueue(
        (record(), replace(record(), source_id="other", kind="submission")),
        partition="test",
        evidence=b"synthetic",
    )
    run_capture(archive, client(payload=b"%PDF-synthetic"))
    decisions = archive.report_decisions()
    assert len(decisions) == 1
    batch = archive.package(decisions)
    archive.note_publication(
        str(batch["batch"]), "edithatogo/archive-govt-nz-global", "revision", "verified"
    )
    assert archive.report_decisions() == {}
    archive.requeue("example", refresh=True)
    run_capture(archive, client(payload=b"not a pdf"))
    with pytest.raises(ValueError, match="report_payload_not_pdf"):
        archive.report_decisions()
    monkeypatch.setattr(pipeline, "MAX_BATCH_BYTES", 1)
    assert archive.report_decisions() == {}


def test_duplicate_source_metadata_and_empty_listing() -> None:
    """Conflicting duplicate identities require reconciliation, not last-wins loss."""
    first = '<tr><td><a href="/document/example/">First</a></td></tr>'
    second = first.replace("First", "Different")
    with pytest.raises(ValueError, match="conflicting_source_identity"):
        parse_listing(
            "Displaying 1-2 of 2" + first + second,
            "https://www3.parliament.nz/en/pb/sc/",
        )
    assert not parse_listing(
        "Displaying 0-0 of 0<tr><td>Empty</td></tr>",
        "https://www3.parliament.nz/en/pb/sc/",
    ).records
    assert (
        parse_listing(
            "Displaying 1-1 of 1" + first, "https://www3.parliament.nz/en/pb/sc/"
        )
        .records[0]
        .kind
        == "unknown"
    )


@pytest.mark.parametrize(
    "kwargs",
    [{"page": 0}, {"page_size": 0}, {"page_size": 101}, {"keyword": "x" * 201}],
)
def test_invalid_report_bounds(kwargs: dict[str, Any]) -> None:
    """Invalid API bounds cannot silently become server defaults."""
    with pytest.raises(ValueError, match="invalid_report_query"):
        ReportQuery(**kwargs)


def test_duplicate_report_ids_are_not_unique_coverage() -> None:
    """Duplicate source IDs in a full API page invalidate that page's accounting."""
    with pytest.raises(ValueError, match="report_contract_mismatch"):
        parse_reports(
            {"results": [REPORT, REPORT], "page": 1, "pageSize": 2, "totalResults": 2},
            ReportQuery(page_size=2),
        )
