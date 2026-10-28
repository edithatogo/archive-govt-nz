"""Typed report-only projections; never export a raw database or arbitrary CAS."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from contextlib import closing
from typing import Any, NoReturn
lazy from pathlib import Path

from archive_govt_nz.parliament.contracts import validate_manifest
from archive_govt_nz.parliament.discovery import Record
from archive_govt_nz.parliament.pipeline import ParliamentArchive
from archive_govt_nz.parliament.report_holds import (
    HOLD_EVENT,
    HTTP_ERROR_MAX,
    HTTP_ERROR_MIN,
    HTTP_FAILURE_EVENT,
    MAX_HOLD_BYTES,
    V2,
    read_hold,
)
from archive_govt_nz.parliament.reports import (
    DEFAULT_PAGE_SIZE,
    ENDPOINT,
    ReportQuery,
    parse_reports,
)

MAX_ROWS = 200000
MAX_CLOCK = 1e12
MAX_BYTES = 262144000
MAX_RECORDS = 100
MAX_SECONDS = 900
SUCCESS = 200

SCHEMA = "parliament-hosted-state/v1"
DIGEST = r"[0-9a-f]{64}"
REVISION = r"[0-9a-f]{40}"
GUID = r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"
DOWNLOAD = "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/"
REPOSITORY = "edithatogo/archive-govt-nz-global"
TABLES = {
    "records": ("source_id", "record", "partition", "status", "last_error"),
    "captures": ("source_id", "url", "sha256", "size", "content_type", "observed"),
    "observations": (
        "source_id",
        "url",
        "sha256",
        "record_sha256",
        "record",
        "observed",
    ),
    "members": ("source_id", "sha256", "record_sha256", "batch"),
    "publications": ("batch", "revision", "repo", "status"),
    "events": ("source_id", "status", "detail", "observed"),
    "control": ("key", "value"),
    "pages": ("partition", "url", "sha256", "next_url", "total", "observed"),
}


def canonical(value: object) -> bytes:
    """Encode checkpoint metadata deterministically, without nonfinite values."""
    return (
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    ).encode()


def digest(data: bytes) -> str:
    """Return the immutable SHA256 identity."""
    return hashlib.sha256(data).hexdigest()


def fail(reason: str) -> NoReturn:
    """Fail closed with a sanitized public reason."""
    raise ValueError(reason)


def safe_event(value: str | None) -> str | None:
    """Retain typed source receipts/codes, replacing raw diagnostics by hashes."""
    if value is None or re.fullmatch(
        r"(?:[a-z]+(?:_[a-z]+)+|[0-9a-f]{64}|redacted_sha256:[0-9a-f]{64}|(?:Read|Connect|Write|Pool)Timeout|(?:Connect|Read|Write|Network|Protocol|Transport)Error)",
        value,
    ):
        return value
    try:
        data = json.loads(value)
    except ValueError:
        data = None
    if (
        isinstance(data, dict)
        and set(data) == {"error_class", "http_status", "url_sha256", "record_sha256"}
        and data["error_class"] == "terminal_status"
        and type(data["http_status"]) is int
        and HTTP_ERROR_MIN <= data["http_status"] <= HTTP_ERROR_MAX
        and all(
            isinstance(data[k], str) and re.fullmatch(DIGEST, data[k])
            for k in ("url_sha256", "record_sha256")
        )
    ):
        return canonical(data).decode()
    if (
        isinstance(data, dict)
        and set(data)
        == {
            "url",
            "http_status",
            "content_type",
            "sha256",
            "blake3",
            "bytes",
            "duration",
        }
        and (
            re.fullmatch(re.escape(DOWNLOAD) + GUID, data["url"])
            and data["http_status"] == SUCCESS
            and re.fullmatch(DIGEST, data["sha256"])
            and re.fullmatch(DIGEST, data["blake3"])
            and type(data["bytes"]) is int
            and 0 <= data["bytes"] <= 64 * 1024 * 1024
            and type(data["duration"]) in {int, float}
            and math.isfinite(data["duration"])
            and data["duration"] >= 0
            and (
                data["content_type"] is None
                or re.fullmatch(r"[A-Za-z0-9_./+;= -]{1,200}", data["content_type"])
            )
        )
    ):
        return canonical(data).decode()
    return "redacted_sha256:" + digest(value.encode())


def candidate(
    value: dict[str, Any], sha: str, ids: set[str], responses: set[str]
) -> None:
    """Require an exact native report candidate shard and source evidence."""
    if (
        set(value) != {"schema_version", "partition", "discovery_sha256", "records"}
        or value["schema_version"] != "parliament-candidates/v1"
        or digest(canonical(value)) != sha
        or value["discovery_sha256"] not in responses
        or not re.fullmatch(r"[a-z0-9-]{1,100}", value["partition"])
        or not 0 < len(value["records"]) <= MAX_RECORDS
    ):
        fail("report_only_candidate")
    for row in value["records"]:
        if report(canonical(row).decode()).source_id not in ids:
            fail("report_only_candidate")


def report(text: str) -> Record:
    """Validate the exact report record and its public source addresses."""
    try:
        value = Record(**json.loads(text))
    except ValueError, TypeError:
        fail("report_only_record")
    if (
        value.kind != "report"
        or not re.fullmatch("report-" + GUID, value.source_id)
        or value.url
        != "https://selectcommittees.parliament.nz/v/6/" + value.source_id[7:]
        or len(value.attachments) > 1
        or any(
            not re.fullmatch(re.escape(DOWNLOAD) + GUID, url)
            for url in value.attachments
        )
    ):
        fail("report_only_record")
    return value


def reference(value: dict[str, Any], sha: str) -> None:
    """Accept only immutable qualified paths on the single approved target."""
    if (
        set(value) != {"path", "revision", "size"}
        or not re.fullmatch(DIGEST, sha)
        or type(value["size"]) is not int
        or not 0 <= value["size"] <= 64 * 1024 * 1024
        or not re.fullmatch(
            rf"parliament/(?:batches/{DIGEST}/objects|checkpoint-objects/[0-9a-f]{{2}})/{sha}",
            value["path"],
        )
        or (
            value["revision"] is not None
            and not re.fullmatch(REVISION, value["revision"])
        )
    ):
        fail("state_object_reference")


def query(value: dict[str, Any]) -> None:
    """Bound public report queries, including the known late-attachment search."""
    if set(value) != {"page", "page_size", "keyword"}:
        fail("state_query")
    if (
        value["keyword"] not in {"", "Tāmaki Redevelopment"}
        or type(value["page_size"]) is not int
        or value["page_size"] != DEFAULT_PAGE_SIZE
        or (value["page"] is not None and type(value["page"]) is not int)
    ):
        fail("state_query")
    if value["page"] is not None:
        ReportQuery(**value)


def validate_state(state: dict[str, Any]) -> None:  # noqa: C901, PLR0912, PLR0915
    """Reject unrelated records, URLs, tables, object paths and snapshot drift."""
    if set(state) != {
        "schema",
        "tables",
        "objects",
        "batches",
        "candidates",
        "work",
        "cycle",
    } or state["schema"] not in {SCHEMA, V2}:
        fail("state_schema")
    tables = state["tables"]
    if set(tables) != set(TABLES):
        fail("state_schema")
    for name, columns in TABLES.items():
        if not isinstance(tables[name], list) or len(tables[name]) > MAX_ROWS:
            fail("state_schema")
        if any(set(row) != set(columns) for row in tables[name]):
            fail("state_schema")
    ids = set()
    for row in tables["records"]:
        rec = report(row["record"])
        if row["source_id"] != rec.source_id or row["source_id"] in ids:
            fail("report_only_identity")
        ids.add(rec.source_id)
        if row["status"] not in {"pending", "captured", "metadata_only", "failed"}:
            fail("state_status")
        if row["last_error"] is not None and not re.fullmatch(
            r"[A-Za-z0-9_:.-]{1,128}", row["last_error"]
        ):
            fail("state_error")
    for row in tables["captures"] + tables["observations"]:
        sha = row["sha256"]
        if row["source_id"] not in ids or sha not in state["objects"]:
            fail("state_capture_reference")
        if not (
            row["url"] == ENDPOINT + "#response=" + sha
            or re.fullmatch(re.escape(DOWNLOAD) + GUID, row["url"])
        ):
            fail("report_only_capture")
        if "record" in row and (
            report(row["record"]).source_id != row["source_id"]
            or digest(row["record"].encode()) != row["record_sha256"]
        ):
            fail("state_observation_identity")
    capture_keys = {
        (row["source_id"], row["url"], row["sha256"]) for row in tables["captures"]
    }
    observations = {
        (row["source_id"], row["sha256"], row["record_sha256"])
        for row in tables["observations"]
    }
    for row in tables["observations"]:
        if (row["source_id"], row["url"], row["sha256"]) not in capture_keys:
            fail("state_observation_reference")
    for row in tables["captures"]:
        if row["size"] != state["objects"][row["sha256"]]["size"]:
            fail("state_capture_size")
    for row in tables["members"]:
        if row["source_id"] not in ids or any(
            not re.fullmatch(DIGEST, row[key])
            for key in ("sha256", "record_sha256", "batch")
        ):
            fail("state_member")
        if (row["source_id"], row["sha256"], row["record_sha256"]) not in observations:
            fail("state_member_observation")
    for row in tables["publications"]:
        if (
            row["repo"] != REPOSITORY
            or row["status"] not in {"uploaded", "verified"}
            or not re.fullmatch(DIGEST, row["batch"])
            or not re.fullmatch(REVISION, row["revision"])
        ):
            fail("state_publication")
    for row in tables["control"]:
        key = row["key"]
        if key.startswith("reports:") and re.fullmatch(r"reports:[a-z0-9-]{1,80}", key):
            query(json.loads(row["value"]))
        elif key in {"last_request", "defer_until"}:
            if not 0 <= float(row["value"]) < MAX_CLOCK:
                fail("state_control")
        elif key != "schema_version" or row["value"] != "2":
            fail("state_control")
    if state["schema"] == SCHEMA and any(
        r["status"] in {HOLD_EVENT, HTTP_FAILURE_EVENT} for r in tables["events"]
    ):
        fail("state_semantics_require_v2")
    for row in tables["events"]:
        if row["status"] == HOLD_EVENT and (
            row["detail"] not in state["objects"]
            or state["objects"][row["detail"]]["size"] > MAX_HOLD_BYTES
        ):
            fail("state_hold_reference")
        if (
            row["source_id"] not in ids
            or not re.fullmatch(r"[a-z_]{1,80}", row["status"])
            or row["detail"] != safe_event(row["detail"])
        ):
            fail("state_event")
    for row in tables["pages"]:
        if (
            not re.fullmatch(re.escape(ENDPOINT) + "#request=" + DIGEST, row["url"])
            or row["sha256"] not in state["objects"]
        ):
            fail("state_page")
    for sha, ref in state["objects"].items():
        reference(ref, sha)
    for sha, manifest in state["batches"].items():
        validate_manifest(manifest)
        if digest(canonical(manifest)) != sha or any(
            report(row["record"]).source_id != row["source_id"]
            for row in manifest["records"]
        ):
            fail("report_only_batch")
    referenced = {row["sha256"] for row in tables["captures"]}
    for row in tables["pages"]:
        referenced.update((row["sha256"], row["url"].split("#request=")[1]))
    for manifest in state["batches"].values():
        referenced.update(row["sha256"] for row in manifest["records"])
    if len(state["candidates"]) > MAX_ROWS:
        fail("state_candidate_bound")
    for sha, shard in state["candidates"].items():
        candidate(shard, sha, ids, referenced)
    referenced.update(
        r["detail"] for r in tables["events"] if r["status"] == HOLD_EVENT
    )
    if referenced != set(state["objects"]):
        fail("state_unreferenced_objects")
    if type(state["cycle"]) is not int or state["cycle"] < 0:
        fail("state_cycle")
    # Work contains controller-owned counters only; never raw diagnostics/URLs.
    if state["work"] is not None:
        work = state["work"]
        required = {
            "phase",
            "query",
            "partition",
            "bytes",
            "observed",
            "captured",
            "seconds",
            "reserved",
            "interrupted",
            "invocation",
        }
        if set(work) != required or work["phase"] not in {
            "discover",
            "capture",
            "publish",
        }:
            fail("state_work")
        query(work["query"])
        if (
            not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", work["invocation"])
            or type(work["interrupted"]) is not bool
        ):
            fail("state_work_owner")
        if not re.fullmatch(r"[a-z0-9-]{1,100}", work["partition"]) or any(
            type(work[k]) not in {int, float}
            or not math.isfinite(work[k])
            or work[k] < 0
            for k in ("bytes", "observed", "captured", "seconds", "reserved")
        ):
            fail("state_work")
        if (
            work["bytes"] + work["reserved"] > MAX_BYTES
            or work["observed"] > MAX_RECORDS
            or work["captured"] > MAX_RECORDS
            or work["seconds"] > MAX_SECONDS
        ):
            fail("state_work_bounds")


def candidate_index(
    root: Path, ids: set[str], responses: set[str], previous: dict[str, Any] | None
) -> dict[str, Any]:
    """Keep qualified original shards without exposing unrelated local evidence."""
    candidates = dict(previous or {})
    for path in (root / "candidates").glob("*.json"):
        try:
            value = json.loads(path.read_bytes())
            candidate(value, path.stem, ids, responses)
        except ValueError, TypeError, KeyError:
            # Unsupported legacy/unqualified shards remain on the original SSD.
            # Hosted retirement refuses to delete anything outside this index.
            continue
        candidates[path.stem] = value
    return candidates


def _hold_references(
    archive: ParliamentArchive, events: list[dict[str, Any]]
) -> set[str]:
    """Admit only bounded, typed own-metadata qualification objects."""
    wanted: set[str] = set()
    for event in events:
        if event["status"] == HOLD_EVENT:
            proof = read_hold(archive, event["detail"])
            if proof["source_id"] != event["source_id"]:
                fail("state_hold_source")
            wanted.add(event["detail"])
    return wanted


def export_state(
    archive: ParliamentArchive,
    refs: dict[str, Any],
    *,
    work: dict[str, Any] | None = None,
    cycle: int = 0,
    previous_candidates: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Path]]:
    """Project public report state and return only newly referenced qualified files."""
    connection = sqlite3.connect(archive.database)
    connection.row_factory = sqlite3.Row
    try:
        tables = {
            name: [
                dict(row)
                for row in connection.execute(
                    "SELECT * FROM "  # noqa: S608 - fixed TABLES keys
                    + name
                    + (" ORDER BY rowid" if name == "events" else "")
                )
            ]
            for name in TABLES
        }
    finally:
        connection.close()
    ids = {report(row["record"]).source_id for row in tables["records"]}
    for name in ("captures", "observations", "members", "events"):
        tables[name] = [row for row in tables[name] if row["source_id"] in ids]
    # Diagnostic details stay in local history, never in public state. Ordering
    # and event times still preserve refresh/version replay semantics.
    for row in tables["events"]:
        row["detail"] = safe_event(row["detail"])
    tables["control"] = [
        row
        for row in tables["control"]
        if row["key"] == "schema_version"
        or row["key"] in {"last_request", "defer_until"}
        or row["key"].startswith("reports:")
    ]
    tables["pages"] = [
        row for row in tables["pages"] if row["url"].startswith(ENDPOINT + "#request=")
    ]
    objects: dict[str, Any] = {}
    files: dict[str, Path] = {}
    wanted = {row["sha256"] for row in tables["captures"]}
    wanted.update(_hold_references(archive, tables["events"]))
    for row in tables["pages"]:
        request_sha = row["url"].split("#request=")[1]
        request = (
            json.loads(
                (archive.store.objects / request_sha[:2] / request_sha).read_bytes()
            )
            if request_sha not in refs
            else None
        )
        if request is not None:
            if (
                set(request)
                != {"endpoint", "method", "body", "response_sha256", "http_status"}
                or request["endpoint"] != ENDPOINT
                or request["method"] != "POST"
                or request["http_status"] != SUCCESS
                or request["response_sha256"] != row["sha256"]
            ):
                fail("report_only_request")
            body = request["body"]
            q = ReportQuery(
                page=body["page"], page_size=body["pageSize"], keyword=body["keyword"]
            )
            query({"page": q.page, "page_size": q.page_size, "keyword": q.keyword})
            parse_reports(
                json.loads(
                    (
                        archive.store.objects / row["sha256"][:2] / row["sha256"]
                    ).read_bytes()
                ),
                q,
            )
        wanted.update((request_sha, row["sha256"]))
    candidates = candidate_index(archive.root, ids, wanted, previous_candidates)
    batches = {}
    verified = {r["batch"] for r in tables["publications"] if r["status"] == "verified"}
    for batch in {r["batch"] for r in tables["members"]} - verified:
        manifest = json.loads(
            (archive.root / "batches" / batch / "manifest.json").read_bytes()
        )
        batches[batch] = manifest
        wanted.update(row["sha256"] for row in manifest["records"])
    for sha in wanted:
        if sha in refs:
            objects[sha] = dict(refs[sha])
        else:
            receipt = archive.store.verify("sha256:" + sha)
            objects[sha] = {
                "size": receipt.byte_count,
                "path": "parliament/checkpoint-objects/" + sha[:2] + "/" + sha,
                "revision": None,
            }
            files[objects[sha]["path"]] = receipt.path
    state = {
        "schema": V2
        if any(
            r["status"] in {HOLD_EVENT, HTTP_FAILURE_EVENT} for r in tables["events"]
        )
        else SCHEMA,
        "tables": tables,
        "objects": objects,
        "batches": batches,
        "candidates": candidates,
        "work": work,
        "cycle": cycle,
    }
    validate_state(state)
    return state, files


def import_state(state: dict[str, Any], root: Path) -> ParliamentArchive:
    """Restore only validated columns into a new isolated database."""
    validate_state(state)
    if (root / "state.sqlite3").exists():
        fail("restore_target_exists")
    archive = ParliamentArchive(root)
    with closing(sqlite3.connect(archive.database)) as connection, connection:
        for name, columns in TABLES.items():
            connection.execute("DELETE FROM " + name)  # noqa: S608 - fixed table names
            sql = (
                "INSERT INTO "
                + name
                + "("
                + ",".join(columns)
                + ") VALUES("
                + ",".join("?" for _ in columns)
                + ")"
            )
            connection.executemany(
                sql,
                [tuple(row[col] for col in columns) for row in state["tables"][name]],
            )
    for batch, manifest in state["batches"].items():
        path = root / "batches" / batch / "manifest.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical(manifest))
    return archive
