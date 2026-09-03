"""Bounded Budget canonical export acceptance tests."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Protocol

import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_budget_classification import inputs

from archive_govt_nz.domains.health_appropriations import budget_canonical_export
from archive_govt_nz.domains.health_appropriations.budget_canonical_export import (
    export_budget_appropriations,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema


class _PinnedRoot(Protocol):
    @property
    def descriptor(self) -> int | None: ...


def test_dry_run_write_parity_and_determinism(tmp_path: Path) -> None:
    source = inputs(tmp_path)
    package = tmp_path / "package"
    original = tmp_path / "source.xlsx"
    first = tmp_path / "first"
    plan = export_budget_appropriations(
        package, source["manifest_sha256"], original, first
    )
    assert plan["status"] == "planned"
    assert not first.exists()
    persisted = export_budget_appropriations(
        package, source["manifest_sha256"], original, first, dry_run=False
    )
    second = tmp_path / "second"
    export_budget_appropriations(
        package, source["manifest_sha256"], original, second, dry_run=False
    )
    assert persisted["status"] == "passed"
    assert [entry["sha256"] for entry in plan["files"]] == [
        entry["sha256"] for entry in persisted["files"]
    ]
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    assert {path.name for path in first.iterdir()} == {
        "appropriation_fact.parquet",
        "classification_dimension.parquet",
        "field_lineage.parquet",
        "projection_receipt.json",
        "lineage_accounting.jsonl",
        "LOCAL_BUDGET.json",
    }
    marker = json.loads((first / "LOCAL_BUDGET.json").read_bytes())
    assert marker["publication_approval"] == "not_granted"
    assert marker["rights_state"] == "not_evaluated"
    assert (
        marker["original_sha256"] == hashlib.sha256(original.read_bytes()).hexdigest()
    )
    assert len(marker["files"]) == 5
    for name in ("appropriation_fact", "classification_dimension", "field_lineage"):
        table = pq.read_table(first / f"{name}.parquet")
        assert table.schema.equals(recordset_schema(name), check_metadata=True)


@pytest.mark.parametrize("change", ["pin", "package", "original", "existing"])
def test_input_failures_create_no_output(tmp_path: Path, change: str) -> None:
    source = inputs(tmp_path)
    package = tmp_path / "package"
    original = tmp_path / "source.xlsx"
    pin = source["manifest_sha256"]
    output = tmp_path / "output"
    if change == "pin":
        pin = "a" * 64
    elif change == "package":
        (package / "budget_facts.parquet").write_bytes(b"bad")
    elif change == "original":
        original.write_bytes(b"bad")
    else:
        output.mkdir()
    with pytest.raises(ValueError, match=r"^budget_canonical_export_input$"):
        export_budget_appropriations(package, pin, original, output, dry_run=False)
    assert change == "existing" or not output.exists()


@pytest.mark.parametrize("value", [None, 0, 1, "true"])
def test_dry_run_is_a_literal_boolean(tmp_path: Path, value: object) -> None:
    source = inputs(tmp_path)
    with pytest.raises(ValueError, match=r"^budget_canonical_export_input$"):
        export_budget_appropriations(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            tmp_path / "output",
            dry_run=value,  # type: ignore[arg-type]
        )


def test_write_failure_retains_partial_state_and_failure_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"
    real_write = budget_canonical_export._write  # noqa: SLF001 - failure injection

    def fail_second(root: object, name: str, payload: bytes) -> None:
        if name == "classification_dimension.parquet":
            message = "injected"
            raise OSError(message)
        real_write(root, name, payload)  # type: ignore[arg-type]

    monkeypatch.setattr(budget_canonical_export, "_write", fail_second)
    with pytest.raises(ValueError, match=r"^budget_canonical_export_write$"):
        export_budget_appropriations(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=False,
        )
    assert output.is_dir()
    assert (output / "FAILURE.json").is_file()
    assert not (output / "LOCAL_BUDGET.json").exists()


def test_output_reservation_failure_is_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)

    def fail_mkdir(_path: Path) -> None:
        message = "injected"
        raise OSError(message)

    monkeypatch.setattr(Path, "mkdir", fail_mkdir)
    with pytest.raises(ValueError, match=r"^budget_canonical_export_reserve$"):
        export_budget_appropriations(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            tmp_path / "output",
            dry_run=False,
        )


def test_pin_failure_closes_descriptor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    real_close = os.close
    closed: list[int] = []

    def fail_fstat(_descriptor: int) -> os.stat_result:
        message = "injected"
        raise OSError(message)

    def observe_close(descriptor: int) -> None:
        closed.append(descriptor)
        real_close(descriptor)

    monkeypatch.setattr(os, "fstat", fail_fstat)
    monkeypatch.setattr(os, "close", observe_close)
    with pytest.raises(ValueError, match=r"^budget_canonical_export_write$"):
        export_budget_appropriations(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            tmp_path / "output",
            dry_run=False,
        )
    assert len(closed) == 1


def test_keyboard_interrupt_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)

    real_write = budget_canonical_export._write  # noqa: SLF001 - failure injection
    interrupted = False

    def interrupt(root: object, name: str, payload: bytes) -> None:
        nonlocal interrupted
        if not interrupted:
            interrupted = True
            raise KeyboardInterrupt
        real_write(root, name, payload)  # type: ignore[arg-type]

    monkeypatch.setattr(budget_canonical_export, "_write", interrupt)
    with pytest.raises(KeyboardInterrupt):
        export_budget_appropriations(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            tmp_path / "output",
            dry_run=False,
        )


def test_descriptorless_fallback_round_trip(tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    status = output.stat()
    root = budget_canonical_export._PinnedDirectory(  # noqa: SLF001
        output, (status.st_dev, status.st_ino), None
    )
    files = {"receipt.json": b"{}\n"}

    budget_canonical_export._write(root, "receipt.json", files["receipt.json"])  # noqa: SLF001
    budget_canonical_export._readback(root, files)  # noqa: SLF001


def test_reserved_directory_replacement_cannot_mutate_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    package = tmp_path / "package"
    original = tmp_path / "source.xlsx"
    before = {path.name: path.read_bytes() for path in package.iterdir()}
    output = tmp_path / "output"
    moved = tmp_path / "moved-output"
    real_pin = budget_canonical_export._pin  # noqa: SLF001 - race injection

    def replace_after_pin(path: Path) -> _PinnedRoot:
        root = real_pin(path)
        path.rename(moved)
        try:
            path.symlink_to(package, target_is_directory=True)
        except OSError:
            if root.descriptor is not None:
                os.close(root.descriptor)
            pytest.skip("directory symlink creation unavailable")
        return root

    monkeypatch.setattr(budget_canonical_export, "_pin", replace_after_pin)
    with pytest.raises(ValueError, match=r"^budget_canonical_export_write$"):
        export_budget_appropriations(
            package,
            source["manifest_sha256"],
            original,
            output,
            dry_run=False,
        )
    assert {path.name: path.read_bytes() for path in package.iterdir()} == before
    assert not (package / "FAILURE.json").exists()
    assert not (package / "LOCAL_BUDGET.json").exists()
