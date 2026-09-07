"""Bounded five-table parity oracle; explanations never authorize repairs."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from typing import TYPE_CHECKING, Any

from archive_govt_nz.domains.health_appropriations.gold import _TABLE_DEFINITIONS

if TYPE_CHECKING:
    from pathlib import Path

MAX_BYTES = 16 * 1024 * 1024
MAX_ROWS = 10000
DONOR_COUNTS = {
    "gdp_historical": 53,
    "health_spending_summary_befu25_data_expense_tables": 10,
    "health_spending_summary_hyefu24_data_expense_tables": 10,
    "historical_health_spending": 24,
    "recent_health_appropriations": 215,
}
_DIGEST = re.compile(r"[0-9a-f]{64}")


def _hash(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


@dataclass(frozen=True)
class Database:
    """Verified byte identity and ordered, typed row digests only."""

    sha256: str
    tables: tuple[tuple[str, tuple[str, ...]], ...]


@dataclass(frozen=True)
class Repair:
    """Exact mismatch explanation with source location and executable reference.

    This is evidence accounting, not approval or proof that a test was run.
    Callers retain the test result and verify source lineage independently.
    """

    mismatch_id: str
    source_sha256: str
    source_coordinate: str
    rationale: str
    test_reference: str

    def __post_init__(self) -> None:
        """Reject explanations without the required evidence fields."""
        if (
            _DIGEST.fullmatch(self.mismatch_id) is None
            or _DIGEST.fullmatch(self.source_sha256) is None
            or not self.source_coordinate.strip()
            or not self.rationale.strip()
            or "::" not in self.test_reference
        ):
            message = "invalid_repair"
            raise ValueError(message)


def _row_digest(row: tuple[Any, ...]) -> str:
    cells = []
    for value in row:
        if isinstance(value, float):
            if not math.isfinite(value):
                message = "nonfinite_database_value"
                raise ValueError(message)
            token = value.hex()
        elif isinstance(value, bytes):
            token = value.hex()
        else:
            token = value
        cells.append((type(value).__name__, token))
    return _hash(cells)


def read_database(path: Path, expected_sha256: str) -> Database:
    """Read capped bytes once; inspect an in-memory, query-only SQLite copy.

    Exact schema and row bounds fail closed. No source URI is opened by SQLite,
    so no journal or sidecar can be created and filename metacharacters are inert.
    Input fixity identifies the bytes read, not future filesystem state. Native
    SQLite parsing is bounded but is not a hostile-parser process sandbox.
    """
    with path.open("rb") as stream:
        payload = stream.read(MAX_BYTES + 1)
    if len(payload) > MAX_BYTES:
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
        connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_BYTES)
        # Bound VM work as well as returned rows, including integrity checks.
        connection.set_progress_handler(lambda: 1, 1000000)
        if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
            message = "database_integrity"
            raise ValueError(message)
        objects = connection.execute(
            "SELECT name, type FROM sqlite_master ORDER BY name"
        ).fetchall()
        if objects != [(name, "table") for name in sorted(_TABLE_DEFINITIONS)]:
            message = "database_table_drift"
            raise ValueError(message)
        tables = []
        total = 0
        for table, columns in sorted(_TABLE_DEFINITIONS.items()):
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
            ).fetchmany(MAX_ROWS + 1)
            total += len(rows)
            if total > MAX_ROWS:
                message = "database_row_limit"
                raise ValueError(message)
            tables.append((table, tuple(_row_digest(row) for row in rows)))
        return Database(digest, tuple(tables))
    finally:
        connection.close()


def compare_databases(
    donor: Database,
    candidate: Database,
    *,
    repairs: tuple[Repair, ...] = (),
) -> dict[str, Any]:
    """Account for every row occurrence, ignoring insertion order, never values.

    Type-tagged cell hashes retain REAL binary identity, NULL, text and duplicate
    multiplicity. Replacements produce donor-only and candidate-only entries;
    neither side disappears behind a heuristic key or numeric tolerance.
    Mismatch IDs bind both file hashes, table, row ordinal and row content.
    """
    left, right = dict(donor.tables), dict(candidate.tables)
    if set(left) != set(DONOR_COUNTS) or set(right) != set(DONOR_COUNTS):
        message = "comparison_table_drift"
        raise ValueError(message)
    explanations = {repair.mismatch_id: repair for repair in repairs}
    if len(explanations) != len(repairs):
        message = "unused_or_duplicate_repair"
        raise ValueError(message)
    rows = []
    matched = 0
    unresolved = 0
    counts = {}
    for table in sorted(left):
        available: dict[str, deque[int]] = defaultdict(deque)
        for number, digest in enumerate(right[table], 1):
            available[digest].append(number)
        pairs: list[tuple[int | None, int | None, str]] = []
        for number, digest in enumerate(left[table], 1):
            target = available[digest].popleft() if available[digest] else None
            pairs.append((number, target, digest))
        pairs.extend(
            (None, number, digest)
            for digest, numbers in sorted(available.items())
            for number in numbers
        )
        for origin, target, digest in pairs:
            status = (
                "match"
                if origin is not None and target is not None
                else "donor_only"
                if origin is not None
                else "candidate_only"
            )
            identity = _hash(
                [donor.sha256, candidate.sha256, table, origin, target, digest]
            )
            repair = explanations.pop(identity, None) if status != "match" else None
            matched += status == "match"
            unresolved += status != "match" and repair is None
            rows.append(
                {
                    "id": identity,
                    "table": table,
                    "donor_row": origin,
                    "candidate_row": target,
                    "row_sha256": digest,
                    "status": status,
                    "repair": asdict(repair) if repair else None,
                }
            )
        counts[table] = {"donor": len(left[table]), "candidate": len(right[table])}
    if explanations:
        message = "unused_or_duplicate_repair"
        raise ValueError(message)
    return {
        "schema_version": "archive-govt-nz.health-donor-parity/v1",
        "donor_sha256": donor.sha256,
        "candidate_sha256": candidate.sha256,
        "pinned_donor_counts": {key: len(left[key]) for key in left} == DONOR_COUNTS,
        "table_counts": counts,
        "matched_rows": matched,
        "unresolved_rows": unresolved,
        "explained_rows": len(repairs),
        "status": "unresolved"
        if unresolved
        else "explained_deviations"
        if repairs
        else "exact_parity",
        "repair_approval": "not_asserted",
        "rows": rows,
    }
