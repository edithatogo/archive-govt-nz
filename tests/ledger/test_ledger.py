"""Operational ledger contracts."""

from pathlib import Path

import pytest

from archive_govt_nz.ledger import Ledger, LedgerError


def test_ledger_migrates_constraints_and_deterministic_export(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "ledger.sqlite")
    ledger.record_observation("b", {"z": 1, "a": "two"})
    ledger.record_observation("a", {"value": 3})
    assert [row["id"] for row in ledger.export()] == ["a", "b"]
    with pytest.raises(LedgerError) as raised:
        ledger.record_observation("a", {"value": 4})
    assert raised.value.error_class == "duplicate_observation"
    ledger.close()


def test_checkpoint_is_resumable_and_updates_transactionally(tmp_path: Path) -> None:
    path = tmp_path / "ledger.sqlite"
    ledger = Ledger(path)
    assert ledger.checkpoint("treasury", "page:0").value == "page:0"
    assert ledger.checkpoint("treasury", "page:25").value == "page:25"
    ledger.close()
    reopened = Ledger(path)
    checkpoint = reopened.get_checkpoint("treasury")
    assert checkpoint is not None
    assert checkpoint.value == "page:25"
    reopened.close()


def test_blank_checkpoint_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(LedgerError) as raised:
        Ledger(tmp_path / "ledger.sqlite").checkpoint(" ", "x")
    assert raised.value.error_class == "invalid_checkpoint"
