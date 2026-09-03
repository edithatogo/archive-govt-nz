"""Bounded, deterministic local export of canonical Budget appropriations."""

from __future__ import annotations

import hashlib
import json
import os
from decimal import Context, Decimal, Inexact, Rounded, localcontext
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_budget_classification import inputs

from archive_govt_nz.domains.health_appropriations import budget_export
from archive_govt_nz.domains.health_appropriations.budget_export import (
    export_budget_appropriations,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def _args(tmp_path: Path) -> tuple[Path, str, Path, Path]:
    source = inputs(tmp_path)
    return (
        tmp_path / "package",
        source["manifest_sha256"],
        tmp_path / "source.xlsx",
        tmp_path / "output",
    )


def test_dry_run_and_deterministic_write_preserve_inputs(tmp_path: Path) -> None:
    args = _args(tmp_path)
    before = {path: path.read_bytes() for path in [args[2], *args[0].iterdir()]}
    plan = export_budget_appropriations(*args)
    assert plan["status"] == "planned"
    assert plan["hash_state"] == "planned"
    assert not args[3].exists()
    passed = export_budget_appropriations(*args, dry_run=False)
    second = tmp_path / "second"
    export_budget_appropriations(*args[:3], second, dry_run=False)
    assert passed["status"] == "passed"
    assert passed["hash_state"] == "verified_persisted"
    assert {p.name: p.read_bytes() for p in args[3].iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }
    assert {path: path.read_bytes() for path in before} == before
    assert {p.name for p in args[3].iterdir()} == {
        "appropriation_fact.parquet",
        "classification_dimension.parquet",
        "field_lineage.parquet",
        "projection_receipt.json",
        "lineage_accounting.jsonl",
        "LOCAL_BUDGET.json",
    }


def test_exact_descriptor_tables_and_accounting(tmp_path: Path) -> None:
    args = _args(tmp_path)
    export_budget_appropriations(*args, dry_run=False)
    marker = json.loads((args[3] / "LOCAL_BUDGET.json").read_bytes())
    assert marker == {
        **marker,
        "schema_version": budget_export.SCHEMA,
        "transformation_id": "budget-appropriation-canonical/v1",
        "descriptor_state": "verify_all_files_before_use",
        "publication_state": "local_validation_only",
        "rights_state": "not_evaluated",
        "authoritative_mapping": "not_performed",
        "publication_approval": "not_granted",
        "self_contained_archive": False,
        "input_verification": "package_snapshots_and_original_hash",
    }
    assert marker["original_sha256"] == hashlib.sha256(args[2].read_bytes()).hexdigest()
    assert len(marker["files"]) == 5
    for entry in marker["files"]:
        payload = (args[3] / entry["path"]).read_bytes()
        assert entry["bytes"] == len(payload)
        assert entry["sha256"] == hashlib.sha256(payload).hexdigest()
    for name in ("appropriation_fact", "classification_dimension", "field_lineage"):
        table = pq.read_table(args[3] / f"{name}.parquet")
        assert table.schema.equals(recordset_schema(name), check_metadata=True)
    receipt = json.loads((args[3] / "projection_receipt.json").read_bytes())
    accounting = [
        json.loads(line)
        for line in (args[3] / "lineage_accounting.jsonl").read_text().splitlines()
    ]
    assert accounting == receipt["lineage_accounting"]
    assert receipt["input_fixity"] == "not_performed"


@pytest.mark.parametrize("change", ["missing", "pin", "payload", "original"])
def test_input_failure_creates_nothing(tmp_path: Path, change: str) -> None:
    package, pin, original, output = _args(tmp_path)
    if change == "missing":
        package = tmp_path / "missing"
    elif change == "pin":
        pin = "a" * 64
    elif change == "payload":
        (package / "budget_facts.parquet").write_bytes(b"broken")
    else:
        original.write_bytes(b"broken")
    with pytest.raises(ValueError, match=r"^budget_export_input$"):
        export_budget_appropriations(package, pin, original, output, dry_run=False)
    assert not output.exists()


@pytest.mark.parametrize("value", [None, 0, 1, "false", "true"])
def test_dry_run_is_literal_boolean(tmp_path: Path, value: object) -> None:
    args = _args(tmp_path)
    with pytest.raises(ValueError, match=r"^budget_export_input$"):
        export_budget_appropriations(*args, dry_run=value)  # type: ignore[arg-type]
    assert not args[3].exists()


@pytest.mark.parametrize(
    "target", ["package", "child", "ancestor", "original", "existing"]
)
def test_overlap_and_existing_output_are_rejected(tmp_path: Path, target: str) -> None:
    package, pin, original, output = _args(tmp_path)
    existing = tmp_path / "existing"
    existing.mkdir()
    output = {
        "package": package,
        "child": package / "child",
        "ancestor": tmp_path,
        "original": original,
        "existing": existing,
    }[target]
    with pytest.raises(ValueError, match=r"^budget_export_input$"):
        export_budget_appropriations(package, pin, original, output, dry_run=False)
    assert not (existing / "FAILURE.json").exists()


@pytest.mark.parametrize(
    "limit", ["MAX_FILE_BYTES", "MAX_TOTAL_BYTES", "MAX_ORIGINAL_BYTES"]
)
def test_byte_caps_fail_before_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    args = _args(tmp_path)
    monkeypatch.setattr(budget_export, limit, 1)
    with pytest.raises(ValueError, match=r"^budget_export_input$"):
        export_budget_appropriations(*args)
    assert not args[3].exists()


def test_partial_failure_is_retained_and_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)
    real_write = budget_export._write  # noqa: SLF001 - synthetic fault boundary

    def fail(directory: budget_export._Directory, name: str, payload: bytes) -> None:
        if name == "field_lineage.parquet":
            real_write(directory, name, payload[:7])
            message = "private locator"
            raise OSError(message)
        real_write(directory, name, payload)

    monkeypatch.setattr(budget_export, "_write", fail)
    with pytest.raises(ValueError, match=r"^budget_export_write$"):
        export_budget_appropriations(*args, dry_run=False)
    assert (args[3] / "field_lineage.parquet").read_bytes()
    assert json.loads((args[3] / "FAILURE.json").read_bytes()) == {
        "schema_version": budget_export.SCHEMA,
        "status": "failed",
    }


def test_short_os_writes_are_completed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)
    real_write = os.write

    def short_write(descriptor: int, payload: bytes | memoryview) -> int:
        return real_write(descriptor, payload[:1024])

    monkeypatch.setattr(os, "write", short_write)
    export_budget_appropriations(*args, dry_run=False)
    assert (args[3] / "LOCAL_BUDGET.json").is_file()


def test_interrupt_propagates_and_retains_failure_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)
    real_write = budget_export._write  # noqa: SLF001 - synthetic fault boundary
    calls = 0

    def interrupt(
        directory: budget_export._Directory, name: str, payload: bytes
    ) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise KeyboardInterrupt
        real_write(directory, name, payload)

    monkeypatch.setattr(budget_export, "_write", interrupt)
    with pytest.raises(KeyboardInterrupt):
        export_budget_appropriations(*args, dry_run=False)
    assert args[3].is_dir()
    assert json.loads((args[3] / "FAILURE.json").read_bytes())["status"] == "failed"


def test_reservation_race_does_not_write_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)

    def raced_mkdir(_self: Path) -> None:
        message = "synthetic race"
        raise FileExistsError(message)

    monkeypatch.setattr(Path, "mkdir", raced_mkdir)
    with pytest.raises(ValueError, match=r"^budget_export_reserve$"):
        export_budget_appropriations(*args, dry_run=False)
    assert not args[3].exists()


def test_reserved_root_replacement_before_open_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not budget_export._DIR_FD_SUPPORTED:  # noqa: SLF001 - platform contract
        pytest.skip("descriptor reservation is POSIX-only")
    args = _args(tmp_path)
    real_open = os.open

    def fail_root(
        path: os.PathLike[str] | str, flags: int, *rest: object, **kwargs: object
    ) -> int:
        if path == args[3]:
            message = "synthetic root replacement"
            raise OSError(message)
        return real_open(path, flags, *rest, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "open", fail_root)
    with pytest.raises(ValueError, match=r"^budget_export_reserve$"):
        export_budget_appropriations(*args, dry_run=False)
    assert args[3].is_dir()
    assert not list(args[3].iterdir())


def test_output_root_replacement_cannot_redirect_writes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)
    owned = tmp_path / "owned-renamed"
    outside = tmp_path / "outside"
    outside.mkdir()
    real_write = budget_export._write  # noqa: SLF001 - synthetic race boundary
    replaced = False

    def replace(directory: budget_export._Directory, name: str, payload: bytes) -> None:
        nonlocal replaced
        if not replaced:
            args[3].rename(owned)
            args[3].symlink_to(outside, target_is_directory=True)
            replaced = True
        real_write(directory, name, payload)

    monkeypatch.setattr(budget_export, "_write", replace)
    with pytest.raises(ValueError, match=r"^budget_export_write$"):
        export_budget_appropriations(*args, dry_run=False)
    assert not list(outside.iterdir())
    assert not list(owned.iterdir())


def test_path_identity_fallback_persists_and_rejects_root_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_root = tmp_path / "first"
    first_root.mkdir()
    first = _args(first_root)
    monkeypatch.setattr(budget_export, "_DIR_FD_SUPPORTED", False)
    export_budget_appropriations(*first, dry_run=False)
    assert {path.name for path in first[3].iterdir()} == {
        "appropriation_fact.parquet",
        "classification_dimension.parquet",
        "field_lineage.parquet",
        "projection_receipt.json",
        "lineage_accounting.jsonl",
        "LOCAL_BUDGET.json",
    }

    second_root = tmp_path / "second"
    second_root.mkdir()
    second = _args(second_root)
    owned = tmp_path / "owned-fallback"
    outside = tmp_path / "outside-fallback"
    outside.mkdir()
    real_write = budget_export._write  # noqa: SLF001 - synthetic race boundary
    replaced = False

    def replace(directory: budget_export._Directory, name: str, payload: bytes) -> None:
        nonlocal replaced
        if not replaced:
            second[3].rename(owned)
            second[3].symlink_to(outside, target_is_directory=True)
            replaced = True
        real_write(directory, name, payload)

    monkeypatch.setattr(budget_export, "_write", replace)
    with pytest.raises(ValueError, match=r"^budget_export_write$"):
        export_budget_appropriations(*second, dry_run=False)
    assert not list(outside.iterdir())
    assert not list(owned.iterdir())


def test_path_identity_fallback_rejects_replacement_before_reserve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)
    outside = tmp_path / "outside-before-reserve"
    outside.mkdir()
    real_reserve = budget_export._reserve  # noqa: SLF001 - synthetic race boundary

    def replace(output: Path, expected: tuple[int, int]) -> object:
        output.rmdir()
        output.symlink_to(outside, target_is_directory=True)
        return real_reserve(output, expected)

    monkeypatch.setattr(budget_export, "_DIR_FD_SUPPORTED", False)
    monkeypatch.setattr(budget_export, "_reserve", replace)
    with pytest.raises(ValueError, match=r"^budget_export_reserve$"):
        export_budget_appropriations(*args, dry_run=False)
    assert not list(outside.iterdir())


def test_path_identity_fallback_rejects_ordinary_directory_before_reserve(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)
    replaced = tmp_path / "replaced-before-reserve"
    real_reserve = budget_export._reserve  # noqa: SLF001 - synthetic race boundary

    def replace(output: Path, expected: tuple[int, int]) -> object:
        output.rename(replaced)
        output.mkdir()
        return real_reserve(output, expected)

    monkeypatch.setattr(budget_export, "_DIR_FD_SUPPORTED", False)
    monkeypatch.setattr(budget_export, "_reserve", replace)
    with pytest.raises(ValueError, match=r"^budget_export_reserve$"):
        export_budget_appropriations(*args, dry_run=False)
    assert not list(args[3].iterdir())
    assert not list(replaced.iterdir())


def test_descriptor_reserve_closes_handle_on_identity_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    if not budget_export._DIR_FD_SUPPORTED:  # noqa: SLF001 - platform contract
        pytest.skip("descriptor reservation is POSIX-only")
    output = tmp_path / "reserve-close"
    output.mkdir()
    state = output.lstat()

    def reject(_output: Path, _directory: budget_export._Directory) -> None:
        message = "synthetic identity failure"
        raise ValueError(message)

    monkeypatch.setattr(budget_export, "_owned", reject)
    with pytest.raises(ValueError, match="synthetic identity failure"):
        budget_export._reserve(  # noqa: SLF001 - direct cleanup boundary
            output, (state.st_dev, state.st_ino)
        )


def test_path_identity_fallback_rejects_replacement_during_listing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)
    owned = tmp_path / "owned-during-listing"
    outside = tmp_path / "outside-during-listing"
    outside.mkdir()
    real_listdir = os.listdir
    replaced = False

    def replace(path: object) -> list[str]:
        nonlocal replaced
        listing = real_listdir(path)  # type: ignore[arg-type]
        if path == args[3] and not replaced:
            args[3].rename(owned)
            args[3].symlink_to(outside, target_is_directory=True)
            replaced = True
        return listing

    monkeypatch.setattr(budget_export, "_DIR_FD_SUPPORTED", False)
    monkeypatch.setattr(os, "listdir", replace)
    with pytest.raises(ValueError, match=r"^budget_export_write$"):
        export_budget_appropriations(*args, dry_run=False)
    assert not list(outside.iterdir())


def test_failure_marker_base_exception_does_not_replace_original(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)
    calls = 0

    def doubly_interrupted(
        _directory: budget_export._Directory, _name: str, _payload: bytes
    ) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise SystemExit(17)
        raise KeyboardInterrupt

    monkeypatch.setattr(budget_export, "_write", doubly_interrupted)
    with pytest.raises(SystemExit) as raised:
        export_budget_appropriations(*args, dry_run=False)
    assert raised.value.code == 17


def test_source_table_order_does_not_change_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)
    original_reader = budget_export.read_verified_budget
    baseline = export_budget_appropriations(*args)

    def reversed_reader(
        package: Path, pin: str
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        dict[str, Any],
    ]:
        facts, lineage, dispositions, manifest = original_reader(package, pin)
        return list(reversed(facts)), list(reversed(lineage)), dispositions, manifest

    monkeypatch.setattr(budget_export, "read_verified_budget", reversed_reader)
    assert export_budget_appropriations(*args) == baseline


def test_decimal_context_is_isolated_and_exact(tmp_path: Path) -> None:
    args = _args(tmp_path)
    with localcontext(Context(prec=2)) as caller:
        caller.traps[Inexact] = True
        caller.traps[Rounded] = True
        before = (
            caller.prec,
            caller.rounding,
            caller.flags.copy(),
            caller.traps.copy(),
        )
        export_budget_appropriations(*args, dry_run=False)
        assert (
            caller.prec,
            caller.rounding,
            caller.flags.copy(),
            caller.traps.copy(),
        ) == before
    facts = pq.read_table(args[3] / "appropriation_fact.parquet")
    assert facts.schema.field("amount").type == pa.decimal128(38, 18)
    assert all(value == Decimal("123.000") for value in facts["amount"].to_pylist())


@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_exact_file_and_aggregate_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, delta: int
) -> None:
    args = _args(tmp_path)
    plan = export_budget_appropriations(*args)
    largest = max(entry["bytes"] for entry in plan["files"])
    total = sum(entry["bytes"] for entry in plan["files"])
    monkeypatch.setattr(budget_export, "MAX_FILE_BYTES", largest + delta)
    monkeypatch.setattr(budget_export, "MAX_TOTAL_BYTES", total + delta)
    if delta < 0:
        with pytest.raises(ValueError, match=r"^budget_export_input$"):
            export_budget_appropriations(*args)
    else:
        export_budget_appropriations(*args)


def test_extra_entry_and_final_readback_failure_retain_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    args = _args(tmp_path)
    real_readback = budget_export._readback  # noqa: SLF001 - fault boundary
    calls = 0

    def extra(
        output: Path,
        directory: budget_export._Directory,
        files: dict[str, bytes],
    ) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            target: str | Path = "unexpected"
            if directory.descriptor is None:
                target = directory.path / "unexpected"
            descriptor = os.open(
                target,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
                dir_fd=directory.descriptor,
            )
            os.close(descriptor)
        real_readback(output, directory, files)

    monkeypatch.setattr(budget_export, "_readback", extra)
    with pytest.raises(ValueError, match=r"^budget_export_write$"):
        export_budget_appropriations(*args, dry_run=False)
    assert (args[3] / "LOCAL_BUDGET.json").is_file()
    assert (args[3] / "FAILURE.json").is_file()
