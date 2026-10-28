"""Reviewed exclusions preserve failures without granting publication or retry."""

from __future__ import annotations

import asyncio
import hashlib
import json
from typing import TYPE_CHECKING

import httpx
import pytest

from archive_govt_nz.parliament.hosted_state import (
    export_state,
    import_state,
    validate_state,
)
from archive_govt_nz.parliament.pipeline import Bounds
from archive_govt_nz.parliament.report_holds import (
    enforce_holds,
    register_hold,
    reviewed_holds,
    unreviewed_failures,
    validate_hold,
)

from .test_hosted_state import GUID, SID, seeded

if TYPE_CHECKING:
    from pathlib import Path

    from archive_govt_nz.parliament.pipeline import ParliamentArchive


def failed(root: Path) -> tuple[ParliamentArchive, dict[str, object]]:
    """Retain one real-shaped terminal source failure, without network access."""
    archive = seeded(root)
    url = (
        "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/" + GUID
    )
    with archive._connection() as connection:  # noqa: SLF001 - isolated fixture
        record = json.loads(
            connection.execute("SELECT record FROM records").fetchone()[0]
        )
        record.update(metadata_only=False, attachments=[url])
        text = json.dumps(record)
        connection.execute(
            "UPDATE records SET record=?,status='failed',last_error='terminal_status'",
            (text,),
        )
        connection.execute(
            "INSERT INTO events VALUES(?,?,?,?)",
            (SID, "failed", "terminal_status", 1.0),
        )
    proof = {
        "schema_version": "parliament-report-access-hold/v1",
        "source_id": SID,
        "record_sha256": hashlib.sha256(text.encode()).hexdigest(),
        "source_url": url,
        "reason": "terminal_http_response_unclassified",
        "original_http_status": None,
        "failure_state_schema": "parliament-hosted-state/v1",
        "native_failure_receipt": {
            "status": "failed",
            "operation": "run",
            "error_class": "HostedError",
            "reason": "report_capture_failed",
        },
        "native_failure_receipt_canonical_sha256": "4" * 64,
        "failure_code_revision": "3" * 40,
        "failure_snapshot_sha256": "1" * 64,
        "failure_snapshot_revision": "2" * 40,
        "failing_invocation": "gha_1_1",
        "failure_observed": 1.0,
        "approval_invocation": "gha_2_1",
        "approval_observed": 2.0,
        "licence_grant": False,
        "original_publication_grant": False,
        "source_probed_during_approval": False,
        "scope": "single_unchanged_source_url",
    }
    return archive, proof


def test_exact_hold_retains_failed_status_and_does_not_publish(tmp_path: Path) -> None:
    """One reviewed failure is explicit; neither bytes nor a success are invented."""
    archive, proof = failed(tmp_path)
    assert unreviewed_failures(archive) == [SID]
    sha = register_hold(archive, proof)
    assert len(sha) == 64
    assert set(reviewed_holds(archive)) == {SID}
    assert unreviewed_failures(archive) == []
    assert archive.summary()["failed"] == 1
    assert archive.summary()["captured"] == 0
    assert not archive.report_decisions()


def test_metadata_refresh_cannot_retry_same_held_attachment(tmp_path: Path) -> None:
    """A changed title cannot re-probe an unchanged inaccessible source object."""
    archive, proof = failed(tmp_path)
    register_hold(archive, proof)
    with archive._connection() as connection:  # noqa: SLF001 - isolated fixture
        record = json.loads(
            connection.execute("SELECT record FROM records").fetchone()[0]
        )
        record["title"] = "Refreshed metadata"
        connection.execute(
            "UPDATE records SET record=?,status='pending'", (json.dumps(record),)
        )
    assert enforce_holds(archive)
    assert archive.summary()["pending"] == 0
    assert archive.summary()["failed"] == 1
    assert not enforce_holds(archive)


def test_hold_proof_survives_typed_cold_restore_and_fences_v1(tmp_path: Path) -> None:
    """The new semantics cannot be consumed by an older unaware producer."""
    archive, proof = failed(tmp_path / "source")
    sha = register_hold(archive, proof)
    state, files = export_state(archive, {})
    assert state["schema"] == "parliament-hosted-state/v2"
    assert any(path.endswith(sha) for path in files)
    assert b"UNQUALIFIED AUTHOR HTML" not in b"".join(
        p.read_bytes() for p in files.values()
    )
    fresh = import_state(state, tmp_path / "fresh")
    for path in files.values():
        fresh.store.put_bytes(path.read_bytes())
    assert set(reviewed_holds(fresh)) == {SID}
    assert fresh.summary()["failed"] == 1
    state["schema"] = "parliament-hosted-state/v1"
    with pytest.raises(ValueError, match="state_"):
        validate_state(state)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("licence_grant", True),
        ("original_publication_grant", True),
        ("source_probed_during_approval", True),
        ("scope", "all_reports"),
        ("source_url", "https://example.org/attachment"),
        ("source_id", "submission-" + GUID),
        ("record_sha256", "invalid"),
        ("approval_invocation", "local_actor"),
        ("approval_observed", 0.5),
        ("failure_observed", float("inf")),
        ("original_http_status", 500),
        ("native_failure_receipt", {}),
    ],
)
def test_proof_cannot_grant_access_or_widen_scope(
    tmp_path: Path, field: str, value: object
) -> None:
    """Malformed metadata cannot become an approved exclusion or licence."""
    archive, proof = failed(tmp_path)
    proof[field] = value
    with pytest.raises(ValueError, match="report_hold_"):
        register_hold(archive, proof)
    assert unreviewed_failures(archive) == [SID]


def test_known_access_status_requires_new_wire_and_explicit_class(
    tmp_path: Path,
) -> None:
    """An old missing numeric code cannot be invented or misclassified."""
    _, proof = failed(tmp_path)
    proof.update(
        original_http_status=403,
        failure_state_schema="parliament-hosted-state/v2",
        reason="terminal_http_access_unavailable",
    )
    validate_hold(proof)
    proof["original_http_status"] = None
    with pytest.raises(ValueError, match="failure_class"):
        validate_hold(proof)


def test_changed_url_and_unrelated_failure_still_block(tmp_path: Path) -> None:
    """A hold does not exempt new sources or integrity/robots failures."""
    archive, proof = failed(tmp_path)
    sha = register_hold(archive, proof)
    assert register_hold(archive, proof) == sha
    with archive._connection() as connection:  # noqa: SLF001 - isolated fixture
        connection.execute("UPDATE records SET last_error='robots_denied'")
    assert unreviewed_failures(archive) == [SID]
    with archive._connection() as connection:  # noqa: SLF001 - isolated fixture
        record = json.loads(
            connection.execute("SELECT record FROM records").fetchone()[0]
        )
        record["attachments"] = [str(proof["source_url"]).replace(GUID, "0" * 36)]
        connection.execute(
            "UPDATE records SET status='pending',record=?", (json.dumps(record),)
        )
    assert not enforce_holds(archive)
    assert archive.summary()["pending"] == 1


def test_source_terminal_status_preserved_without_response_body(
    tmp_path: Path,
) -> None:
    """One source request yields only status and exact hashes in public state."""
    archive, _ = failed(tmp_path)
    with archive._connection() as connection:  # noqa: SLF001 - isolated fixture
        connection.execute("UPDATE records SET status='pending',last_error=NULL")
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        requests.append(str(request.url))
        if request.url.path == "/robots.txt":
            return httpx.Response(200, text="User-agent: *\nAllow: /")
        return httpx.Response(403, text="PRIVATE RESPONSE MUST NEVER BE PUBLISHED")

    async def capture() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(respond)) as client:
            await archive.capture(client, Bounds(max_records=1))

    asyncio.run(capture())
    assert len([r for r in requests if "/download/" in r]) == 1
    state, _ = export_state(archive, {})
    assert state["schema"] == "parliament-hosted-state/v2"
    events = [
        r for r in state["tables"]["events"] if r["status"] == "source_http_failure"
    ]
    assert len(events) == 1
    assert json.loads(events[0]["detail"])["http_status"] == 403
    assert "PRIVATE RESPONSE" not in json.dumps(state)
    assert unreviewed_failures(archive) == [SID]
