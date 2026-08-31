"""Transactional local snapshots; not a cross-repository ownership authority."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, NoReturn

if TYPE_CHECKING:
    from pathlib import Path


def _fail(reason: str) -> NoReturn:
    raise ValueError(reason)


def _canonical(document: dict[str, Any]) -> str:
    return json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(key: str, version: int, document: str, previous: str) -> str:
    return hashlib.sha256(
        _canonical(
            {"key": key, "version": version, "document": document, "previous": previous}
        ).encode()
    ).hexdigest()


@dataclass(frozen=True)
class StoredState:
    """A decoded version and its integrity digest, detached from the database."""

    version: int
    document: dict[str, Any]
    sha256: str


class StateStore:
    """Bounded append-only JSON history with transactional version comparison.

    Sharing a filename across machines does not make this a remote fence. All
    participating local writers must use this store; an external owner token
    and sink-side checks remain necessary for a distributed archive.
    """

    def __init__(
        self,
        path: Path,
        *,
        max_document_bytes: int = 1024 * 1024,
        max_versions: int = 10000,
        max_history_bytes: int = 16 * 1024 * 1024,
    ) -> None:
        """Open a bounded local state database without trusting an existing link."""
        if (
            type(max_document_bytes) is not int
            or max_document_bytes < 1
            or type(max_versions) is not int
            or max_versions < 1
            or type(max_history_bytes) is not int
            or max_history_bytes < 1
        ):
            _fail("state_budget")
        if path.is_symlink():
            _fail("state_path")
        self.path = path
        self.max_document_bytes = max_document_bytes
        self.max_versions = max_versions
        self.max_history_bytes = max_history_bytes
        with closing(sqlite3.connect(path, timeout=5)) as connection, connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS snapshots ("
                "name TEXT NOT NULL, version INTEGER NOT NULL, document TEXT NOT NULL, "
                "previous TEXT NOT NULL, digest TEXT NOT NULL, "
                "PRIMARY KEY(name, version))"
            )

            connection.execute(
                "CREATE TABLE IF NOT EXISTS heads ("
                "name TEXT PRIMARY KEY, version INTEGER NOT NULL, "
                "digest TEXT NOT NULL, total_bytes INTEGER NOT NULL)"
            )

    @staticmethod
    def _key(key: str) -> None:
        if not isinstance(key, str) or not re.fullmatch(
            r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", key
        ):
            _fail("state_key")

    def _history(
        self, connection: sqlite3.Connection, key: str, *, retain: bool = False
    ) -> tuple[list[StoredState], int]:
        count, total, largest, malformed = connection.execute(
            "SELECT COUNT(*), COALESCE(SUM(length(CAST(document AS BLOB))),0), "
            "COALESCE(MAX(length(CAST(document AS BLOB))),0), "
            "COALESCE(SUM(typeof(document) != 'text' OR length(previous) > 64 "
            "OR length(digest) != 64),0) FROM snapshots WHERE name=?",
            (key,),
        ).fetchone()
        if count > self.max_versions or total > self.max_history_bytes:
            _fail("state_history_budget")
        if largest > self.max_document_bytes or malformed:
            _fail("state_integrity")
        head = connection.execute(
            "SELECT version, digest, total_bytes FROM heads WHERE name=?", (key,)
        ).fetchone()
        if (head is None) != (count == 0):
            _fail("state_integrity")
        result: list[StoredState] = []
        prior = ""
        rows = connection.execute(
            "SELECT version, document, previous, digest FROM snapshots "
            "WHERE name=? ORDER BY version",
            (key,),
        )
        for expected, (version, document, previous, digest) in enumerate(rows, 1):
            if (
                version != expected
                or previous != prior
                or digest != _digest(key, version, document, previous)
            ):
                _fail("state_integrity")
            try:
                value = json.loads(document)
                valid = isinstance(value, dict) and _canonical(value) == document
            except (ValueError, TypeError) as error:
                message = "state_integrity"
                raise ValueError(message) from error
            if not valid:
                _fail("state_integrity")
            if not retain:
                result.clear()
            result.append(StoredState(version, value, digest))
            prior = digest
        if head is not None and head != (count, prior, total):
            _fail("state_integrity")
        return result, total

    def history(self, key: str) -> list[StoredState]:
        """Verify every retained version within a consistent read transaction."""
        self._key(key)
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN")
            return self._history(connection, key, retain=True)[0]

    def read(self, key: str) -> StoredState | None:
        """Verify history incrementally and return only its latest snapshot."""
        self._key(key)
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN")
            history, _ = self._history(connection, key)
            return history[-1] if history else None

    def compare_and_swap(
        self,
        key: str,
        expected_version: int | None,
        document: dict[str, Any],
    ) -> StoredState:
        """Append under SQLite's write lock only when the expected head matches."""
        self._key(key)
        if expected_version is not None and (
            type(expected_version) is not int or expected_version < 1
        ):
            _fail("state_version")
        try:
            if not isinstance(document, dict):
                _fail("state_document")
            encoded = _canonical(document)
        except (ValueError, TypeError) as error:
            message = "state_document"
            raise ValueError(message) from error
        if len(encoded.encode()) > self.max_document_bytes:
            _fail("state_document")
        with closing(sqlite3.connect(self.path, timeout=5)) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            history, total = self._history(connection, key)
            latest = history[-1] if history else None
            if (latest.version if latest else None) != expected_version:
                _fail("state_conflict")
            if (latest is not None and latest.version >= self.max_versions) or (
                total + len(encoded.encode()) > self.max_history_bytes
            ):
                _fail("state_history_budget")
            version = latest.version + 1 if latest else 1
            previous = latest.sha256 if latest else ""
            digest = _digest(key, version, encoded, previous)
            connection.execute(
                "INSERT INTO snapshots VALUES (?, ?, ?, ?, ?)",
                (key, version, encoded, previous, digest),
            )
            connection.execute(
                "INSERT INTO heads VALUES (?, ?, ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET version=excluded.version, "
                "digest=excluded.digest, total_bytes=excluded.total_bytes",
                (key, version, digest, total + len(encoded.encode())),
            )
        return StoredState(version, json.loads(encoded), digest)
