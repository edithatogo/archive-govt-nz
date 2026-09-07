"""Shared bounded donor-SQLite snapshot admission, independent of layer projections."""

from __future__ import annotations

import hashlib
import sqlite3
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

MAX_BYTES = 16 * 1024 * 1024
MAX_ROWS = 10000

TABLE_DEFINITIONS = {
    "gdp_historical": (
        ("Year", "INTEGER"),
        ("NominalGDPMillions", "INTEGER"),
    ),
    "health_spending_summary_befu25_data_expense_tables": (
        ("Year", "INTEGER"),
        ("HealthSpendingMillions", "INTEGER"),
    ),
    "health_spending_summary_hyefu24_data_expense_tables": (
        ("Year", "INTEGER"),
        ("HealthSpendingMillions", "INTEGER"),
    ),
    "historical_health_spending": (
        ("Year", "INTEGER"),
        ("HealthSpendingMillions", "REAL"),
    ),
    "recent_health_appropriations": (
        ("Year", "INTEGER"),
        ("Department", "TEXT"),
        ("AppropriationName", "TEXT"),
        ("FunctionalClassification", "TEXT"),
        ("AmountThousands", "INTEGER"),
        ("AmountType", "TEXT"),
        ("PortfolioName", "TEXT"),
    ),
}


def read_rows(
    path: Path,
    expected_sha256: str,
    *,
    max_bytes: int = MAX_BYTES,
    max_rows: int = MAX_ROWS,
) -> dict[str, tuple[tuple[Any, ...], ...]]:
    """Read capped bytes once; inspect an in-memory, query-only SQLite copy.

    Exact schema and row bounds fail closed. No source URI is opened by SQLite,
    so no journal or sidecar can be created and filename metacharacters are inert.
    Input fixity identifies the bytes read, not future filesystem state. Native
    SQLite parsing is bounded but is not a hostile-parser process sandbox.
    """
    if max_bytes < 1 or max_rows < 1:
        message = "invalid_database_bound"
        raise ValueError(message)
    with path.open("rb") as stream:
        payload = stream.read(max_bytes + 1)
    if len(payload) > max_bytes:
        message = "database_size_limit"
        raise ValueError(message)
    digest = hashlib.sha256(payload).hexdigest()
    if digest != expected_sha256:
        message = "database_fixity"
        raise ValueError(message)
    connection = sqlite3.connect(":memory:")
    try:
        connection.deserialize(payload)
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA trusted_schema=OFF")
        connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, max_bytes)
        # Bound VM work as well as returned rows, including integrity checks.
        connection.set_progress_handler(lambda: 1, 1000000)
        if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            message = "database_integrity"
            raise ValueError(message)
        objects = connection.execute(
            "SELECT name, type FROM sqlite_master ORDER BY name"
        ).fetchall()
        if objects != [(name, "table") for name in sorted(TABLE_DEFINITIONS)]:
            message = "database_table_drift"
            raise ValueError(message)
        tables: dict[str, tuple[tuple[Any, ...], ...]] = {}
        total = 0
        for table, columns in sorted(TABLE_DEFINITIONS.items()):
            # Names come exclusively from the existing fixed export schema.
            schema = connection.execute(f'PRAGMA table_xinfo("{table}")').fetchall()
            expected = [
                (index, name, kind, 0, None, 0, 0)
                for index, (name, kind) in enumerate(columns)
            ]
            if schema != expected:
                message = "database_column_drift"
                raise ValueError(message)
            rows = connection.execute(
                f'SELECT * FROM "{table}" ORDER BY rowid'  # noqa: S608
            ).fetchmany(max_rows - total + 1)
            total += len(rows)
            if total > max_rows:
                message = "database_row_limit"
                raise ValueError(message)
            tables[table] = tuple(rows)
        return tables
    finally:
        connection.close()
