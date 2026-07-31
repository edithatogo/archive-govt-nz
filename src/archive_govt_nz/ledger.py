"""Transactional SQLite ledger for resumable archival operations."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path


class LedgerError(RuntimeError):
    """Stable ledger failure class."""

    def __init__(self, error_class: str) -> None:
        self.error_class = error_class
        super().__init__(error_class)


@dataclass(frozen=True, slots=True)
class LedgerCheckpoint:
    """Committed resumability marker."""

    key: str
    value: str


class Ledger:
    """Own a SQLite database with foreign keys and WAL durability."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self._migrate()

    def _migrate(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY);
            INSERT OR IGNORE INTO schema_version(version) VALUES (1);
            CREATE TABLE IF NOT EXISTS observations (
              id TEXT PRIMARY KEY, payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS attempts (
              id TEXT PRIMARY KEY, observation_id TEXT NOT NULL REFERENCES
              observations(id),
              state TEXT NOT NULL, payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS objects (
              object_id TEXT PRIMARY KEY, sha256 TEXT NOT NULL UNIQUE,
              blake3 TEXT NOT NULL, byte_count INTEGER NOT NULL, role TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS versions (
              id TEXT PRIMARY KEY, observation_id TEXT NOT NULL REFERENCES
              observations(id),
              state TEXT NOT NULL, payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS publications (
              id TEXT PRIMARY KEY, version_id TEXT NOT NULL REFERENCES versions(id),
              target TEXT NOT NULL, state TEXT NOT NULL, payload_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
              key TEXT PRIMARY KEY, value TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def close(self) -> None:
        """Commit and close the database connection."""
        self.connection.commit()
        self.connection.close()

    def checkpoint(self, key: str, value: str) -> LedgerCheckpoint:
        """Atomically upsert one resumability marker."""
        if not key.strip():
            raise LedgerError("invalid_checkpoint")
        with self.connection:
            self.connection.execute(
                "INSERT INTO checkpoints(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (key, value),
            )
        return LedgerCheckpoint(key, value)

    def get_checkpoint(self, key: str) -> LedgerCheckpoint | None:
        """Read one checkpoint without exposing unrelated rows."""
        row = self.connection.execute(
            "SELECT key,value FROM checkpoints WHERE key=?", (key,)
        ).fetchone()
        return None if row is None else LedgerCheckpoint(row["key"], row["value"])

    def record_observation(
        self, observation_id: str, payload: dict[str, object]
    ) -> None:
        """Insert an immutable observation, rejecting duplicate identifiers."""
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO observations(id,payload_json) VALUES (?,?)",
                    (observation_id, _canonical(payload)),
                )
        except sqlite3.IntegrityError:
            raise LedgerError("duplicate_observation") from None

    def record_attempt(
        self,
        attempt_id: str,
        observation_id: str,
        state: str,
        payload: dict[str, object],
    ) -> None:
        """Record one capture attempt linked to an observation."""
        self._insert_entity(
            "attempts",
            (attempt_id, observation_id, state, _canonical(payload)),
            "attempt",
        )

    def record_object(
        self, object_id: str, sha256: str, blake3: str, byte_count: int, role: str
    ) -> None:
        """Record one immutable object receipt."""
        if byte_count < 0:
            raise LedgerError("invalid_object")
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO objects(object_id,sha256,blake3,byte_count,role) VALUES (?,?,?,?,?)",
                    (object_id, sha256, blake3, byte_count, role),
                )
        except sqlite3.IntegrityError:
            raise LedgerError("duplicate_object") from None

    def record_version(
        self,
        version_id: str,
        observation_id: str,
        state: str,
        payload: dict[str, object],
    ) -> None:
        """Record one version linked to an observation."""
        self._insert_entity(
            "versions",
            (version_id, observation_id, state, _canonical(payload)),
            "version",
        )

    def record_publication(
        self,
        publication_id: str,
        version_id: str,
        target: str,
        state: str,
        payload: dict[str, object],
    ) -> None:
        """Record one gated publication outcome linked to a version."""
        self._insert_entity(
            "publications",
            (publication_id, version_id, target, state, _canonical(payload)),
            "publication",
        )

    def _insert_entity(
        self, table: str, values: tuple[object, ...], label: str
    ) -> None:
        try:
            with self.connection:
                placeholders = ",".join("?" for _ in values)
                self.connection.execute(
                    f"INSERT INTO {table} VALUES ({placeholders})", values
                )
        except sqlite3.IntegrityError:
            raise LedgerError(f"invalid_or_duplicate_{label}") from None

    def export(self) -> list[dict[str, object]]:
        """Export observations and checkpoints deterministically."""
        rows = self.connection.execute(
            "SELECT id,payload_json FROM observations ORDER BY id"
        ).fetchall()
        return [
            {"id": row["id"], "payload": json.loads(row["payload_json"])}
            for row in rows
        ]


def _canonical(payload: dict[str, object]) -> str:
    return json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
