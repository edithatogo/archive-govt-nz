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
