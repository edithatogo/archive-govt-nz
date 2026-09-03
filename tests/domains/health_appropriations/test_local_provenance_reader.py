"""Composed receipts verify snapshots without creating state or rights."""

import hashlib
import json
from collections.abc import Iterator
from dataclasses import replace
from decimal import Inexact, localcontext
from io import BytesIO
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_budget_classification import inputs
from tests.domains.health_appropriations.test_historical_snapshot import _package

from archive_govt_nz.domains.health_appropriations import (
    local_provenance_reader as reader,
)
from archive_govt_nz.domains.health_appropriations.budget_export import (
    export_budget_appropriations,
)
from archive_govt_nz.domains.health_appropriations.classification_export import (
    export_budget_classification,
)
from archive_govt_nz.domains.health_appropriations.historical_canonical_export import (
    export_historical_canonical,
)
from archive_govt_nz.domains.health_appropriations.local_provenance_reader import (
    CanonicalPackageInput,
    read_local_provenance,
)


def package(tmp_path: Path, kind: str) -> CanonicalPackageInput:
    output = tmp_path / "canonical"
    if kind == "historical":
        raw, source, pin = _package(tmp_path)
        export_historical_canonical(raw, source, pin, output, write=True)
        marker = "LOCAL_CANONICAL.json"
    else:
        data = inputs(tmp_path)
        raw, source, pin = (
            tmp_path / "package",
            tmp_path / "source.xlsx",
            data["manifest_sha256"],
        )
        if kind == "budget":
            export_budget_appropriations(raw, pin, source, output, dry_run=False)
            marker = "LOCAL_BUDGET.json"
        else:
            export_budget_classification(raw, pin, source, output, dry_run=False)
            marker = "LOCAL_CLASSIFICATION.json"
    return CanonicalPackageInput(
        kind=kind,
        root=output,
        marker_sha256=hashlib.sha256((output / marker).read_bytes()).hexdigest(),
        original=source,
        raw_root=raw,
        raw_manifest_sha256=pin,
    )


@pytest.mark.parametrize("kind", ["historical", "classification", "budget"])
def test_verified_inventory_keeps_pure_claims_separate(
    tmp_path: Path, kind: str
) -> None:
    value = package(tmp_path, kind)
    before = {
        p: p.read_bytes()
        for p in (value.original, *value.root.iterdir(), *value.raw_root.iterdir())
    }
    result = read_local_provenance((value,))
    assert result["status"] == "verified_scoped_snapshots"
    assert result["inventory"]["input_fixity"] == "not_performed"
    assert result["inventory"]["rights_state"] == "not_evaluated"
    assert (
        len(result["inventory"]["products"])
        == {
            "historical": 3,
            "classification": 2,
            "budget": 3,
        }[kind]
    )
    assert result == read_local_provenance((value,))
    assert before == {p: p.read_bytes() for p in before}


@pytest.mark.parametrize(
    "change", ["missing", "marker_pin", "raw_pin", "original", "payload"]
)
def test_fail_closed_does_not_create_state(tmp_path: Path, change: str) -> None:
    value = package(tmp_path, "classification")
    if change == "missing":
        value = replace(value, root=tmp_path / "missing")
    elif change == "marker_pin":
        value = replace(value, marker_sha256="0" * 64)
    elif change == "raw_pin":
        value = replace(value, raw_manifest_sha256="0" * 64)
    elif change == "original":
        value.original.write_bytes(b"changed")
    else:
        (value.root / "classification_dimension.parquet").write_bytes(b"changed")
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))
    assert not (tmp_path / "missing").exists()


def _marker_name(value: CanonicalPackageInput) -> str:
    return {
        "historical": "LOCAL_CANONICAL.json",
        "classification": "LOCAL_CLASSIFICATION.json",
        "budget": "LOCAL_BUDGET.json",
    }[value.kind]


def _repin(value: CanonicalPackageInput, marker: object) -> CanonicalPackageInput:
    payload = json.dumps(marker).encode()
    (value.root / _marker_name(value)).write_bytes(payload)
    return replace(value, marker_sha256=hashlib.sha256(payload).hexdigest())


def _changed_payload(
    value: CanonicalPackageInput, name: str, payload: bytes
) -> CanonicalPackageInput:
    (value.root / name).write_bytes(payload)
    marker = json.loads((value.root / _marker_name(value)).read_bytes())
    entry = (
        marker["outputs"][name]
        if value.kind == "historical"
        else next(row for row in marker["files"] if row["path"] == name)
    )
    entry.update(sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload))
    return _repin(value, marker)


@pytest.mark.parametrize("kind", ["historical", "classification", "budget"])
@pytest.mark.parametrize("change", ["value", "schema", "accounting"])
def test_repin_cannot_legitimize_wrong_projection(
    tmp_path: Path, kind: str, change: str
) -> None:
    value = package(tmp_path, kind)
    if change == "accounting":
        name = (
            "lineage_accounting.json"
            if kind == "historical"
            else "projection_receipt.json"
        )
        content = json.loads((value.root / name).read_bytes())
        content["lineage_accounting"].pop()
        value = _changed_payload(value, name, json.dumps(content).encode())
    else:
        name = (
            "health_spending_fact.parquet"
            if kind == "historical"
            else "classification_dimension.parquet"
        )
        table = pq.read_table(value.root / name)
        if change == "schema":
            table = table.replace_schema_metadata({b"wrong": b"metadata"})
        else:
            rows = table.to_pylist()
            rows[0]["source_label"] = "changed"
            table = pa.Table.from_pylist(rows, schema=table.schema)
        buffer = BytesIO()
        pq.write_table(table, buffer)
        value = _changed_payload(value, name, buffer.getvalue())
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


@pytest.mark.parametrize("kind", ["historical", "classification", "budget"])
@pytest.mark.parametrize("change", ["float", "bool", "extra", "rights"])
def test_marker_types_and_claims_are_exact(
    tmp_path: Path, kind: str, change: str
) -> None:
    value = package(tmp_path, kind)
    marker = json.loads((value.root / _marker_name(value)).read_bytes())
    if change == "extra":
        marker["unreviewed"] = True
    elif change == "rights":
        marker["rights_state"] = "eligible"
    elif kind == "historical":
        current = marker["input_fixity"]["original_bytes"]
        marker["input_fixity"]["original_bytes"] = (
            float(current) if change == "float" else True
        )
    else:
        marker["original_bytes"] = (
            float(marker["original_bytes"]) if change == "float" else True
        )
    value = _repin(value, marker)
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


@pytest.mark.parametrize(
    "payload",
    [
        b'{"a":1,"a":2}',
        b'{"a":NaN}',
        b'{"a":1e999}',
        b"[]",
        b'"text"',
        b"\xff",
        pytest.param(b"[" * 10_000 + b"0" + b"]" * 10_000, id="deep-json"),
    ],
)
def test_strict_repinned_marker_json(tmp_path: Path, payload: bytes) -> None:
    value = package(tmp_path, "classification")
    (value.root / _marker_name(value)).write_bytes(payload)
    value = replace(value, marker_sha256=hashlib.sha256(payload).hexdigest())
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


@pytest.mark.parametrize("kind", ["historical", "classification", "budget"])
def test_hostile_decimal_context_does_not_change_result(
    tmp_path: Path, kind: str
) -> None:
    value = package(tmp_path, kind)
    normal = read_local_provenance((value,))
    with localcontext() as context:
        context.prec = 2
        context.traps[Inexact] = True
        assert read_local_provenance((value,)) == normal
        assert context.prec == 2
        assert context.traps[Inexact]


@pytest.mark.parametrize(
    "name", ["MAX_MARKER", "MAX_FILE", "MAX_PACKAGE", "MAX_EXPANDED", "MAX_ROWS"]
)
def test_resource_caps_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    value = package(tmp_path, "historical")
    monkeypatch.setattr(reader, name, 1)
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


def test_repeated_root_and_vintage_rejected(tmp_path: Path) -> None:
    value = package(tmp_path, "historical")
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value, value))
    other = tmp_path / "other"
    other.mkdir()
    second = package(other, "historical")
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value, second))


def test_mixed_profiles_order_is_deterministic(tmp_path: Path) -> None:
    one, two = tmp_path / "one", tmp_path / "two"
    one.mkdir()
    two.mkdir()
    first, second = package(one, "historical"), package(two, "classification")
    assert read_local_provenance((first, second)) == read_local_provenance(
        (second, first)
    )


def test_budget_dependency_graph_is_closed_and_explicit(tmp_path: Path) -> None:
    value = package(tmp_path, "budget")
    inventory = read_local_provenance((value,))["inventory"]
    products = {row["recordset"]: row for row in inventory["products"]}
    dimension = products["classification_dimension"]["key"]
    fact = products["appropriation_fact"]["key"]
    assert products["classification_dimension"]["dependencies"] == []
    assert products["appropriation_fact"]["dependencies"] == [dimension]
    assert products["field_lineage"]["dependencies"] == [fact, dimension]
    assert sum(row["kind"] == "product" for row in inventory["edges"]) == 3


@pytest.mark.parametrize("name", ["appropriation_fact.parquet", "LOCAL_BUDGET.json"])
def test_budget_six_file_closure_rejects_change(tmp_path: Path, name: str) -> None:
    value = package(tmp_path, "budget")
    if name == "LOCAL_BUDGET.json":
        (value.root / "unexpected").write_bytes(b"retained evidence")
    else:
        (value.root / name).write_bytes(b"changed")
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


@pytest.mark.parametrize(
    "name", ["projection_receipt.json", "lineage_accounting.jsonl"]
)
def test_budget_repinned_semantic_json_byte_change_is_rejected(
    tmp_path: Path, name: str
) -> None:
    value = package(tmp_path, "budget")
    payload = (value.root / name).read_bytes()
    value = _changed_payload(value, name, b" " + payload)
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


@pytest.mark.parametrize("target", ["root", "raw_root", "original", "payload"])
def test_direct_symlinks_are_rejected(tmp_path: Path, target: str) -> None:
    value = package(tmp_path, "classification")
    if target == "payload":
        path = value.root / "classification_dimension.parquet"
        retained = tmp_path / "retained.parquet"
        path.rename(retained)
        path.symlink_to(retained)
    else:
        link = tmp_path / "link"
        link.symlink_to(
            getattr(value, target), target_is_directory=target != "original"
        )
        value = replace(value, **{target: link})
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


@pytest.mark.parametrize("change", ["extra", "missing", "directory"])
def test_exact_file_closure(tmp_path: Path, change: str) -> None:
    value = package(tmp_path, "classification")
    if change == "extra":
        (value.root / "unexpected").write_bytes(b"evidence")
    else:
        path = value.root / "classification_dimension.parquet"
        path.rename(tmp_path / "retained.parquet")
        if change == "directory":
            path.mkdir()
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


@pytest.mark.parametrize(
    "change",
    [
        "null",
        "duplicate",
        "path",
        "bytes_bool",
        "bytes_float",
        "bytes_zero",
        "bytes_wrong",
        "entry",
    ],
)
def test_malformed_payload_descriptors(tmp_path: Path, change: str) -> None:
    value = package(tmp_path, "classification")
    marker = json.loads((value.root / _marker_name(value)).read_bytes())
    rows = marker["files"]
    if change == "null":
        marker["files"] = None
    elif change == "duplicate":
        rows[1] = rows[0]
    elif change == "path":
        rows[0]["path"] = "../escape"
    elif change == "entry":
        rows[0] = None
    else:
        rows[0]["bytes"] = {
            "bytes_bool": True,
            "bytes_float": float(rows[0]["bytes"]),
            "bytes_zero": 0,
            "bytes_wrong": rows[0]["bytes"] + 1,
        }[change]
    value = _repin(value, marker)
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


def test_repinned_jsonl_divergence_rejected(tmp_path: Path) -> None:
    value = package(tmp_path, "classification")
    value = _changed_payload(value, "lineage_accounting.jsonl", b"{}\n")
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


@pytest.mark.parametrize(
    "error", [OSError, TypeError, ValueError, KeyError, AttributeError, pa.ArrowInvalid]
)
def test_expected_errors_are_redacted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: type[Exception]
) -> None:
    value = package(tmp_path, "classification")

    def broken(*_args: object, **_kwargs: object) -> None:
        message = "private caller path and source text"
        raise error(message)

    monkeypatch.setattr(reader, "verified_snapshot", broken)
    with pytest.raises(
        ValueError, match=r"^local_provenance_reader_invalid$"
    ) as caught:
        read_local_provenance((value,))
    assert caught.value.__suppress_context__


@pytest.mark.parametrize("error", [KeyboardInterrupt, SystemExit])
def test_interruptions_propagate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: type[BaseException]
) -> None:
    value = package(tmp_path, "classification")

    def broken(*_args: object, **_kwargs: object) -> None:
        raise error

    monkeypatch.setattr(reader, "verified_snapshot", broken)
    with pytest.raises(error):
        read_local_provenance((value,))


@pytest.mark.parametrize("values", [(), [], (None,), (None,) * 5])
def test_invalid_container_rejected(values: object) -> None:
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance(values)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "name", ["MAX_MARKER", "MAX_FILE", "MAX_PACKAGE", "MAX_EXPANDED"]
)
def test_exact_resource_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    value = package(tmp_path, "historical")
    if name == "MAX_MARKER":
        # Keep the independently shared Thrift cap above real schema strings.
        path = value.root / _marker_name(value)
        padded = path.read_bytes() + b" " * (1024 * 1024)
        path.write_bytes(padded)
        value = replace(value, marker_sha256=hashlib.sha256(padded).hexdigest())
    payloads = {path.name: path.read_bytes() for path in value.root.iterdir()}
    marker = payloads[_marker_name(value)]
    expanded = 0
    for filename, payload in payloads.items():
        if filename.endswith(".parquet"):
            with pq.ParquetFile(BytesIO(payload)) as file:
                expanded += sum(
                    file.metadata.row_group(i).total_byte_size
                    for i in range(file.metadata.num_row_groups)
                )
    limit = {
        "MAX_MARKER": len(marker),
        "MAX_FILE": max(
            len(payload)
            for filename, payload in payloads.items()
            if filename != _marker_name(value)
        ),
        "MAX_PACKAGE": sum(map(len, payloads.values())),
        "MAX_EXPANDED": expanded,
    }[name]
    monkeypatch.setattr(reader, name, limit)
    assert read_local_provenance((value,))["status"] == "verified_scoped_snapshots"
    monkeypatch.setattr(reader, name, limit - 1)
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))


def test_root_enumeration_is_bounded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = package(tmp_path, "classification")
    original = Path.iterdir
    count = 0

    def bounded(path: Path) -> Iterator[Path]:
        nonlocal count
        if path != value.root:
            yield from original(path)
            return
        for child in original(path):
            count += 1
            yield child
        count += 1
        yield path / "unexpected"
        pytest.fail("enumerated beyond allowlist plus one")

    monkeypatch.setattr(Path, "iterdir", bounded)
    with pytest.raises(ValueError, match=r"^local_provenance_reader_invalid$"):
        read_local_provenance((value,))
    assert count == 6
