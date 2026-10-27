"""Durable bounded Parliament queues, guarded capture and immutable batches."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform
import re
import sqlite3
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass, replace
from email.utils import parsedate_to_datetime
from importlib.resources import files
from typing import TYPE_CHECKING
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import httpx

from archive_govt_nz import __version__
from archive_govt_nz.capture import CaptureConfig, CaptureError, capture_url
from archive_govt_nz.object_store import ContentAddressedStore
from archive_govt_nz.parliament.contracts import (
    PUBLIC_REPOSITORY,
    decision_for,
    validate_decisions,
    validate_manifest,
)
from archive_govt_nz.parliament.discovery import (
    Record,
    attachment_links,
    parse_listing,
    safe_url,
)
from archive_govt_nz.parliament.lease import file_lock
from archive_govt_nz.parliament.reports import (
    DEFAULT_PAGE_SIZE,
    ENDPOINT,
    ReportQuery,
    parse_reports,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

USER_AGENT = "archive-govt-nz-preservation/1.0"
MAX_BATCH_DECISIONS = 200
MAX_BATCH_RECORDS = 100
MAX_BATCH_BYTES = 250 * 1024 * 1024
STATE_RESERVE_BYTES = 64 * 1024


def _json(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, ensure_ascii=False) + "\n").encode()


def _atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            if path.read_bytes() != data:
                message = "immutable_batch_conflict"
                raise ValueError(message)
        else:
            temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


@dataclass(frozen=True)
class Bounds:
    """First-hit run bounds, additionally enforced per HTTP response."""

    max_records: int = 100
    max_bytes: int = 250 * 1024 * 1024
    max_seconds: float = 900
    max_file_bytes: int = 64 * 1024 * 1024
    max_spool_bytes: int = 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        """Reject non-positive bounds before filesystem or network work."""
        if (
            min(
                self.max_records,
                self.max_bytes,
                self.max_seconds,
                self.max_file_bytes,
                self.max_spool_bytes,
            )
            <= 0
        ):
            message = "invalid_bounds"
            raise ValueError(message)


class ParliamentArchive:
    """One shared durable state root for all Parliament collection streams."""

    def __init__(
        self,
        root: Path,
        *,
        delay: float = 1.0,
        checkpoint: Callable[[str, dict[str, object]], None] | None = None,
        guard: Callable[[], None] | None = None,
        source_guard: Callable[[], None] | None = None,
    ) -> None:
        """Open one explicitly selected durable state root."""
        if delay < 0:
            message = "invalid_delay"
            raise ValueError(message)
        self.root = root
        self.checkpoint = checkpoint
        self.guard = guard
        self.source_guard = source_guard
        self.delay = delay
        root.mkdir(parents=True, exist_ok=True)
        self.store = ContentAddressedStore(root / "cas")
        self.database = root / "state.sqlite3"
        with self._connection() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS records (
                    source_id TEXT PRIMARY KEY, record TEXT NOT NULL,
                    partition TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
                    last_error TEXT);
                CREATE TABLE IF NOT EXISTS captures (
                    source_id TEXT NOT NULL, url TEXT NOT NULL, sha256 TEXT NOT NULL,
                    size INTEGER NOT NULL, content_type TEXT,
                    observed REAL NOT NULL,
                    PRIMARY KEY(source_id, url, sha256));
                CREATE TABLE IF NOT EXISTS pages (
                    partition TEXT NOT NULL, url TEXT NOT NULL, sha256 TEXT NOT NULL,
                    next_url TEXT, total INTEGER NOT NULL, observed REAL NOT NULL,
                    PRIMARY KEY(partition, url, sha256));
                CREATE TABLE IF NOT EXISTS events (
                    source_id TEXT, status TEXT NOT NULL, detail TEXT,
                    observed REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS control (
                    key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS publications (
                    batch TEXT PRIMARY KEY, revision TEXT NOT NULL,
                    repo TEXT NOT NULL, status TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS members (
                    source_id TEXT NOT NULL, sha256 TEXT NOT NULL,
                    record_sha256 TEXT NOT NULL, batch TEXT NOT NULL,
                    PRIMARY KEY(source_id,sha256,record_sha256,batch));
                CREATE TABLE IF NOT EXISTS observations (
                    source_id TEXT NOT NULL, url TEXT NOT NULL,
                    sha256 TEXT NOT NULL, record_sha256 TEXT NOT NULL,
                    record TEXT NOT NULL, observed REAL NOT NULL,
                    PRIMARY KEY(source_id,url,sha256,record_sha256));
            """)
            version = connection.execute(
                "SELECT value FROM control WHERE key='schema_version'"
            ).fetchone()
            if version is None:
                # Preserve the pilot's original record snapshot once. Future
                # metadata changes must never be joined onto earlier bytes.
                for row in connection.execute(
                    "SELECT r.record,c.* FROM records r "
                    "JOIN captures c USING(source_id)"
                ).fetchall():
                    connection.execute(
                        "INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?)",
                        (
                            row["source_id"],
                            row["url"],
                            row["sha256"],
                            hashlib.sha256(row["record"].encode()).hexdigest(),
                            row["record"],
                            row["observed"],
                        ),
                    )
                connection.execute("INSERT INTO control VALUES('schema_version','2')")
            elif version["value"] != "2":
                message = "unsupported_parliament_state_version"
                raise ValueError(message)

    def _checkpoint(self, stage: str, detail: dict[str, object]) -> None:
        if self.checkpoint is not None:
            self.checkpoint(stage, detail)

    def _guard(self) -> None:
        if (self.root / "hosted-authority.json").exists() and self.guard is None:
            message = "hosted_authority_requires_fenced_controller"
            raise ValueError(message)
        if self.guard is not None:
            self.guard()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @contextmanager
    def lease(self) -> Iterator[None]:
        """Fence local writers and recover abandoned SQL ownership after a crash."""
        self._guard()
        owner = uuid.uuid4().hex
        with (self.root / "writer.lock").open("a+b") as handle:
            if handle.tell() == 0:
                handle.write(b"0")
                handle.flush()
            try:
                file_lock(handle)
            except OSError:
                message = "writer_busy"
                raise ValueError(message) from None
            try:
                with self._connection() as connection:
                    connection.execute(
                        "INSERT OR REPLACE INTO control VALUES (?, ?)",
                        ("writer", owner),
                    )
                yield
            finally:
                with self._connection() as connection:
                    connection.execute(
                        "DELETE FROM control WHERE key=? AND value=?",
                        ("writer", owner),
                    )
                file_lock(handle, release=True)

    def enqueue(
        self, records: tuple[Record, ...], *, partition: str, evidence: bytes
    ) -> None:
        """Persist candidate shard and original discovery evidence before admission."""
        with self.lease():
            self._enqueue(records, partition=partition, evidence=evidence)

    def _enqueue(
        self, records: tuple[Record, ...], *, partition: str, evidence: bytes
    ) -> None:
        records = tuple(
            replace(
                record,
                url=safe_url(record.url),
                attachments=tuple(safe_url(url) for url in record.attachments),
            )
            for record in records
        )
        proof = self.store.put_bytes(evidence)
        shard = _json(
            {
                "schema_version": "parliament-candidates/v1",
                "partition": partition,
                "discovery_sha256": proof.sha256,
                "records": [asdict(record) for record in records],
            }
        )
        digest = hashlib.sha256(shard).hexdigest()
        _atomic(self.root / "candidates" / (digest + ".json"), shard)
        with self._connection() as connection:
            for record in records:
                safe_url(record.url)
                for url in record.attachments:
                    safe_url(url)
                previous = connection.execute(
                    "SELECT record FROM records WHERE source_id=?", (record.source_id,)
                ).fetchone()
                value = _json(asdict(record)).decode()
                state = "metadata_only" if record.metadata_only else "pending"
                if previous is None:
                    connection.execute(
                        "INSERT INTO records(source_id,record,partition,status) "
                        "VALUES(?,?,?,?)",
                        (record.source_id, value, partition, state),
                    )
                elif (
                    _json(asdict(Record(**json.loads(previous["record"]))))
                    != value.encode()
                ):
                    connection.execute(
                        "UPDATE records SET record=?,status=? WHERE source_id=?",
                        (value, state, record.source_id),
                    )
                    connection.execute(
                        "INSERT INTO events VALUES(?,?,?,?)",
                        (record.source_id, "metadata_changed", digest, time.time()),
                    )

    async def _permit(self, client: httpx.AsyncClient, url: str) -> None:
        self._guard()
        if self.source_guard is not None:
            self.source_guard()
        url = safe_url(url)
        with self._connection() as connection:
            cooldown = connection.execute(
                "SELECT value FROM control WHERE key='defer_until'"
            ).fetchone()
        if cooldown and float(cooldown["value"]) > time.time():
            message = "source_cooldown"
            raise ValueError(message)
        host = urlsplit(url).netloc
        robots_url = f"https://{host}/robots.txt"
        await self._pace()
        async with client.stream(
            "GET",
            robots_url,
            follow_redirects=False,
            headers={"User-Agent": USER_AGENT},
            timeout=30,
        ) as response:
            await self._response(response)
            if response.status_code != httpx.codes.OK:
                message = "robots_unavailable"
                raise ValueError(message)
            body = bytearray()
            async for chunk in response.aiter_bytes():
                body.extend(chunk)
                if len(body) > 128 * 1024:
                    message = "robots_oversize"
                    raise ValueError(message)
        parser = RobotFileParser()
        parser.parse(body.decode("utf-8", errors="replace").splitlines())
        if not parser.can_fetch(USER_AGENT, url):
            message = "robots_denied"
            raise ValueError(message)
        delay = parser.crawl_delay(USER_AGENT)
        await self._pace(float(delay) if delay else self.delay)

    async def _response(self, response: httpx.Response) -> None:
        if response.status_code not in {
            httpx.codes.TOO_MANY_REQUESTS,
            httpx.codes.SERVICE_UNAVAILABLE,
        }:
            return
        value = response.headers.get("retry-after", "60")
        try:
            seconds = float(value)
            until = time.time() + max(60, seconds)
        except ValueError:
            try:
                until = max(time.time() + 60, parsedate_to_datetime(value).timestamp())
            except ValueError, TypeError, OverflowError:
                until = time.time() + 60
        with self._connection() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO control VALUES('defer_until',?)",
                (str(until),),
            )

    async def _pace(self, delay: float | None = None) -> None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT value FROM control WHERE key='last_request'"
            ).fetchone()
        last = float(row["value"]) if row else 0
        await asyncio.sleep(max(0, last + max(self.delay, delay or 0) - time.time()))
        with self._connection() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO control VALUES('last_request',?)",
                (str(time.time()),),
            )

    async def discover(
        self, client: httpx.AsyncClient, url: str, *, partition: str
    ) -> dict[str, object]:
        """Admit one observed listing page; never infer exhaustion from an app shell."""
        with self.lease():
            await self._permit(client, url)
            result = await capture_url(
                client,
                safe_url(url),
                self.store,
                CaptureConfig(max_bytes=4 * 1024 * 1024, max_redirects=0),
            )
            page = parse_listing(result.receipt.path.read_text(encoding="utf-8"), url)
            self._enqueue(
                page.records,
                partition=partition,
                evidence=result.receipt.path.read_bytes(),
            )
            with self._connection() as connection:
                connection.execute(
                    "INSERT OR IGNORE INTO pages VALUES(?,?,?,?,?,?)",
                    (
                        partition,
                        url,
                        result.receipt.sha256,
                        page.next_url,
                        page.total,
                        time.time(),
                    ),
                )
            return {
                "discovered": len(page.records),
                "next_url": page.next_url,
                "observed_total": page.total,
                "coverage_claim": False,
            }

    async def reports(
        self,
        client: httpx.AsyncClient,
        *,
        partition: str,
        query: ReportQuery | None = None,
        require_unfiltered: bool = False,
        bounds: Bounds | None = None,
    ) -> dict[str, object]:
        """Persist one qualified report page and its independent durable cursor."""
        active = bounds or Bounds()
        if self._report_limit(active.max_bytes, active.max_spool_bytes) <= 0:
            return self._deferred_report()
        key = "reports:" + partition
        with self.lease():
            if query is None:
                with self._connection() as connection:
                    cursor = connection.execute(
                        "SELECT value FROM control WHERE key=?", (key,)
                    ).fetchone()
                if cursor:
                    value = json.loads(cursor["value"])
                    if require_unfiltered and (
                        value["keyword"] or value["page_size"] != DEFAULT_PAGE_SIZE
                    ):
                        message = "worker_cursor_scope_mismatch"
                        raise ValueError(message)
                    if value["page"] is None:
                        return {
                            "discovered": 0,
                            "observed_exhaustion": True,
                            "coverage_claim": False,
                        }
                    query = ReportQuery(**value)
                else:
                    query = ReportQuery()
            response = await self._report_response(client, query, active)
            if isinstance(response, dict):
                return response
            raw = response
            response_hash = hashlib.sha256(raw).hexdigest()
            response_object = self.store.put_bytes(bytes(raw))
            request = self.store.put_bytes(
                _json(
                    {
                        "endpoint": ENDPOINT,
                        "method": "POST",
                        "body": query.body(),
                        "response_sha256": response_hash,
                        "http_status": 200,
                    }
                )
            )
            try:
                page = parse_reports(json.loads(raw), query)
            except ValueError:
                with self._connection() as connection:
                    connection.execute(
                        "INSERT INTO events VALUES(?,?,?,?)",
                        (None, "discovery_failed", request.sha256, time.time()),
                    )
                raise
            self._enqueue(
                page.records,
                partition=partition,
                evidence=bytes(raw),
            )
            with self._connection() as connection:
                for record in page.records:
                    snapshot = connection.execute(
                        "SELECT record FROM records WHERE source_id=?",
                        (record.source_id,),
                    ).fetchone()["record"]
                    metadata_url = ENDPOINT + "#response=" + response_hash
                    connection.execute(
                        "INSERT INTO captures VALUES(?,?,?,?,?,?) "
                        "ON CONFLICT(source_id,url,sha256) DO UPDATE "
                        "SET observed=excluded.observed",
                        (
                            record.source_id,
                            metadata_url,
                            response_object.sha256,
                            response_object.byte_count,
                            "application/json",
                            time.time(),
                        ),
                    )
                    connection.execute(
                        "INSERT OR IGNORE INTO observations VALUES(?,?,?,?,?,?)",
                        (
                            record.source_id,
                            metadata_url,
                            response_object.sha256,
                            hashlib.sha256(snapshot.encode()).hexdigest(),
                            snapshot,
                            time.time(),
                        ),
                    )
                connection.execute(
                    "INSERT OR IGNORE INTO pages VALUES(?,?,?,?,?,?)",
                    (
                        partition,
                        ENDPOINT + "#request=" + request.sha256,
                        response_hash,
                        str(page.next_page),
                        page.total,
                        time.time(),
                    ),
                )
                connection.execute(
                    "INSERT OR REPLACE INTO control VALUES(?,?)",
                    (
                        key,
                        _json(
                            {
                                "page": page.next_page,
                                "page_size": query.page_size,
                                "keyword": query.keyword,
                            }
                        ).decode(),
                    ),
                )
            result = {
                "discovered": len(page.records),
                "next_page": page.next_page,
                "observed_total": page.total,
                "bytes": len(raw),
                "coverage_claim": False,
            }
            self._checkpoint("reports", result)
            return result

    async def _report_response(
        self, client: httpx.AsyncClient, query: ReportQuery, bounds: Bounds
    ) -> bytes | dict[str, object]:
        """Read only a response whose retained evidence can fit the spool."""
        await self._permit(client, ENDPOINT)
        limit = self._report_limit(bounds.max_bytes, bounds.max_spool_bytes)
        if limit <= 0:
            return self._deferred_report()
        raw = bytearray()
        async with client.stream(
            "POST",
            ENDPOINT,
            json=query.body(),
            headers={"User-Agent": USER_AGENT},
            timeout=30,
            follow_redirects=False,
        ) as response:
            await self._response(response)
            if response.status_code != httpx.codes.OK:
                message = "report_search_failed"
                raise ValueError(message)
            async for chunk in response.aiter_bytes(min(64 * 1024, limit + 1)):
                raw.extend(chunk)
                if len(raw) > limit:
                    if limit < min(4 * 1024 * 1024, bounds.max_bytes):
                        return self._deferred_report(len(raw))
                    message = "report_response_oversize"
                    raise ValueError(message)
        return bytes(raw)

    def _report_limit(self, max_bytes: int, max_spool_bytes: int) -> int:
        # Reserve a complete SQLite rollback journal and fixed bookkeeping.
        # Eight response copies cover CAS staging, candidate JSON, current and
        # immutable record snapshots, and their SQLite/index/temporary overhead.
        available = (
            max_spool_bytes
            - self._spool_bytes()
            - self.database.stat().st_size
            - 4 * STATE_RESERVE_BYTES
        )
        return max(0, min(4 * 1024 * 1024, max_bytes, available // 8))

    @staticmethod
    def _deferred_report(byte_count: int = 0) -> dict[str, object]:
        return {
            "discovered": 0,
            "bytes": byte_count,
            "status": "spool_bound_reached",
            "coverage_claim": False,
        }

    @staticmethod
    def _bound_reached() -> None:
        message = "run_bound_reached"
        raise ValueError(message)

    def _spool_bytes(self) -> int:
        return sum(
            path.stat().st_size for path in self.root.rglob("*") if path.is_file()
        )

    async def capture(
        self, client: httpx.AsyncClient, bounds: Bounds
    ) -> dict[str, object]:
        """Capture a bounded pending queue with zero automatic retries."""
        client.event_hooks["response"].append(self._response)
        try:
            async with asyncio.timeout(bounds.max_seconds):
                return await self._capture(client, bounds)
        finally:
            client.event_hooks["response"].remove(self._response)

    def _resume_url(self, source_id: str, url: str, urls: list[str]) -> bool:
        with self._connection() as connection:
            exists = connection.execute(
                "SELECT sha256,content_type FROM captures WHERE source_id=? "
                "AND url=? AND observed >= COALESCE("
                "(SELECT MAX(observed) FROM events WHERE source_id=? "
                "AND status IN ('metadata_changed','refresh_requested')),0)",
                (source_id, url, source_id),
            ).fetchone()
        if not exists:
            return False
        preserved = self.store.verify("sha256:" + exists["sha256"])
        if "text/html" in (exists["content_type"] or ""):
            links = attachment_links(preserved.path.read_text(encoding="utf-8"), url)
            urls.extend(link for link in links if link not in urls)
        return True

    async def _capture(
        self, client: httpx.AsyncClient, bounds: Bounds
    ) -> dict[str, object]:
        started, used, captured, failed = time.monotonic(), 0, 0, 0
        with self.lease():
            with self._connection() as connection:
                pending = connection.execute(
                    "SELECT * FROM records WHERE status='pending' "
                    "ORDER BY source_id LIMIT ?",
                    (bounds.max_records,),
                ).fetchall()
            for item in pending:
                remaining = bounds.max_seconds - (time.monotonic() - started)
                space = bounds.max_spool_bytes - self._spool_bytes()
                if remaining <= 0 or used >= bounds.max_bytes or space <= 0:
                    break
                record = json.loads(item["record"])
                limit = bounds.max_file_bytes
                try:
                    # Keep the source page as context in addition to attachments.
                    # The API supplies report context. Avoid publishing a
                    # client-rendered HTML shell with transient form tokens.
                    sources = (
                        record["attachments"]
                        if record["kind"] == "report" and record["attachments"]
                        else [record["url"], *record["attachments"]]
                    )
                    urls = list(dict.fromkeys(sources))
                    for url in urls:
                        if self._resume_url(item["source_id"], url, urls):
                            continue
                        await self._permit(client, url)
                        remaining = bounds.max_seconds - (time.monotonic() - started)
                        limit = min(
                            bounds.max_file_bytes,
                            bounds.max_bytes - used,
                            max(
                                0,
                                (
                                    bounds.max_spool_bytes
                                    - self._spool_bytes()
                                    - STATE_RESERVE_BYTES
                                )
                                // 2,
                            ),
                        )
                        if remaining <= 0 or limit <= 0:
                            self._bound_reached()
                        config = CaptureConfig(
                            max_bytes=limit,
                            chunk_bytes=min(64 * 1024, limit),
                            max_duration_seconds=remaining,
                            timeout_seconds=min(30, remaining),
                            max_redirects=0,
                        )
                        async with asyncio.timeout(remaining):
                            result = await capture_url(client, url, self.store, config)
                        used += result.receipt.byte_count
                        if result.content_type and "text/html" in result.content_type:
                            if url != record["url"]:
                                self._attachment_error()
                            links = attachment_links(
                                result.receipt.path.read_text(encoding="utf-8"), url
                            )
                            if not links and record["kind"] in {"submission", "advice"}:
                                self._attachment_error()
                            urls.extend(link for link in links if link not in urls)
                        with self._connection() as connection:
                            connection.execute(
                                "INSERT INTO captures VALUES(?,?,?,?,?,?) "
                                "ON CONFLICT(source_id,url,sha256) DO UPDATE "
                                "SET observed=excluded.observed",
                                (
                                    item["source_id"],
                                    url,
                                    result.receipt.sha256,
                                    result.receipt.byte_count,
                                    result.content_type,
                                    time.time(),
                                ),
                            )
                            connection.execute(
                                "INSERT OR IGNORE INTO observations "
                                "VALUES(?,?,?,?,?,?)",
                                (
                                    item["source_id"],
                                    url,
                                    result.receipt.sha256,
                                    hashlib.sha256(item["record"].encode()).hexdigest(),
                                    item["record"],
                                    time.time(),
                                ),
                            )
                            connection.execute(
                                "INSERT INTO events VALUES(?,?,?,?)",
                                (
                                    item["source_id"],
                                    "captured",
                                    _json(
                                        {
                                            "url": url,
                                            "http_status": result.status_code,
                                            "content_type": result.content_type,
                                            "sha256": result.receipt.sha256,
                                            "blake3": result.receipt.blake3,
                                            "bytes": result.receipt.byte_count,
                                            "duration": result.elapsed_seconds,
                                        }
                                    ).decode(),
                                    time.time(),
                                ),
                            )
                        self._checkpoint(
                            "capture_object", {"bytes": result.receipt.byte_count}
                        )
                    with self._connection() as connection:
                        connection.execute(
                            "UPDATE records SET status='captured',last_error=NULL "
                            "WHERE source_id=?",
                            (item["source_id"],),
                        )
                    self._checkpoint("capture_record", {"captured": 1})
                    captured += 1
                except (
                    CaptureError,
                    ValueError,
                    httpx.HTTPError,
                    TimeoutError,
                ) as error:
                    detail = (
                        error.error_class
                        if isinstance(error, CaptureError)
                        else str(error)
                        if isinstance(error, ValueError)
                        else type(error).__name__
                    )
                    deferred = detail == "run_bound_reached" or (
                        detail in {"size_limit", "decompression_limit"}
                        and limit < bounds.max_file_bytes
                    )
                    with self._connection() as connection:
                        connection.execute(
                            "UPDATE records SET status=?,last_error=? "
                            "WHERE source_id=?",
                            (
                                "pending" if deferred else "failed",
                                None if deferred else detail,
                                item["source_id"],
                            ),
                        )
                        connection.execute(
                            "INSERT INTO events VALUES(?,?,?,?)",
                            (
                                item["source_id"],
                                "deferred" if deferred else "failed",
                                detail,
                                time.time(),
                            ),
                        )
                    failed += int(not deferred)
                    # A failed body may have consumed the remaining transfer
                    # allowance. Defer all further work rather than exceed it.
                    break
            return {
                "captured": captured,
                "failed": failed,
                "bytes": used,
                "coverage_claim": False,
            }

    def summary(self) -> dict[str, object]:
        """Keep capture and verified publication accounting independent."""
        with self._connection() as connection:
            counts = {
                row["status"]: row["n"]
                for row in connection.execute(
                    "SELECT status,COUNT(*) AS n FROM records GROUP BY status"
                )
            }
            last = connection.execute(
                "SELECT last_error AS detail FROM records WHERE status='failed' "
                "AND last_error IS NOT NULL ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
            published = connection.execute(
                "SELECT COUNT(*) FROM publications WHERE status='verified'"
            ).fetchone()[0]
        return {
            "pending": 0,
            "captured": 0,
            "failed": 0,
            **counts,
            "published": published,
            "last_error": last["detail"] if last else None,
            "coverage_claim": False,
        }

    @staticmethod
    def _attachment_error() -> None:
        message = "attachment_contract_unqualified"
        raise ValueError(message)

    def verify(self) -> dict[str, int]:
        """Independently rehash every captured original referenced by the ledger."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT DISTINCT sha256,size FROM captures"
            ).fetchall()
        for row in rows:
            receipt = self.store.verify("sha256:" + row["sha256"])
            if receipt.byte_count != row["size"]:
                message = "capture_size_mismatch"
                raise ValueError(message)
        return {"verified": len(rows)}

    def package(self, decisions: dict[str, dict[str, str]]) -> dict[str, object]:
        """Stage only records with explicit hash-bound publication decisions."""
        validate_decisions(decisions)
        rows = self._package_rows(decisions)
        objects: dict[str, dict[str, object]] = {}
        selected: list[sqlite3.Row] = []
        for row in rows:
            try:
                decision_for(decisions, row["source_id"], row["sha256"])
            except ValueError:
                continue
            selected.append(row)
            objects[row["sha256"]] = {"sha256": row["sha256"], "size": row["size"]}
        if rows and not selected:
            message = "publication_decision_required"
            raise ValueError(message)
        rows = selected
        if sum(int(str(item["size"])) for item in objects.values()) > MAX_BATCH_BYTES:
            message = "batch_byte_limit"
            raise ValueError(message)
        if not rows:
            message = "no_captured_records"
            raise ValueError(message)
        manifest = {
            "schema_version": "parliament-batch/v2",
            "coverage_claim": False,
            "records": [
                {
                    **dict(row),
                    "representation": "source_metadata"
                    if row["url"].startswith(ENDPOINT + "#response=")
                    else "source_payload",
                }
                for row in rows
            ],
            "decisions": decisions,
            "software": {
                "package_version": __version__,
                "python": platform.python_version(),
                "implementation_sha256": self._implementation_hash(),
            },
        }
        validate_manifest(manifest)
        data = _json(manifest)
        batch = hashlib.sha256(data).hexdigest()
        target = self.root / "batches" / batch
        _atomic(target / "manifest.json", data)
        for digest in objects:
            receipt = self.store.verify("sha256:" + digest)
            destination = target / "objects" / digest
            # Hard links avoid a second spool copy; copies are not required.
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                os.link(receipt.path, destination)
        with self._connection() as connection:
            for row in rows:
                connection.execute(
                    "INSERT OR IGNORE INTO members VALUES(?,?,?,?)",
                    (
                        row["source_id"],
                        row["sha256"],
                        hashlib.sha256(row["record"].encode()).hexdigest(),
                        batch,
                    ),
                )
        self._checkpoint("package", {"batch": batch})
        return {"batch": batch, "path": str(target), "object_count": len(objects)}

    def _package_rows(self, decisions: dict[str, dict[str, str]]) -> list[sqlite3.Row]:
        with self._connection() as connection:
            rows: list[sqlite3.Row] = []
            source_ids: set[str] = set()
            for key, decision in decisions.items():
                exact = connection.execute(
                    "SELECT 1 FROM records WHERE source_id=?", (key,)
                ).fetchone()
                source_ids.add(
                    key if exact else key.removesuffix(":" + decision["sha256"])
                )
            if len(source_ids) > MAX_BATCH_RECORDS:
                message = "batch_record_limit"
                raise ValueError(message)
            for source_id in sorted(source_ids):
                rows.extend(self._unpublished(connection, source_id).fetchall())
        return rows

    def publication(self, batch: str) -> dict[str, str] | None:
        """Read the durable uploaded/verified checkpoint for one exact batch."""
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM publications WHERE batch=?", (batch,)
            ).fetchone()
        return dict(row) if row else None

    def requeue(self, source_id: str, *, refresh: bool = False) -> None:
        """Explicitly request one retry or a new immutable content observation."""
        with self.lease(), self._connection() as connection:
            result = connection.execute(
                "UPDATE records SET status='pending',last_error=NULL WHERE source_id=?",
                (source_id,),
            )
            if result.rowcount != 1:
                message = "unknown_source_id"
                raise ValueError(message)
            connection.execute(
                "INSERT INTO events VALUES(?,?,?,?)",
                (
                    source_id,
                    "refresh_requested" if refresh else "retry_requested",
                    None,
                    time.time(),
                ),
            )

    def note_publication(
        self, batch: str, repo: str, revision: str, status: str
    ) -> None:
        """Persist upload and verification stages independently for safe resume."""
        if status not in {"uploaded", "verified"}:
            message = "invalid_publication_status"
            raise ValueError(message)
        if repo != PUBLIC_REPOSITORY:
            message = "publication_target_mismatch"
            raise ValueError(message)
        with self._connection() as connection:
            connection.execute(
                "INSERT OR REPLACE INTO publications VALUES(?,?,?,?)",
                (batch, revision, repo, status),
            )

        self._checkpoint("publication", {"batch": batch, "status": status})

    def report_decisions(self) -> dict[str, dict[str, str]]:
        """Select a bounded report-only batch under Parliament's stated reuse basis."""
        with self._connection() as connection:
            rows = self._unpublished(connection)
            decisions: dict[str, dict[str, str]] = {}
            sizes: dict[str, int] = {}
            selected_sources: set[str] = set()
            for row in rows:
                record = json.loads(row["record"])
                metadata = row["url"].startswith(ENDPOINT + "#response=")
                if record["kind"] != "report" or not (
                    metadata
                    or row["url"].startswith(
                        "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/"
                    )
                ):
                    continue
                if (
                    row["source_id"] not in selected_sources
                    and len(selected_sources) >= MAX_BATCH_RECORDS
                ):
                    break
                sizes[row["sha256"]] = row["size"]
                if sum(sizes.values()) > MAX_BATCH_BYTES:
                    break
                receipt = self.store.verify("sha256:" + row["sha256"])
                if not metadata:
                    with receipt.path.open("rb") as handle:
                        if handle.read(5) != b"%PDF-":
                            message = "report_payload_not_pdf"
                            raise ValueError(message)
                key = row["source_id"] + ":" + row["sha256"]
                decisions[key] = {
                    "sha256": row["sha256"],
                    "basis": (
                        "Official report catalogue metadata. Source: Office of "
                        "the Clerk / Parliamentary Service (New Zealand Parliament). "
                        "Reused under Creative Commons Attribution 4.0 International "
                        "(https://creativecommons.org/licenses/by/4.0/). "
                        "Original API response bytes unchanged."
                    )
                    if metadata
                    else (
                        "Select committee report: Parliament identifies reports of "
                        "select committees as public domain content. "
                        "Source: New Zealand Parliament. Original bytes unchanged."
                    ),
                    "evidence_url": "https://www.parliament.nz/Copyright",
                }
                selected_sources.add(row["source_id"])
                if len(decisions) >= MAX_BATCH_DECISIONS:
                    break
        return decisions

    def pending_report_batch(self) -> str | None:
        """Recover a staged report batch before attempting another native commit."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT DISTINCT m.batch FROM members m "
                "LEFT JOIN publications p USING(batch) "
                "WHERE p.status IS NULL OR p.status!='verified' ORDER BY m.rowid"
            ).fetchall()
        for row in rows:
            batch = str(row["batch"])
            if not re.fullmatch("[0-9a-f]{64}", batch):
                message = "invalid_batch_id"
                raise ValueError(message)
            path = self.root / "batches" / batch / "manifest.json"
            data = path.read_bytes()
            if hashlib.sha256(data).hexdigest() != batch:
                message = "batch_manifest_mismatch"
                raise ValueError(message)
            manifest = json.loads(data)
            validate_manifest(manifest)
            if all(
                json.loads(item["record"])["kind"] == "report"
                and item["url"].startswith(
                    (
                        ENDPOINT + "#response=",
                        "https://selectcommittees.parliament.nz/download/SelectCommitteeReport/",
                    )
                )
                for item in manifest["records"]
            ):
                return batch
        return None

    def verification_failure(self, evidence: dict[str, str]) -> None:
        """Record expected/observed hashes without placing payloads in logs."""
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO events VALUES(?,?,?,?)",
                (None, "verification_failed", _json(evidence).decode(), time.time()),
            )

    @staticmethod
    def _unpublished(
        connection: sqlite3.Connection,
        source_id: str | None = None,
    ) -> sqlite3.Cursor:
        return connection.execute(
            "SELECT o.record,o.source_id,o.url,o.sha256,c.size,"
            "c.content_type,o.observed,r.status AS capture_state FROM observations o "
            "JOIN records r ON r.source_id=o.source_id "
            "JOIN captures c ON c.source_id=o.source_id AND c.url=o.url "
            "AND c.sha256=o.sha256 WHERE (r.status='captured' OR o.url LIKE ?) "
            "AND (? IS NULL OR o.source_id=?) AND NOT EXISTS ("
            "SELECT 1 FROM members m JOIN publications p USING(batch) "
            "WHERE p.status='verified' AND p.repo=? AND m.source_id=o.source_id "
            "AND m.sha256=o.sha256 AND m.record_sha256=o.record_sha256) "
            "ORDER BY o.source_id,o.url,o.sha256,o.record_sha256",
            (ENDPOINT + "#response=%", source_id, source_id, PUBLIC_REPOSITORY),
        )

    @staticmethod
    def _implementation_hash() -> str:
        source = files("archive_govt_nz.parliament")
        entries = sorted(
            (item.name, hashlib.sha256(item.read_bytes()).hexdigest())
            for item in source.iterdir()
            if item.name.endswith((".py", ".json"))
        )
        return hashlib.sha256(_json(entries)).hexdigest()
