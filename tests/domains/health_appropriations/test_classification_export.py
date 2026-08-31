"""Exclusive local classification packages retain inputs and complete accounting."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_budget_classification import inputs

from archive_govt_nz.domains.health_appropriations import classification_export
from archive_govt_nz.domains.health_appropriations.classification_export import (
    _readback,
    _write,
    export_budget_classification,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def test_dry_run_and_deterministic_packages(tmp_path: Path) -> None:
    source = inputs(tmp_path)
    package, original = tmp_path / "package", tmp_path / "source.xlsx"
    before = {path: path.read_bytes() for path in [original, *package.iterdir()]}
    output = tmp_path / "first"
    plan = export_budget_classification(
        package, source["manifest_sha256"], original, output
    )
    assert plan["status"] == "planned"
    assert plan["hash_state"] == "planned"
    assert not output.exists()
    first = export_budget_classification(
        package, source["manifest_sha256"], original, output, dry_run=False
    )
    second = tmp_path / "second"
    export_budget_classification(
        package, source["manifest_sha256"], original, second, dry_run=False
    )
    assert first["status"] == "passed"
    assert first["hash_state"] == "verified_persisted"
    assert {p.name: p.read_bytes() for p in output.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }
    assert {path: path.read_bytes() for path in before} == before
    marker = json.loads((output / "LOCAL_CLASSIFICATION.json").read_bytes())
    assert marker["publication_state"] == "local_validation_only"
    assert marker["rights_state"] == "not_evaluated"
    assert marker["self_contained_archive"] is False
    assert marker["publication_approval"] == "not_granted"
    assert marker["authoritative_mapping"] == "not_performed"
    assert marker["input_manifest_sha256"] == source["manifest_sha256"]
    assert (
        marker["original_sha256"] == hashlib.sha256(original.read_bytes()).hexdigest()
    )
    assert marker["original_bytes"] == original.stat().st_size
    assert marker["input_payload_sha256"] == source["manifest"]["output_sha256"]
    assert not (output / "MANIFEST.json").exists()
    assert len(marker["files"]) == 4
    for entry in marker["files"]:
        payload = (output / entry["path"]).read_bytes()
        assert len(payload) == entry["bytes"]
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"]
    for name in ("classification_dimension", "field_lineage"):
        table = pq.read_table(output / f"{name}.parquet")
        assert table.schema.equals(recordset_schema(name), check_metadata=True)
        assert table.num_rows == 2
    accounting = (output / "lineage_accounting.jsonl").read_text().splitlines()
    assert len(accounting) == 18
    assert sum(json.loads(row)["state"] == "mapped" for row in accounting) == 2


@pytest.mark.parametrize("change", ["missing", "pin", "payload", "original"])
def test_input_failure_creates_nothing(tmp_path: Path, change: str) -> None:
    source = inputs(tmp_path)
    package, original = tmp_path / "package", tmp_path / "source.xlsx"
    pin = source["manifest_sha256"]
    if change == "missing":
        package = tmp_path / "missing"
    elif change == "pin":
        pin = "a" * 64
    elif change == "payload":
        (package / "budget_facts.parquet").write_bytes(b"tampered")
    else:
        original.write_bytes(b"tampered")
    output = tmp_path / "output"
    with pytest.raises(ValueError, match=r"^classification_export_input$"):
        export_budget_classification(package, pin, original, output, dry_run=False)
    assert not output.exists()


@pytest.mark.parametrize("value", [None, 0, 1, "false", "true"])
def test_dry_run_requires_literal_boolean(tmp_path: Path, value: object) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"
    with pytest.raises(ValueError, match=r"^classification_export_input$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=value,  # type: ignore[arg-type]
        )
    assert not output.exists()


def test_failure_marker_cannot_mask_original_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"

    def broken_write(path: Path, _payload: bytes) -> None:
        if path.name == "FAILURE.json":
            msg = "failure marker failed"
            raise ValueError(msg)
        msg = "original write failed"
        raise OSError(msg)

    monkeypatch.setattr(classification_export, "_write", broken_write)
    with pytest.raises(ValueError, match=r"^classification_export_write$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=False,
        )
    assert output.is_dir()


@pytest.mark.parametrize(
    "limit", ["MAX_FILE_BYTES", "MAX_TOTAL_BYTES", "MAX_ORIGINAL_BYTES"]
)
@pytest.mark.parametrize("delta", [-1, 0, 1])
def test_exact_byte_boundaries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str, delta: int
) -> None:
    source = inputs(tmp_path)
    args = (
        tmp_path / "package",
        source["manifest_sha256"],
        tmp_path / "source.xlsx",
        tmp_path / "output",
    )
    plan = export_budget_classification(*args)
    sizes = [entry["bytes"] for entry in plan["files"]]
    bound = {
        "MAX_FILE_BYTES": max(sizes),
        "MAX_TOTAL_BYTES": sum(sizes),
        "MAX_ORIGINAL_BYTES": args[2].stat().st_size,
    }[limit]
    monkeypatch.setattr(classification_export, limit, bound + delta)
    if delta < 0:
        with pytest.raises(ValueError, match=r"^classification_export_input$"):
            export_budget_classification(*args)
    else:
        assert export_budget_classification(*args) == plan
    assert not args[3].exists()


@pytest.mark.parametrize(
    "target", ["package", "child", "ancestor", "original", "existing"]
)
def test_output_overlap_or_existing_rejected(tmp_path: Path, target: str) -> None:
    source = inputs(tmp_path)
    package, original = tmp_path / "package", tmp_path / "source.xlsx"
    existing = tmp_path / "existing"
    existing.mkdir()
    outputs = {
        "package": package,
        "child": package / "child",
        "ancestor": tmp_path,
        "original": original,
        "existing": existing,
    }
    before = {path: path.read_bytes() for path in [original, *package.iterdir()]}
    with pytest.raises(ValueError, match=r"^classification_export_input$"):
        export_budget_classification(
            package, source["manifest_sha256"], original, outputs[target], dry_run=False
        )
    assert {path: path.read_bytes() for path in before} == before
    assert not (existing / "FAILURE.json").exists()


@pytest.mark.parametrize("target", ["package", "original", "output"])
def test_direct_symlinks_rejected(tmp_path: Path, target: str) -> None:
    source = inputs(tmp_path)
    paths = {
        "package": tmp_path / "package",
        "original": tmp_path / "source.xlsx",
        "output": tmp_path / "output",
    }
    link = tmp_path / "link"
    try:
        link.symlink_to(paths[target], target_is_directory=target != "original")
    except OSError:
        pytest.skip("symlink creation unavailable")
    paths[target] = link
    with pytest.raises(ValueError, match=r"^classification_export_input$"):
        export_budget_classification(
            paths["package"],
            source["manifest_sha256"],
            paths["original"],
            paths["output"],
            dry_run=False,
        )
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize(
    "name",
    [
        "classification_dimension.parquet",
        "field_lineage.parquet",
        "projection_receipt.json",
        "lineage_accounting.jsonl",
        "LOCAL_CLASSIFICATION.json",
    ],
)
def test_partial_write_evidence_retained(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"
    write = _write

    def partial(path: Path, payload: bytes) -> None:
        if path.name == name:
            write(path, payload[:7])
            msg = "synthetic private locator must not enter receipt"
            raise OSError(msg)
        write(path, payload)

    monkeypatch.setattr(classification_export, "_write", partial)
    with pytest.raises(ValueError, match=r"^classification_export_write$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=False,
        )
    assert len((output / name).read_bytes()) == 7
    failure = (output / "FAILURE.json").read_bytes()
    assert b"locator" not in failure
    assert json.loads(failure) == {
        "schema_version": classification_export.SCHEMA,
        "status": "failed",
    }


def test_failed_final_readback_preserves_complete_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"
    readback = _readback

    def tampered(root: Path, files: dict[str, bytes]) -> None:
        if "LOCAL_CLASSIFICATION.json" in files:
            (root / "field_lineage.parquet").write_bytes(b"tampered")
        readback(root, files)

    monkeypatch.setattr(classification_export, "_readback", tampered)
    with pytest.raises(ValueError, match=r"^classification_export_write$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=False,
        )
    assert json.loads((output / "LOCAL_CLASSIFICATION.json").read_bytes())
    assert (output / "FAILURE.json").is_file()


def test_missing_output_parent_rejected_without_creation(tmp_path: Path) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "absent" / "output"
    with pytest.raises(ValueError, match=r"^classification_export_input$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=False,
        )
    assert not output.parent.exists()


def test_payloads_verified_before_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"
    observed = []

    def observe(root: Path, files: dict[str, bytes]) -> None:
        observed.append((set(files), (root / "LOCAL_CLASSIFICATION.json").exists()))
        _readback(root, files)

    monkeypatch.setattr(classification_export, "_readback", observe)
    export_budget_classification(
        tmp_path / "package",
        source["manifest_sha256"],
        tmp_path / "source.xlsx",
        output,
        dry_run=False,
    )
    assert len(observed) == 2
    assert "LOCAL_CLASSIFICATION.json" not in observed[0][0]
    assert observed[0][1] is False
    assert observed[1][1] is True


@pytest.mark.parametrize("change", ["name", "metadata", "nullability", "rows", "value"])
def test_serializer_schema_damage_fails_before_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"
    writer = pq.write_table

    def broken(
        table: pa.Table, where: pa.BufferOutputStream, *, compression: str, version: str
    ) -> None:
        if change == "name":
            damaged = table.rename_columns(["broken", *table.column_names[1:]])
        elif change == "metadata":
            damaged = table.replace_schema_metadata({b"tampered": b"metadata"})
        elif change == "nullability":
            field = table.schema.field(0)
            altered = pa.field(field.name, field.type, nullable=not field.nullable)
            damaged = table.cast(table.schema.set(0, altered))
        elif change == "rows":
            damaged = table.slice(0, 1)
        else:
            damaged = table.set_column(
                0, table.schema.field(0), pa.array(["wrong"] * table.num_rows)
            )
        writer(damaged, where, compression=compression, version=version)

    monkeypatch.setattr(pq, "write_table", broken)
    with pytest.raises(ValueError, match=r"^classification_export_input$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=False,
        )
    assert not output.exists()


@pytest.mark.parametrize("marker_failure", [False, True])
def test_type_errors_are_redacted_and_cannot_mask_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, marker_failure: bool
) -> None:
    source = inputs(tmp_path)

    def broken(path: Path, payload: bytes) -> None:
        message = "synthetic private error detail"
        if marker_failure and path.name != "FAILURE.json":
            raise OSError(message)
        if marker_failure or path.name != "FAILURE.json":
            raise TypeError(message)
        _write(path, payload)

    monkeypatch.setattr(classification_export, "_write", broken)
    with pytest.raises(ValueError, match=r"^classification_export_write$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            tmp_path / "output",
            dry_run=False,
        )


def test_serialized_cap_checked_before_parquet_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    monkeypatch.setattr(classification_export, "MAX_FILE_BYTES", 1)

    def forbidden_decode(*_args: object, **_kwargs: object) -> None:
        message = "oversized buffer decoded"
        raise AssertionError(message)

    monkeypatch.setattr(pq, "read_table", forbidden_decode)
    with pytest.raises(ValueError, match=r"^classification_export_input$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            tmp_path / "output",
        )


@pytest.mark.parametrize("exception", [KeyboardInterrupt, SystemExit])
def test_interruptions_preserve_partial_outputs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exception: type[BaseException]
) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"

    def interrupt(_root: Path, _files: dict[str, bytes]) -> None:
        raise exception

    monkeypatch.setattr(classification_export, "_readback", interrupt)
    with pytest.raises(exception):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=False,
        )
    assert (output / "classification_dimension.parquet").is_file()
    assert (output / "FAILURE.json").is_file()
    assert not (output / "LOCAL_CLASSIFICATION.json").exists()


def test_mkdir_race_never_marks_other_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"
    mkdir = Path.mkdir

    def race(path: Path) -> None:
        assert path == output
        mkdir(path)
        (path / "other_run").write_bytes(b"keep")
        raise FileExistsError

    monkeypatch.setattr(Path, "mkdir", race)
    with pytest.raises(ValueError, match=r"^classification_export_reserve$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=False,
        )
    assert {p.name: p.read_bytes() for p in output.iterdir()} == {"other_run": b"keep"}


def test_symlink_parent_rejected(tmp_path: Path) -> None:
    source = inputs(tmp_path)
    parent = tmp_path / "real"
    parent.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(parent, target_is_directory=True)
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ValueError, match=r"^classification_export_input$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            link / "output",
            dry_run=False,
        )
    assert list(parent.iterdir()) == []


@pytest.mark.parametrize("change", ["extra", "missing", "symlink"])
def test_readback_file_closure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"

    def damaged(root: Path, files: dict[str, bytes]) -> None:
        if change == "extra":
            (root / "unexpected").write_bytes(b"retain")
        else:
            target = root / "field_lineage.parquet"
            target.unlink()
            if change == "symlink":
                try:
                    target.symlink_to(root / "classification_dimension.parquet")
                except OSError:
                    pytest.skip("symlink creation unavailable")
        _readback(root, files)

    monkeypatch.setattr(classification_export, "_readback", damaged)
    with pytest.raises(ValueError, match=r"^classification_export_write$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=False,
        )
    assert (output / "FAILURE.json").is_file()
    assert not (output / "LOCAL_CLASSIFICATION.json").exists()


def test_short_write_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def short(payload: bytes) -> int:
        return len(payload) - 1

    @contextmanager
    def opened(_path: Path, _mode: str) -> Iterator[object]:
        yield SimpleNamespace(write=short)

    with monkeypatch.context() as local:
        local.setattr(Path, "open", opened)
        with pytest.raises(ValueError, match="classification_export_contract"):
            _write(tmp_path / "short", b"payload")


def test_marker_bytes_are_in_dry_run_cap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    args = (
        tmp_path / "package",
        source["manifest_sha256"],
        tmp_path / "source.xlsx",
        tmp_path / "output",
    )
    plan = export_budget_classification(*args)
    without_marker = sum(
        item["bytes"]
        for item in plan["files"]
        if item["path"] != "LOCAL_CLASSIFICATION.json"
    )
    monkeypatch.setattr(classification_export, "MAX_TOTAL_BYTES", without_marker)
    with pytest.raises(ValueError, match=r"^classification_export_input$"):
        export_budget_classification(*args)
    assert not args[3].exists()


def test_output_error_is_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = inputs(tmp_path)
    output = tmp_path / "output"

    def broken(path: Path, payload: bytes) -> None:
        if path.name != "FAILURE.json":
            message = "caller private output path"
            raise OSError(message)
        _write(path, payload)

    monkeypatch.setattr(classification_export, "_write", broken)
    with pytest.raises(ValueError, match=r"^classification_export_write$"):
        export_budget_classification(
            tmp_path / "package",
            source["manifest_sha256"],
            tmp_path / "source.xlsx",
            output,
            dry_run=False,
        )
