"""Read-only source inventory handles literal paths and quoted identifiers."""

import sqlite3
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from archive_govt_nz.domains.health_appropriations import formats


def _database(path: Path, table: str = "budget") -> None:
    quoted = '"' + table.replace('"', '""') + '"'
    connection = sqlite3.connect(path)
    try:
        connection.execute(f"CREATE TABLE {quoted} (amount TEXT)")
        connection.executemany(
            f"INSERT INTO {quoted} VALUES (?)", [("1.230",), (None,)]
        )
        connection.commit()
    finally:
        connection.close()


@pytest.mark.parametrize(
    "filename",
    ["source#vintage.sqlite", "source%23vintage.sqlite", "health space.sqlite"],
)
def test_literal_paths_and_original_bytes(tmp_path: Path, filename: str) -> None:
    """URI delimiters must not select or create a different database."""
    path = tmp_path / filename
    _database(path)
    before = {item.name: item.read_bytes() for item in tmp_path.iterdir()}
    result = formats.inventory_sqlite(path)
    assert result["integrity"] == "ok"
    assert cast("list[dict[str, object]]", result["tables"])[0]["row_count"] == 2
    assert {item.name: item.read_bytes() for item in tmp_path.iterdir()} == before


@pytest.mark.parametrize(
    "table", ['budget"quoted', 'budget"; DROP TABLE budget;--', '健康 "費用"', "select"]
)
def test_table_names_are_identifiers(tmp_path: Path, table: str) -> None:
    """Names are quoted as SQLite identifiers, never executable SQL fragments."""
    path = tmp_path / "source.sqlite"
    _database(path, table)
    before = path.read_bytes()
    first = formats.inventory_sqlite(path)
    assert first["tables"] == [
        {
            "name": table,
            "sql": 'CREATE TABLE "' + table.replace('"', '""') + '" (amount TEXT)',
            "row_count": 2,
        }
    ]
    assert formats.inventory_sqlite(path) == first
    assert path.read_bytes() == before


def test_missing_source_is_never_created(tmp_path: Path) -> None:
    """Read-only open fails without creating a source or a truncated alias."""
    with pytest.raises(sqlite3.OperationalError):
        formats.inventory_sqlite(tmp_path / "missing#source.sqlite")
    assert list(tmp_path.iterdir()) == []


def test_connection_cannot_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The actual connection rejects mutation, not just an advertised flag."""
    path = tmp_path / "source.sqlite"
    _database(path)
    real_connect = sqlite3.connect
    connections: list[sqlite3.Connection] = []

    def connect(database: str, *, uri: bool) -> sqlite3.Connection:
        connection = real_connect(database, uri=uri)
        connections.append(connection)
        with pytest.raises(sqlite3.OperationalError, match="readonly"):
            connection.execute("CREATE TABLE forbidden (value TEXT)")
        return connection

    # Limit the spy to the adapter; coverage tools also use sqlite3.connect.
    monkeypatch.setattr(formats, "sqlite3", SimpleNamespace(connect=connect))
    formats.inventory_sqlite(path)
    with pytest.raises(sqlite3.ProgrammingError, match="closed"):
        connections[0].execute("SELECT 1")
