"""Verified historical export is exclusive, deterministic and local only."""

import hashlib
import json
from collections.abc import Buffer
from decimal import Decimal
from io import BytesIO
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from hypothesis import given
from hypothesis import strategies as st
from tests.domains.health_appropriations.test_historical_snapshot import _package

from archive_govt_nz.domains.health_appropriations import (
    historical_canonical_export as export,
)
from archive_govt_nz.domains.health_appropriations.historical_canonical_export import (
    _encoded,
    _readback,
    _write,
    export_historical_canonical,
)
from archive_govt_nz.schemas.health_recordsets import recordset_schema


def test_default_dry_run_verifies_without_writing(tmp_path: Path) -> None:
    root, source, pin = _package(tmp_path)
    before = {p: p.read_bytes() for p in [source, *root.iterdir()]}
    output = tmp_path / "canonical"
    result = export_historical_canonical(root, source, pin, output)
    assert result["status"] == "dry_run"
    assert result["input_fixity"]["status"] == "snapshot_verified"
    assert result["semantic_validation"] == "historical-health-gdp-canonical/v1"
    assert result["rights_state"] == "not_evaluated"
    assert result["publication"] == "not_performed"
    assert not output.exists()
    assert before == {p: p.read_bytes() for p in before}


def test_two_local_builds_are_identical(tmp_path: Path) -> None:
    root, source, pin = _package(tmp_path)
    first, second = tmp_path / "first", tmp_path / "second"
    result = export_historical_canonical(root, source, pin, first, write=True)
    assert result == export_historical_canonical(root, source, pin, second, write=True)
    assert result["status"] == "complete"
    assert {p.name: p.read_bytes() for p in first.iterdir()} == {
        p.name: p.read_bytes() for p in second.iterdir()
    }
    assert {p.name for p in first.iterdir()} == {
        "health_spending_fact.parquet",
        "fiscal_context_fact.parquet",
        "field_lineage.parquet",
        "lineage_accounting.json",
        "LOCAL_CANONICAL.json",
    }


def test_readback_pins_schemas_and_complete_accounting(tmp_path: Path) -> None:
    root, source, pin = _package(tmp_path)
    output = tmp_path / "out"
    result = export_historical_canonical(root, source, pin, output, write=True)
    assert json.loads((output / "LOCAL_CANONICAL.json").read_bytes()) == result
    for name, entry in result["outputs"].items():
        payload = (output / name).read_bytes()
        assert entry == {
            "bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    for recordset, count in result["recordsets"].items():
        table = pq.read_table(output / (recordset + ".parquet"))
        assert table.num_rows == count
        assert table.schema.equals(recordset_schema(recordset), check_metadata=True)
    accounting = json.loads((output / "lineage_accounting.json").read_bytes())
    manifest = json.loads((root / "MANIFEST.json").read_bytes())
    assert len(accounting["lineage_accounting"]) == manifest["counts"]["lineage"]
    assert accounting["input_manifest_sha256"] == pin
    assert (
        result["source_package_retention"] == "required_for_retained_only_information"
    )
    assert result["source_precision"] == {"precision": 38, "scale": 17}
    assert result["canonical_precision"] == {"precision": 38, "scale": 18}


@pytest.mark.parametrize("write", [None, 0, 1, "true", [], {}])
def test_nonboolean_write_rejected_without_output(
    tmp_path: Path, write: object
) -> None:
    root, source, pin = _package(tmp_path)
    output = tmp_path / "out"
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output, write=write)  # type: ignore[arg-type]
    assert not output.exists()


@pytest.mark.parametrize(
    "kind",
    [
        "existing",
        "dangling",
        "symlink",
        "inside",
        "source",
        "ancestor",
        "missing_parent",
        "symlink_parent",
    ],
)
def test_output_preflight_does_not_touch_existing_paths(
    tmp_path: Path, kind: str
) -> None:
    root, source, pin = _package(tmp_path)
    output = tmp_path / "out"
    if kind == "existing":
        output.mkdir()
        (output / "keep").write_bytes(b"retained")
    elif kind == "dangling":
        output.symlink_to(tmp_path / "missing", target_is_directory=True)
    elif kind == "symlink":
        output.symlink_to(root, target_is_directory=True)
    elif kind == "inside":
        output = root / "out"
    elif kind == "source":
        output = source
    elif kind == "ancestor":
        output = tmp_path
    elif kind == "missing_parent":
        output = tmp_path / "missing" / "out"
    else:
        parent = tmp_path / "linked"
        parent.symlink_to(tmp_path, target_is_directory=True)
        output = parent / "out"
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output, write=True)
    assert not (output / "FAILURE.json").exists()
    assert source.is_file()


@pytest.mark.parametrize("target", ["source", "manifest", "table", "pin"])
def test_verification_failure_never_reserves_output(
    tmp_path: Path, target: str
) -> None:
    root, source, pin = _package(tmp_path)
    if target == "source":
        source.write_bytes(b"changed")
    elif target == "manifest":
        (root / "MANIFEST.json").write_bytes(b"changed")
    elif target == "table":
        (root / "field_lineage.parquet").write_bytes(b"changed")
    else:
        pin = "bad"
    output = tmp_path / "out"
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output, write=True)
    assert not output.exists()


def test_repinned_semantic_failure_precedes_output(tmp_path: Path) -> None:
    root, source, _ = _package(tmp_path)
    path = root / "historical_facts.parquet"
    table = pq.read_table(path)
    rows = table.to_pylist()
    rows[0]["amount"] = Decimal(999)
    pq.write_table(pa.Table.from_pylist(rows, schema=table.schema), path)
    manifest = json.loads((root / "MANIFEST.json").read_bytes())
    manifest["output_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    payload = json.dumps(manifest).encode()
    (root / "MANIFEST.json").write_bytes(payload)
    output = tmp_path / "out"
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(
            root, source, hashlib.sha256(payload).hexdigest(), output, write=True
        )
    assert not output.exists()


@pytest.mark.parametrize(
    "stage",
    [
        "lineage_accounting.json",
        "health_spending_fact.parquet",
        "fiscal_context_fact.parquet",
        "field_lineage.parquet",
        "LOCAL_CANONICAL.json",
    ],
)
def test_write_failure_retains_partial_files_and_redacts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    root, source, pin = _package(tmp_path)
    output = tmp_path / "out"
    original_write = _write

    def fail(path: Path, payload: bytes) -> None:
        if path.name == stage:
            path.write_bytes(b"partial")
            message = "sensitive source metadata"
            raise OSError(message)
        original_write(path, payload)

    monkeypatch.setattr(export, "_write", fail)
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output, write=True)
    assert (output / stage).read_bytes() == b"partial"
    failure = json.loads((output / "FAILURE.json").read_bytes())
    assert failure["status"] == "incomplete"
    assert failure["error_type"] == "OSError"
    assert b"sensitive" not in (output / "FAILURE.json").read_bytes()
    retained = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output, write=True)
    assert retained == {p.name: p.read_bytes() for p in output.iterdir()}


def test_failure_receipt_failure_preserves_primary_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, source, pin = _package(tmp_path)
    output = tmp_path / "out"

    def fail(_path: Path, _payload: bytes) -> None:
        message = "not for disclosure"
        raise OSError(message)

    monkeypatch.setattr(export, "_write", fail)
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output, write=True)
    assert output.is_dir()
    assert not list(output.iterdir())


def test_interrupt_preserves_bytes_and_propagates(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, source, pin = _package(tmp_path)
    output = tmp_path / "out"

    def interrupt(path: Path, _payload: bytes) -> None:
        path.write_bytes(b"interrupted")
        raise KeyboardInterrupt

    monkeypatch.setattr(export, "_write", interrupt)
    with pytest.raises(KeyboardInterrupt):
        export_historical_canonical(root, source, pin, output, write=True)
    assert (output / "lineage_accounting.json").read_bytes() == b"interrupted"
    assert not (output / "FAILURE.json").exists()


def test_raced_output_mkdir_never_gets_failure_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, source, pin = _package(tmp_path)
    output = tmp_path / "out"
    original = Path.mkdir

    def raced(path: Path, *args: object, **kwargs: object) -> None:
        if path == output:
            original(path)
            (path / "keep").write_bytes(b"other actor")
            message = "raced"
            raise FileExistsError(message)
        original(path, *args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(Path, "mkdir", raced)
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output, write=True)
    assert {p.name for p in output.iterdir()} == {"keep"}


@pytest.mark.parametrize(
    "stage",
    [
        "lineage_accounting.json",
        "health_spending_fact.parquet",
        "fiscal_context_fact.parquet",
        "field_lineage.parquet",
        "LOCAL_CANONICAL.json",
    ],
)
def test_readback_failure_never_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, stage: str
) -> None:
    root, source, pin = _package(tmp_path)
    output = tmp_path / "out"

    def fail(path: Path, payload: bytes, table: pa.Table | None = None) -> None:
        if path.name == stage:
            path.write_bytes(b"changed after write")
        _readback(path, payload, table)

    monkeypatch.setattr(export, "_readback", fail)
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output, write=True)
    assert (output / stage).read_bytes() == b"changed after write"
    assert json.loads((output / "FAILURE.json").read_bytes())["status"] == "incomplete"


@pytest.mark.parametrize("when", ["payload", "marker"])
def test_extra_output_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, when: str
) -> None:
    root, source, pin = _package(tmp_path)
    output = tmp_path / "out"

    def inject(path: Path, payload: bytes) -> None:
        _write(path, payload)
        if path.name == (
            "LOCAL_CANONICAL.json" if when == "marker" else "field_lineage.parquet"
        ):
            (output / "unexpected").write_bytes(b"retained")

    monkeypatch.setattr(export, "_write", inject)
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output, write=True)
    assert (output / "unexpected").read_bytes() == b"retained"
    assert (output / "FAILURE.json").is_file()


@pytest.mark.parametrize("adjustment", [-1, 0])
def test_output_budget_includes_completion_metadata(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, adjustment: int
) -> None:
    root, source, pin = _package(tmp_path)
    first = tmp_path / "first"
    export_historical_canonical(root, source, pin, first, write=True)
    total = sum(p.stat().st_size for p in first.iterdir())
    monkeypatch.setattr(export, "MAX_OUTPUT_BYTES", total + adjustment)
    second = tmp_path / "second"
    if adjustment:
        with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
            export_historical_canonical(root, source, pin, second, write=True)
        assert not second.exists()
    else:
        assert (
            export_historical_canonical(root, source, pin, second, write=True)["status"]
            == "complete"
        )


def test_payload_budget_rejected_before_reservation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, source, pin = _package(tmp_path)
    monkeypatch.setattr(export, "MAX_OUTPUT_BYTES", 1)
    output = tmp_path / "out"
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output, write=True)
    assert not output.exists()


@pytest.mark.parametrize("kind", ["missing", "symlink", "trailing", "schema"])
def test_readback_rejects_malformed_outputs(tmp_path: Path, kind: str) -> None:
    path = tmp_path / "out"
    table = pa.table({"value": [1]})
    payload = b"expected"
    if kind == "symlink":
        source = tmp_path / "source"
        source.write_bytes(payload)
        path.symlink_to(source)
    elif kind == "trailing":
        path.write_bytes(payload + b"extra")
    elif kind == "schema":
        pq.write_table(table, path)
        payload = path.read_bytes()
        table = pa.table({"other": [1]})
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        _readback(path, payload, table)


def test_exclusive_file_writer_preserves_existing_file(tmp_path: Path) -> None:
    path = tmp_path / "existing"
    path.write_bytes(b"retained")
    with pytest.raises(FileExistsError):
        _write(path, b"changed")
    assert path.read_bytes() == b"retained"


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf")])
def test_nonfinite_receipt_encoding_is_rejected(value: float) -> None:
    with pytest.raises(ValueError, match="Out of range float"):
        _encoded({"value": value})


def test_dry_run_checks_the_same_serialization_budget(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, source, pin = _package(tmp_path)
    monkeypatch.setattr(export, "MAX_OUTPUT_BYTES", 1)
    output = tmp_path / "out"
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        export_historical_canonical(root, source, pin, output)
    assert not output.exists()


def test_dry_run_and_write_have_identical_planned_payloads(tmp_path: Path) -> None:
    root, source, pin = _package(tmp_path)
    dry = export_historical_canonical(root, source, pin, tmp_path / "dry")
    written = export_historical_canonical(
        root, source, pin, tmp_path / "written", write=True
    )
    assert dry.pop("planned_outputs") == written["outputs"]
    assert "outputs" not in dry
    assert {**dry, "status": "complete", "outputs": written["outputs"]} == written


def test_short_write_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class ShortWriter(BytesIO):
        def write(self, payload: Buffer) -> int:
            return super().write(memoryview(payload)[:-1])

    def opened(_path: Path, _mode: str) -> ShortWriter:
        return ShortWriter()

    monkeypatch.setattr(Path, "open", opened)
    with pytest.raises(ValueError, match=r"^historical_canonical_export_contract$"):
        _write(tmp_path / "out", b"bytes")


@given(
    st.dictionaries(
        st.text(max_size=10), st.integers(min_value=-1000, max_value=1000), max_size=5
    )
)
def test_receipt_encoding_is_canonical_and_exact(value: dict[str, int]) -> None:
    payload = _encoded(value)
    assert payload == _encoded(dict(reversed(list(value.items()))))
    assert payload.endswith(b"\n")
    assert json.loads(payload) == value
