"""Synthetic row-level parity contracts, with no retained donor payloads."""

import hashlib
import sqlite3
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from archive_govt_nz.domains.health_appropriations import donor_parity, donor_sqlite
from archive_govt_nz.domains.health_appropriations.donor_parity import (
    Database,
    Repair,
    compare_databases,
    read_database,
)
from archive_govt_nz.domains.health_appropriations.gold import _TABLE_DEFINITIONS


def database(path: Path, *, extra: bool = False) -> str:
    with closing(sqlite3.connect(path)) as connection, connection:
        for table, columns in _TABLE_DEFINITIONS.items():
            definition = ",".join(f'"{name}" {kind}' for name, kind in columns)
            connection.execute(f'CREATE TABLE "{table}" ({definition})')
            values = (
                (2020, "D", "A", "F", 4, "Actual", "P")
                if len(columns) == 7
                else (2020, 4)
            )
            marks = ",".join("?" for _ in values)
            connection.execute(f'INSERT INTO "{table}" VALUES ({marks})', values)
        if extra:
            connection.execute(
                "INSERT INTO historical_health_spending VALUES (2021, 5)"
            )
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_identical_rows_and_deterministic_receipt(tmp_path: Path) -> None:
    path = tmp_path / "donor # %23.sqlite"
    pin = database(path)
    snapshot = read_database(path, pin)
    result = compare_databases(snapshot, snapshot)
    assert result == compare_databases(snapshot, snapshot)
    assert result["matched_rows"] == 5
    assert result["unresolved_rows"] == 0
    assert result["status"] == "exact_parity"
    assert len(result["rows"]) == 5
    assert hashlib.sha256(path.read_bytes()).hexdigest() == pin


def test_generated_column_is_rejected_before_row_query(tmp_path: Path) -> None:
    path = tmp_path / "generated.sqlite"
    database(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "ALTER TABLE historical_health_spending ADD COLUMN surprise BLOB "
            "GENERATED ALWAYS AS (zeroblob(1024)) VIRTUAL"
        )
    pin = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="database_column_drift"):
        read_database(path, pin)


def test_extra_row_requires_exact_test_backed_repair(tmp_path: Path) -> None:
    donor = tmp_path / "donor.sqlite"
    candidate = tmp_path / "candidate.sqlite"
    left = read_database(donor, database(donor))
    right = read_database(candidate, database(candidate, extra=True))
    result = compare_databases(left, right)
    mismatch = next(row for row in result["rows"] if row["status"] == "candidate_only")
    assert result["unresolved_rows"] == 1
    repair = Repair(
        mismatch["id"],
        "a" * 64,
        "sheet:Health/cell:H9",
        "Restore an annotated year omitted by the donor.",
        "test_donor_parity.py::test_extra_row_requires_exact_test_backed_repair",
    )
    fixed = compare_databases(left, right, repairs=(repair,))
    assert fixed["status"] == "explained_deviations"
    assert fixed["unresolved_rows"] == 0
    assert fixed["matched_rows"] == 5
    with pytest.raises(ValueError, match="unused_or_duplicate_repair"):
        compare_databases(left, left, repairs=(repair,))
    with pytest.raises(ValueError, match="unused_or_duplicate_repair"):
        compare_databases(left, right, repairs=(repair, repair))


def test_bad_pin_and_missing_file_do_not_create_inputs(tmp_path: Path) -> None:
    path = tmp_path / "missing.sqlite"
    with pytest.raises(FileNotFoundError):
        read_database(path, "a" * 64)
    assert not path.exists()
    database(path)
    with pytest.raises(ValueError, match="database_fixity"):
        read_database(path, "a" * 64)


@pytest.mark.parametrize(
    "field",
    [
        "mismatch_id",
        "source_sha256",
        "source_coordinate",
        "rationale",
        "test_reference",
    ],
)
def test_repairs_require_evidence(field: str) -> None:
    values = {
        "mismatch_id": "a" * 64,
        "source_sha256": "b" * 64,
        "source_coordinate": "sheet:S/cell:A1",
        "rationale": "retain source",
        "test_reference": "test_donor_parity.py::test_repairs_require_evidence",
    }
    values[field] = ""
    with pytest.raises(ValueError, match="invalid_repair"):
        Repair(**values)


@pytest.mark.parametrize(
    ("sql", "error"),
    [
        ("DROP TABLE gdp_historical", "database_table_drift"),
        ("CREATE VIEW unexpected AS SELECT 1", "database_table_drift"),
        (
            "ALTER TABLE gdp_historical ADD COLUMN unexpected TEXT",
            "database_column_drift",
        ),
    ],
)
def test_schema_mutants(tmp_path: Path, sql: str, error: str) -> None:
    path = tmp_path / "mutant.sqlite"
    database(path)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(sql)
    with pytest.raises(ValueError, match=error):
        read_database(path, hashlib.sha256(path.read_bytes()).hexdigest())


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE gdp_historical SET NominalGDPMillions=5",
        "UPDATE gdp_historical SET NominalGDPMillions=NULL",
        "UPDATE gdp_historical SET NominalGDPMillions=x'34'",
        "UPDATE recent_health_appropriations SET Department='changed'",
        "DELETE FROM gdp_historical",
        "INSERT INTO gdp_historical SELECT * FROM gdp_historical",
    ],
)
def test_value_and_multiplicity_mutants(tmp_path: Path, sql: str) -> None:
    path = tmp_path / "mutant.sqlite"
    before = read_database(path, database(path))
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(sql)
    after = read_database(path, hashlib.sha256(path.read_bytes()).hexdigest())
    result = compare_databases(before, after)
    assert result["status"] == "unresolved"
    assert result["unresolved_rows"] >= 1
    assert result["explained_rows"] == 0


def test_limits_and_nonfinite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "bounded.sqlite"
    pin = database(path)
    monkeypatch.setattr(donor_parity, "MAX_BYTES", 1)
    with pytest.raises(ValueError, match="database_size_limit"):
        read_database(path, pin)
    monkeypatch.setattr(donor_parity, "MAX_BYTES", 16 * 1024 * 1024)
    monkeypatch.setattr(donor_parity, "MAX_ROWS", 4)
    with pytest.raises(ValueError, match="database_row_limit"):
        read_database(path, pin)
    monkeypatch.setattr(donor_parity, "MAX_ROWS", 10000)
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "UPDATE historical_health_spending SET HealthSpendingMillions=?",
            (float("inf"),),
        )
    with pytest.raises(ValueError, match="nonfinite_database_value"):
        read_database(path, hashlib.sha256(path.read_bytes()).hexdigest())


@given(st.lists(st.integers(min_value=0, max_value=10), max_size=50))
def test_multiset_conservation(values: list[int]) -> None:
    tables = tuple(
        (table, tuple(str(value) for value in values))
        for table in sorted(_TABLE_DEFINITIONS)
    )
    donor = Database("a" * 64, tables)
    candidate = Database(
        "b" * 64, tuple((table, tuple(reversed(rows))) for table, rows in tables)
    )
    result = compare_databases(donor, candidate)
    assert result["matched_rows"] == 5 * len(values)
    assert result["unresolved_rows"] == 0
    for table in _TABLE_DEFINITIONS:
        rows = [row for row in result["rows"] if row["table"] == table]
        assert sorted(row["candidate_row"] for row in rows) == list(
            range(1, len(values) + 1)
        )


def test_comparison_rejects_missing_table() -> None:
    with pytest.raises(ValueError, match="comparison_table_drift"):
        compare_databases(Database("a" * 64, ()), Database("b" * 64, ()))


def test_integrity_failure_closes_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "integrity.sqlite"
    pin = database(path)
    original = sqlite3.connect

    class BrokenIntegrity(sqlite3.Connection):
        def execute(
            self,
            sql: str,
            parameters: Any = (),  # noqa: ANN401
        ) -> sqlite3.Cursor:
            if sql == "PRAGMA integrity_check":
                return super().execute("SELECT 'damaged'")
            return super().execute(sql, parameters)

    def connect(name: str) -> sqlite3.Connection:
        return original(name, factory=BrokenIntegrity)

    # Replace this module's binding only; coverage also uses stdlib SQLite.
    proxy = SimpleNamespace(**{**vars(sqlite3), "connect": connect})
    monkeypatch.setattr(donor_sqlite, "sqlite3", proxy)
    with pytest.raises(ValueError, match="database_integrity"):
        read_database(path, pin)
