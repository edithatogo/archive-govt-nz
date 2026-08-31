"""Durable local queue snapshots reject stale writers and damaged history."""

import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from threading import Barrier
from typing import TYPE_CHECKING

import pytest

from archive_govt_nz.foi_state import StateStore, _digest

if TYPE_CHECKING:
    from pathlib import Path


def test_reopen_and_stale_writer_preserve_original(tmp_path: Path) -> None:
    """A reopened process sees the committed snapshot and cannot lose an update."""
    path = tmp_path / "state.sqlite"
    first = StateStore(path)
    assert first.read("nz-fyi") is None
    revision = first.compare_and_swap("nz-fyi", None, {"cursor": 0})
    assert revision.version == 1
    second = StateStore(path)
    assert second.read("nz-fyi") == revision
    updated = second.compare_and_swap("nz-fyi", 1, {"cursor": 1})
    with pytest.raises(ValueError, match="state_conflict"):
        first.compare_and_swap("nz-fyi", 1, {"cursor": 900})
    assert first.read("nz-fyi") == updated
    assert len(first.history("nz-fyi")) == 2


def test_only_one_concurrent_writer_commits(tmp_path: Path) -> None:
    """Two independent SQLite connections compare under the same write lock."""
    path = tmp_path / "state.sqlite"
    StateStore(path).compare_and_swap("source", None, {"cursor": 0})
    barrier = Barrier(2)

    def write(cursor: int) -> str:
        store = StateStore(path)
        barrier.wait(timeout=10)
        try:
            store.compare_and_swap("source", 1, {"cursor": cursor})
        except ValueError as error:
            return str(error)
        return "committed"

    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(write, [1, 2]))
    assert sorted(outcomes) == ["committed", "state_conflict"]
    assert len(StateStore(path).history("source")) == 2


def test_corrupt_history_blocks_reads_and_writes(tmp_path: Path) -> None:
    """A damaged earlier snapshot cannot be hidden by a valid-looking latest row."""
    path = tmp_path / "state.sqlite"
    store = StateStore(path)
    store.compare_and_swap("source", None, {"cursor": 0})
    store.compare_and_swap("source", 1, {"cursor": 1})
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute("UPDATE snapshots SET document='{}' WHERE version=1")
    with pytest.raises(ValueError, match="state_integrity"):
        store.read("source")
    with pytest.raises(ValueError, match="state_integrity"):
        store.compare_and_swap("source", 2, {"cursor": 2})


def test_rejected_payload_does_not_advance_version(tmp_path: Path) -> None:
    """Non-finite or oversized payloads leave the previous state intact."""
    store = StateStore(tmp_path / "state.sqlite", max_document_bytes=64)
    original = store.compare_and_swap("source", None, {"cursor": 0})
    for value in [{"value": float("nan")}, {"value": "x" * 100}]:
        with pytest.raises(ValueError, match="state_document"):
            store.compare_and_swap("source", 1, value)
    assert store.read("source") == original


@pytest.mark.parametrize("key", ["", "../source", "x" * 129, None])
def test_invalid_keys_do_not_touch_other_sources(tmp_path: Path, key: str) -> None:
    """State keys are portable identifiers, never paths or unbounded text."""
    store = StateStore(tmp_path / "state.sqlite")
    with pytest.raises(ValueError, match="state_key"):
        store.read(key)


@pytest.mark.parametrize("version", [0, -1, True, "1"])
def test_invalid_versions_are_rejected(tmp_path: Path, version: int) -> None:
    """A boolean or textual version cannot masquerade as a concurrency token."""
    with pytest.raises(ValueError, match="state_version"):
        StateStore(tmp_path / "state.sqlite").compare_and_swap("source", version, {})


@pytest.mark.parametrize(
    "limits",
    [
        {"max_history_bytes": 0},
        {"max_history_bytes": True},
        {"max_versions": 0},
        {"max_versions": True},
        {"max_document_bytes": 0},
        {"max_document_bytes": True},
    ],
)
def test_invalid_limits_are_rejected(tmp_path: Path, limits: dict) -> None:
    """Budgets must be positive integer bounds."""
    with pytest.raises(ValueError, match="state_budget"):
        StateStore(tmp_path / "state.sqlite", **limits)


def test_history_budget_fails_without_deleting_snapshots(tmp_path: Path) -> None:
    """Reaching the cap requires a reviewed continuation strategy, not truncation."""
    path = tmp_path / "state.sqlite"
    store = StateStore(path, max_versions=1)
    first = store.compare_and_swap("source", None, {})
    with pytest.raises(ValueError, match="state_history_budget"):
        store.compare_and_swap("source", 1, {})
    assert store.read("source") == first
    StateStore(path).compare_and_swap("source", 1, {"new": True})
    with pytest.raises(ValueError, match="state_history_budget"):
        store.read("source")


@pytest.mark.parametrize("value", [[], {"invalid": object()}])
def test_invalid_documents_fail_before_transaction(tmp_path: Path, value: dict) -> None:
    """Only JSON objects can become durable scheduler state."""
    store = StateStore(tmp_path / "state.sqlite")
    with pytest.raises(ValueError, match="state_document"):
        store.compare_and_swap("source", None, value)
    assert store.read("source") is None


@pytest.mark.parametrize(
    "document", ["not-json", "[]", '{"x":NaN}', '{"x": 1}', "{}" * 100]
)
def test_even_rehashed_invalid_documents_are_rejected(
    tmp_path: Path, document: str
) -> None:
    """Fixity alone cannot turn malformed or noncanonical data into valid state."""
    path = tmp_path / "state.sqlite"
    store = StateStore(path, max_document_bytes=64)
    store.compare_and_swap("source", None, {})
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "UPDATE snapshots SET document=?,digest=?",
            (
                document,
                _digest("source", 1, document, ""),
            ),
        )
    with pytest.raises(ValueError, match="state_integrity"):
        store.read("source")


def test_symlink_database_is_rejected(tmp_path: Path) -> None:
    """Do not redirect creation through a supplied database symlink."""
    path = tmp_path / "link.sqlite"
    try:
        path.symlink_to(tmp_path / "target.sqlite")
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError, match="state_path"):
        StateStore(path)


@pytest.mark.parametrize(
    "damage",
    [
        "DELETE FROM snapshots WHERE version=2",
        "DELETE FROM snapshots",
        "DELETE FROM heads",
        "UPDATE heads SET version=9",
        "UPDATE heads SET digest='wrong'",
        "UPDATE heads SET total_bytes=999",
        "UPDATE snapshots SET version=3 WHERE version=2",
        "UPDATE snapshots SET previous='wrong' WHERE version=2",
        "UPDATE snapshots SET previous=printf('%100s','x') WHERE version=2",
        "UPDATE snapshots SET document=CAST(document AS BLOB) WHERE version=2",
    ],
)
def test_missing_or_mismatched_head_blocks_recovery(
    tmp_path: Path, damage: str
) -> None:
    """A lost suffix, missing sentinel or altered link cannot rewind a queue."""
    path = tmp_path / "state.sqlite"
    store = StateStore(path)
    store.compare_and_swap("source", None, {"cursor": 0})
    store.compare_and_swap("source", 1, {"cursor": 1})
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(damage)
    with pytest.raises(ValueError, match="state_integrity"):
        StateStore(path).read("source")
    with pytest.raises(ValueError, match="state_integrity"):
        store.compare_and_swap("source", 1, {"cursor": 99})


def test_total_history_budget_rejects_append_and_oversized_reopen(
    tmp_path: Path,
) -> None:
    """Per-key cumulative bytes are capped before fetching payloads into Python."""
    path = tmp_path / "state.sqlite"
    store = StateStore(path, max_history_bytes=4)
    store.compare_and_swap("source", None, {})
    latest = store.compare_and_swap("source", 1, {})
    with pytest.raises(ValueError, match="state_history_budget"):
        store.compare_and_swap("source", 2, {})
    assert store.read("source") == latest
    with pytest.raises(ValueError, match="state_history_budget"):
        StateStore(path, max_history_bytes=3).read("source")


def test_head_write_failure_rolls_back_snapshot(tmp_path: Path) -> None:
    """The snapshot cannot commit without its matching durable sentinel."""
    path = tmp_path / "state.sqlite"
    store = StateStore(path)
    first = store.compare_and_swap("source", None, {})
    with closing(sqlite3.connect(path)) as connection, connection:
        connection.execute(
            "CREATE TRIGGER reject_head BEFORE UPDATE ON heads "
            "BEGIN SELECT RAISE(ABORT, 'injected'); END"
        )
    with pytest.raises(sqlite3.IntegrityError, match="injected"):
        store.compare_and_swap("source", 1, {"cursor": 1})
    assert StateStore(path).history("source") == [first]
