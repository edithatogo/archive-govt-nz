"""Exact non-publication holds for reviewed terminal report responses."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
from contextlib import closing
from typing import TYPE_CHECKING, Any, NoReturn

from archive_govt_nz.capture import CaptureError
from archive_govt_nz.parliament.reports import GUID

if TYPE_CHECKING:
    from archive_govt_nz.parliament.pipeline import ParliamentArchive

HOLD_EVENT = "report_access_hold"
HTTP_FAILURE_EVENT = "source_http_failure"
HTTP_ERROR_MIN = 400
HTTP_ERROR_MAX = 599
MAX_HOLD_BYTES = 4096
MAX_CLOCK = 100_000_000_000
DOWNLOAD = "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/"
ACCESS_STATUSES = frozenset({401, 403, 404, 410, 451})
V1 = "parliament-hosted-state/v1"
V2 = "parliament-hosted-state/v2"
FIELDS = frozenset(
    {
        "schema_version",
        "source_id",
        "record_sha256",
        "source_url",
        "reason",
        "original_http_status",
        "failure_state_schema",
        "native_failure_receipt",
        "native_failure_receipt_canonical_sha256",
        "failure_code_revision",
        "failure_snapshot_sha256",
        "failure_snapshot_revision",
        "failing_invocation",
        "failure_observed",
        "approval_invocation",
        "approval_observed",
        "licence_grant",
        "original_publication_grant",
        "source_probed_during_approval",
        "scope",
    }
)


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def proof_bytes(value: object) -> bytes:
    """Use deterministic own-metadata bytes, never a source response body."""
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()


def sha256(value: bytes) -> str:
    """Bind an exact source record or qualification object."""
    return hashlib.sha256(value).hexdigest()


def validate_hold(proof: dict[str, Any]) -> None:
    """Reject wider scope, unknown fields, unsafe URLs and every publication grant."""
    if not isinstance(proof, dict) or set(proof) != FIELDS:
        _fail("report_hold_schema")
    sid, url = proof["source_id"], proof["source_url"]
    if (
        not isinstance(sid, str)
        or not sid.startswith("report-")
        or GUID.fullmatch(sid[7:]) is None
        or not isinstance(url, str)
        or not url.startswith(DOWNLOAD)
        or GUID.fullmatch(url[len(DOWNLOAD) :]) is None
        or proof["schema_version"] != "parliament-report-access-hold/v1"
        or proof["scope"] != "single_unchanged_source_url"
        or any(
            proof[k] is not False
            for k in (
                "licence_grant",
                "original_publication_grant",
                "source_probed_during_approval",
            )
        )
    ):
        _fail("report_hold_scope")
    _validate_identity(proof)
    _validate_failure(proof)
    if len(proof_bytes(proof)) > MAX_HOLD_BYTES:
        _fail("report_hold_size")


def _validate_identity(proof: dict[str, Any]) -> None:
    """Bind hashes and both native invocation identities."""
    for key, length in (
        ("record_sha256", 64),
        ("native_failure_receipt_canonical_sha256", 64),
        ("failure_snapshot_sha256", 64),
        ("failure_snapshot_revision", 40),
        ("failure_code_revision", 40),
    ):
        if not isinstance(proof[key], str) or not re.fullmatch(
            r"[0-9a-f]{" + str(length) + "}", proof[key]
        ):
            _fail("report_hold_identity")
    for key in ("failing_invocation", "approval_invocation"):
        if not isinstance(proof[key], str) or not re.fullmatch(
            r"gha_[0-9]{1,20}_[0-9]{1,10}", proof[key]
        ):
            _fail("report_hold_authority")


def _validate_failure(proof: dict[str, Any]) -> None:
    """Preserve uncertainty and reject non-access errors or forged receipt classes."""
    for key in ("failure_observed", "approval_observed"):
        value = proof[key]
        if (
            type(value) not in {int, float}
            or not math.isfinite(value)
            or not 0 <= value < MAX_CLOCK
        ):
            _fail("report_hold_clock")
    if proof["approval_observed"] < proof["failure_observed"]:
        _fail("report_hold_clock")
    receipt = proof["native_failure_receipt"]
    if (
        not isinstance(receipt, dict)
        or set(receipt) != {"status", "operation", "error_class", "reason"}
        or receipt["status"] != "failed"
        or receipt["operation"] not in {"run", "pilot"}
        or receipt["error_class"] != "HostedError"
        or receipt["reason"] != "report_capture_failed"
    ):
        _fail("report_hold_native_receipt")
    status = proof["original_http_status"]
    legacy = (
        status is None
        and proof["failure_state_schema"] == V1
        and proof["reason"] == "terminal_http_response_unclassified"
    )
    known = (
        type(status) is int
        and status in ACCESS_STATUSES
        and proof["failure_state_schema"] == V2
        and proof["reason"] == "terminal_http_access_unavailable"
    )
    if not legacy and not known:
        _fail("report_hold_failure_class")


def read_hold(archive: ParliamentArchive, sha: str) -> dict[str, Any]:
    """Hydrate only a pinned, bounded qualification object from the typed index."""
    if not re.fullmatch(r"[0-9a-f]{64}", sha):
        _fail("report_hold_identity")
    receipt = archive.store.verify("sha256:" + sha)
    if receipt.byte_count > MAX_HOLD_BYTES:
        _fail("report_hold_size")
    proof = json.loads(receipt.path.read_bytes())
    validate_hold(proof)
    return proof


def all_holds(archive: ParliamentArchive) -> list[tuple[str, dict[str, Any]]]:
    """Retain historical URL exclusions, including when a URL later reappears."""
    with closing(sqlite3.connect(archive.database)) as connection:
        rows = connection.execute(
            "SELECT source_id,detail FROM events WHERE status=? ORDER BY rowid",
            (HOLD_EVENT,),
        ).fetchall()
    result = []
    for sid, sha in rows:
        proof = read_hold(archive, sha)
        if proof["source_id"] != sid:
            _fail("report_hold_source")
        result.append((sha, proof))
    return result


def _records(archive: ParliamentArchive) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(archive.database)) as connection:
        connection.row_factory = sqlite3.Row
        return [dict(r) for r in connection.execute("SELECT * FROM records")]


def reviewed_holds(archive: ParliamentArchive) -> dict[str, dict[str, Any]]:
    """Exclude only the same URL and only the admitted terminal failure class."""
    proofs = [p for _, p in all_holds(archive)]
    result = {}
    for row in _records(archive):
        record = json.loads(row["record"])
        if row["status"] != "failed" or row["last_error"] not in {
            "terminal_status",
            "reviewed_access_hold",
        }:
            continue
        for proof in proofs:
            if (
                row["source_id"] == proof["source_id"]
                and record["kind"] == "report"
                and record["attachments"] == [proof["source_url"]]
            ):
                result[row["source_id"]] = proof
    return result


def register_hold(archive: ParliamentArchive, proof: dict[str, Any]) -> str:
    """Register one reviewed exclusion; preserve the original failed state."""
    validate_hold(proof)
    archive._guard()  # noqa: SLF001 - same fenced archive mutation boundary
    rows = [r for r in _records(archive) if r["source_id"] == proof["source_id"]]
    if len(rows) != 1:
        _fail("report_hold_target")
    row = rows[0]
    record = json.loads(row["record"])
    if (
        row["status"] != "failed"
        or row["last_error"] != "terminal_status"
        or sha256(row["record"].encode()) != proof["record_sha256"]
        or record["kind"] != "report"
        or record["metadata_only"]
        or record["attachments"] != [proof["source_url"]]
    ):
        _fail("report_hold_target_changed")
    with closing(sqlite3.connect(archive.database)) as connection:
        event = connection.execute(
            "SELECT 1 FROM events WHERE source_id=? AND status='failed' "
            "AND detail='terminal_status' AND observed=?",
            (proof["source_id"], proof["failure_observed"]),
        ).fetchone()
    if event is None:
        _fail("report_hold_missing_failure")
    for sha, previous in all_holds(archive):
        if (
            previous["source_id"] == proof["source_id"]
            and previous["source_url"] == proof["source_url"]
        ):
            return sha
    receipt = archive.store.put_bytes(proof_bytes(proof))
    with closing(sqlite3.connect(archive.database)) as connection, connection:
        connection.execute(
            "INSERT INTO events VALUES(?,?,?,?)",
            (
                proof["source_id"],
                HOLD_EVENT,
                receipt.sha256,
                proof["approval_observed"],
            ),
        )
    return receipt.sha256


def enforce_holds(archive: ParliamentArchive) -> bool:
    """Block a title/date refresh from retrying an unchanged held URL."""
    proofs = [p for _, p in all_holds(archive)]
    changed = False
    for row in _records(archive):
        if row["status"] != "pending":
            continue
        record = json.loads(row["record"])
        match = next(
            (
                p
                for p in proofs
                if p["source_id"] == row["source_id"]
                and record["attachments"] == [p["source_url"]]
            ),
            None,
        )
        if match is not None:
            archive._guard()  # noqa: SLF001 - same fenced archive mutation boundary
            with closing(sqlite3.connect(archive.database)) as connection, connection:
                connection.execute(
                    "UPDATE records SET status='failed',"
                    "last_error='reviewed_access_hold' "
                    "WHERE source_id=?",
                    (row["source_id"],),
                )
                connection.execute(
                    "INSERT INTO events VALUES(?,?,?,?)",
                    (
                        row["source_id"],
                        "report_access_hold_applied",
                        sha256(row["record"].encode()),
                        time.time(),
                    ),
                )
            changed = True
    return changed


def unreviewed_failures(archive: ParliamentArchive) -> list[str]:
    """Every other failure still stops acquisition; no blanket waiver exists."""
    reviewed = reviewed_holds(archive)
    return [
        r["source_id"]
        for r in _records(archive)
        if r["status"] == "failed" and r["source_id"] not in reviewed
    ]


def record_http_failure(
    connection: sqlite3.Connection,
    source_id: str,
    record: str,
    url: str,
    error: Exception,
) -> None:
    """Retain available HTTP status without response bodies, headers or SDK text."""
    if (
        not isinstance(error, CaptureError)
        or error.error_class != "terminal_status"
        or not error.attempts
        or json.loads(record)["kind"] != "report"
    ):
        return
    status = error.attempts[-1].status_code
    if type(status) is not int or not HTTP_ERROR_MIN <= status <= HTTP_ERROR_MAX:
        return
    detail = proof_bytes(
        {
            "error_class": "terminal_status",
            "http_status": status,
            "url_sha256": sha256(url.encode()),
            "record_sha256": sha256(record.encode()),
        }
    ).decode()
    connection.execute(
        "INSERT INTO events VALUES(?,?,?,?)",
        (source_id, HTTP_FAILURE_EVENT, detail, time.time()),
    )
