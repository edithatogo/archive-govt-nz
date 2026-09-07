"""Direct library admission: verified snapshots, exact schema and exclusive output."""

from __future__ import annotations

import hashlib
import io
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
from typing import IO, Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from tests.domains.health_appropriations.test_donor_parity import database

from archive_govt_nz.domains.health_appropriations import donor_sqlite, silver


def normalize(path: Path, output: Path, pin: str | None = None) -> dict[str, object]:
    """Call the library directly, without CLI/CAS pre-verification."""
    return silver.normalize_donor_sqlite(
        path,
        output,
        source_sha256=pin or hashlib.sha256(path.read_bytes()).hexdigest(),
        observation_id="synthetic",
        observed_at="2026-09-07T00:00:00Z",
    )


def test_wrong_hash_rejected_before_output(tmp_path: Path) -> None:
    source = tmp_path / "donor.sqlite"
    database(source)
    with pytest.raises(ValueError, match="database_fixity"):
        normalize(source, tmp_path / "output", "f" * 64)
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "sql",
    [
        "ALTER TABLE gdp_historical ADD COLUMN extra TEXT",
        "ALTER TABLE gdp_historical ADD COLUMN extra INTEGER GENERATED ALWAYS AS (Year+1) VIRTUAL",
        "CREATE VIEW surprise AS SELECT 1",
        "CREATE INDEX surprise ON gdp_historical(Year)",
    ],
)
def test_exact_schema_rejected_before_output(tmp_path: Path, sql: str) -> None:
    source = tmp_path / "donor.sqlite"
    database(source)
    with closing(sqlite3.connect(source)) as connection, connection:
        connection.execute(sql)
    with pytest.raises(ValueError, match=r"database_(column|table)_drift"):
        normalize(source, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_literal_filename_and_unchanged_source(tmp_path: Path) -> None:
    source = tmp_path / "donor # %23.sqlite"
    pin = database(source)
    before = set(tmp_path.iterdir())
    result = normalize(source, tmp_path / "output", pin)
    assert result["record_count"] == 5
    assert hashlib.sha256(source.read_bytes()).hexdigest() == pin
    assert set(tmp_path.iterdir()) == before | {tmp_path / "output"}
    assert set(
        pq.read_table(tmp_path / "output/donor_facts.parquet")[
            "source_object_sha256"
        ].to_pylist()
    ) == {pin}


def test_snapshot_read_is_bounded_before_hashing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "donor.sqlite"
    pin = database(source)
    payload = source.read_bytes()
    reads = []
    original_open = Path.open

    class ObservedReader(io.BytesIO):
        def read(self, size: int | None = -1) -> bytes:
            reads.append(size)
            assert size == len(payload) + 1
            return super().read(size)

    def open_snapshot(path: Path, mode: str = "r") -> IO[Any]:
        return ObservedReader(payload) if path == source else original_open(path, mode)

    monkeypatch.setattr(Path, "open", open_snapshot)
    monkeypatch.setattr(silver, "MAX_BYTES", len(payload))
    assert normalize(source, tmp_path / "output", pin)["record_count"] == 5
    assert reads == [len(payload) + 1]


def test_reserved_directory_does_not_authorize_overwriting_racing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "donor.sqlite"
    pin = database(source)
    output = tmp_path / "output"
    original_mkdir = Path.mkdir

    def racing_mkdir(
        path: Path, mode: int = 0o777, *, parents: bool = False, exist_ok: bool = False
    ) -> None:
        original_mkdir(path, mode, parents=parents, exist_ok=exist_ok)
        if path == output:
            (output / "donor_facts.parquet").write_bytes(b"another writer")

    monkeypatch.setattr(Path, "mkdir", racing_mkdir)
    with pytest.raises(FileExistsError):
        normalize(source, output, pin)
    assert (output / "donor_facts.parquet").read_bytes() == b"another writer"
    assert not (output / "field_lineage.parquet").exists()


@given(extra=st.integers(min_value=0, max_value=12))
@settings(max_examples=13)
def test_aggregate_row_budget_conserves_all_occurrences(extra: int) -> None:
    """The shared admission keeps duplicates and rejects total budget + 1."""
    with tempfile.TemporaryDirectory() as directory:
        source = Path(directory) / "donor.sqlite"
        database(source)
        with closing(sqlite3.connect(source)) as connection, connection:
            connection.executemany(
                "INSERT INTO gdp_historical VALUES (?, ?)", [(2020, 4)] * extra
            )
        pin = hashlib.sha256(source.read_bytes()).hexdigest()
        rows = donor_sqlite.read_rows(source, pin, max_rows=5 + extra)
        assert sum(map(len, rows.values())) == 5 + extra
        assert rows["gdp_historical"] == ((2020, 4),) * (1 + extra)
        with pytest.raises(ValueError, match="database_row_limit"):
            donor_sqlite.read_rows(source, pin, max_rows=4 + extra)


@pytest.mark.parametrize("populated", [False, True])
def test_existing_output_never_reused(tmp_path: Path, *, populated: bool) -> None:
    source = tmp_path / "donor.sqlite"
    database(source)
    output = tmp_path / "output"
    output.mkdir()
    if populated:
        (output / "donor_facts.parquet").write_bytes(b"retained")
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(FileExistsError):
        normalize(source, output)
    assert {p.name: p.read_bytes() for p in output.iterdir()} == before


@pytest.mark.parametrize(
    "definition",
    [
        '"Year" INTEGER, "NominalGDPMillions" INTEGER GENERATED ALWAYS AS (Year+1) STORED',
        '"Year" INTEGER NOT NULL, "NominalGDPMillions" INTEGER',
        '"Year" INTEGER DEFAULT 2020, "NominalGDPMillions" INTEGER',
        '"Year" INTEGER PRIMARY KEY, "NominalGDPMillions" INTEGER',
        '"Year" INTEGER, "NominalGDPMillions" REAL',
        '"NominalGDPMillions" INTEGER, "Year" INTEGER',
    ],
)
def test_complete_column_signature_includes_hidden_and_constraints(
    tmp_path: Path, definition: str
) -> None:
    source = tmp_path / "donor.sqlite"
    database(source)
    with closing(sqlite3.connect(source)) as connection, connection:
        connection.execute("DROP TABLE gdp_historical")
        connection.execute(f"CREATE TABLE gdp_historical ({definition})")
    with pytest.raises(ValueError, match="database_column_drift"):
        normalize(source, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_exact_byte_and_aggregate_row_limits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "donor.sqlite"
    pin = database(source)
    size = source.stat().st_size
    monkeypatch.setattr(silver, "MAX_BYTES", size)
    monkeypatch.setattr(silver, "MAX_ROWS", 5)
    assert normalize(source, tmp_path / "exact", pin)["record_count"] == 5
    monkeypatch.setattr(silver, "MAX_BYTES", size - 1)
    with pytest.raises(ValueError, match="database_size_limit"):
        normalize(source, tmp_path / "large", pin)
    monkeypatch.setattr(silver, "MAX_BYTES", size)
    monkeypatch.setattr(silver, "MAX_ROWS", 4)
    with pytest.raises(ValueError, match="database_row_limit"):
        normalize(source, tmp_path / "many", pin)
    assert not (tmp_path / "large").exists()
    assert not (tmp_path / "many").exists()


@pytest.mark.parametrize("bounds", [{"max_bytes": 0}, {"max_rows": 0}])
def test_invalid_bounds_fail_before_open(
    tmp_path: Path, bounds: dict[str, int]
) -> None:
    with pytest.raises(ValueError, match="invalid_database_bound"):
        donor_sqlite.read_rows(tmp_path / "absent", "a" * 64, **bounds)
    assert not (tmp_path / "absent").exists()


def test_missing_and_corrupt_inputs_create_no_output(tmp_path: Path) -> None:
    source = tmp_path / "missing # %23.sqlite"
    with pytest.raises(FileNotFoundError):
        normalize(source, tmp_path / "output", "a" * 64)
    assert not source.exists()
    source.write_bytes(b"not a database")
    with pytest.raises(sqlite3.DatabaseError):
        normalize(source, tmp_path / "output")
    assert source.read_bytes() == b"not a database"
    assert not (tmp_path / "output").exists()


def test_rows_come_from_one_verified_snapshot_not_reopened_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "donor.sqlite"
    pin = database(source)
    original_connect = sqlite3.connect
    original_open = Path.open
    source_opens = []

    def track_open(
        path: Path,
        mode: str = "r",
    ) -> IO[Any]:
        if path == source:
            source_opens.append(mode)
        return original_open(path, mode)

    def connect(name: str) -> sqlite3.Connection:
        assert name == ":memory:"
        # After snapshot admission, another writer replaces the source bytes.
        with original_open(source, "wb") as handle:
            handle.write(b"later external replacement")
        return original_connect(name)

    monkeypatch.setattr(Path, "open", track_open)
    monkeypatch.setattr(
        donor_sqlite,
        "sqlite3",
        SimpleNamespace(**{**vars(sqlite3), "connect": connect}),
    )
    assert normalize(source, tmp_path / "output", pin)["record_count"] == 5
    assert len(source_opens) == 1
    facts = pq.read_table(tmp_path / "output/donor_facts.parquet").to_pylist()
    assert {row["source_object_sha256"] for row in facts} == {pin}
    assert {row["year"] for row in facts} == {2020}


def test_interrupted_output_retained_and_retry_never_overwrites(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "donor.sqlite"
    pin = database(source)
    output = tmp_path / "output"
    original_write = pq.write_table
    calls = 0

    def interrupted(table: pa.Table, where: IO[bytes], *, compression: str) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            message = "synthetic_output_interruption"
            raise OSError(message)
        original_write(table, where, compression=compression)

    monkeypatch.setattr(silver.pq, "write_table", interrupted)
    with pytest.raises(OSError, match="synthetic_output_interruption"):
        normalize(source, output, pin)
    first = (output / "donor_facts.parquet").read_bytes()
    assert pq.read_table(output / "donor_facts.parquet").num_rows == 5
    monkeypatch.setattr(silver.pq, "write_table", original_write)
    with pytest.raises(FileExistsError):
        normalize(source, output, pin)
    assert (output / "donor_facts.parquet").read_bytes() == first
    assert hashlib.sha256(source.read_bytes()).hexdigest() == pin
