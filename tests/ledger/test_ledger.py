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
    ledger = Ledger(tmp_path / "ledger.sqlite")
    with pytest.raises(LedgerError) as raised:
        ledger.checkpoint(" ", "x")
    assert raised.value.error_class == "invalid_checkpoint"
    ledger.close()


def test_related_entities_are_transactionally_linked(tmp_path: Path) -> None:
    """Attempts, objects, versions, and publications retain relationships."""
    ledger = Ledger(tmp_path / "ledger.sqlite")
    ledger.record_observation("obs", {"dataset": "treasury"})
    ledger.record_attempt("attempt", "obs", "captured", {"status": 200})
    ledger.record_object("sha256:x", "x", "y", 2, "source")
    ledger.record_version("version", "obs", "material", {"object_id": "sha256:x"})
    ledger.record_publication("publication", "version", "huggingface", "prepared", {})
    with pytest.raises(LedgerError) as raised:
        ledger.record_attempt("orphan", "missing", "failed", {})
    assert raised.value.error_class == "invalid_or_duplicate_attempt"
    ledger.close()
