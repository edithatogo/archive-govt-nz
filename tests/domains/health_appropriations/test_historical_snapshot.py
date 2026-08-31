"""Historical transport verification is bounded and never a semantic grant."""

import hashlib
import json
import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_historical import _run, _source

from archive_govt_nz.domains.health_appropriations import historical_snapshot
from archive_govt_nz.domains.health_appropriations.historical_snapshot import (
    read_historical_snapshot,
)


def _package(tmp_path: Path) -> tuple[Path, Path, str]:
    source = _source(tmp_path)
    root = tmp_path / "historical"
    _run(source, root)
    return (
        root,
        source,
        hashlib.sha256((root / "MANIFEST.json").read_bytes()).hexdigest(),
    )


def test_exact_snapshot_is_read_only(tmp_path: Path) -> None:
    """All snapshots retain source types; receipt does not assert semantics."""
    root, source, pin = _package(tmp_path)
    before = {p: p.read_bytes() for p in [source, *root.iterdir()]}
    tables, manifest, receipt = read_historical_snapshot(root, source, pin)
    assert tables["historical_facts.parquet"].num_rows == manifest["counts"]["facts"]
    assert receipt["status"] == "snapshot_verified"
    assert receipt["semantic_validation"] == "not_performed"
    assert receipt["rights_state"] == "not_evaluated"
    assert receipt["manifest_sha256"] == pin
    assert receipt["original_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert before == {p: p.read_bytes() for p in before}
    assert set(tmp_path.iterdir()) == {root, source}


@pytest.mark.parametrize("target", ["source", "manifest", "facts", "extra", "missing"])
def test_broken_snapshot_fails(tmp_path: Path, target: str) -> None:
    """Missing, extra, mismatched original and corrupt files fail closed."""
    root, source, pin = _package(tmp_path)
    paths = {
        "source": source,
        "manifest": root / "MANIFEST.json",
        "facts": root / "historical_facts.parquet",
    }
    if target in paths:
        paths[target].write_bytes(b"changed")
    elif target == "extra":
        (root / "unexpected").write_bytes(b"extra")
    else:
        (root / "field_lineage.parquet").unlink()
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, pin)


@pytest.mark.parametrize(
    "text", ['{"a":1,"a":2}', '{"x":NaN}', '{"x":Infinity}', '{"x":1e999}', "[]"]
)
def test_repinned_invalid_json_fails(tmp_path: Path, text: str) -> None:
    """An explicit digest does not make non-standard JSON a valid manifest."""
    root, source, _ = _package(tmp_path)
    payload = text.encode()
    (root / "MANIFEST.json").write_bytes(payload)
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, hashlib.sha256(payload).hexdigest())


def test_count_drift_is_rejected(tmp_path: Path) -> None:
    """Repinned manifest counts must match the decoded physical tables."""
    root, source, _ = _package(tmp_path)
    manifest = json.loads((root / "MANIFEST.json").read_bytes())
    manifest["counts"]["facts"] += 1
    payload = json.dumps(manifest).encode()
    (root / "MANIFEST.json").write_bytes(payload)
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, hashlib.sha256(payload).hexdigest())


def _repin(root: Path, manifest: dict) -> str:
    payload = json.dumps(manifest).encode()
    (root / "MANIFEST.json").write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("schema_version", "wrong"),
        ("transformation_id", "wrong"),
        ("status", "partial"),
        ("rights_state", "eligible"),
        ("source_object_sha256", "bad"),
        ("source_locator", ""),
        ("source_vintage", ""),
        ("observed_at", "2026-01-01"),
        ("counts", {"facts": 0, "lineage": 0, "dispositions": 0, "rejected": 0}),
        ("counts", {"facts": True, "lineage": 0, "dispositions": 0, "rejected": 0}),
        ("counts", {"facts": 1, "lineage": 0, "dispositions": 0, "rejected": 1}),
        ("counts", {}),
        ("output_sha256", {}),
        ("counts", None),
    ],
)
def test_manifest_contract(tmp_path: Path, key: str, value: object) -> None:
    """Repinning cannot promote rights or admit unsupported input contracts."""
    root, source, _ = _package(tmp_path)
    manifest = json.loads((root / "MANIFEST.json").read_bytes())
    manifest[key] = value
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, _repin(root, manifest))


@pytest.mark.parametrize(
    "limit",
    [
        "MAX_BYTES",
        "MAX_MANIFEST_BYTES",
        "MAX_TOTAL_BYTES",
        "MAX_ROWS",
        "MAX_EXPANDED_BYTES",
    ],
)
def test_resource_caps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    """Manifest, original, payload, row and aggregate expansion caps are active."""
    root, source, pin = _package(tmp_path)
    monkeypatch.setattr(historical_snapshot, limit, 1)
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, pin)


@pytest.mark.parametrize(
    "target", ["source", "root", "MANIFEST.json", "historical_facts.parquet"]
)
def test_direct_symlinks(tmp_path: Path, target: str) -> None:
    """Reviewed parent roots do not authorize direct source or package symlinks."""
    root, source, pin = _package(tmp_path)
    path = source if target == "source" else root if target == "root" else root / target
    retained = tmp_path / "retained"
    path.rename(retained)
    try:
        path.symlink_to(retained, target_is_directory=target == "root")
    except OSError as error:
        pytest.skip(f"symlink capability unavailable: {type(error).__name__}")
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, pin)


@pytest.mark.parametrize("mode", ["corrupt", "metadata", "type"])
def test_repinned_parquet_drift(tmp_path: Path, mode: str) -> None:
    """A matching digest is insufficient when physical Arrow contracts drift."""
    root, source, _ = _package(tmp_path)
    path = root / "historical_facts.parquet"
    if mode == "corrupt":
        path.write_bytes(b"not parquet")
    else:
        table = pq.read_table(path)
        if mode == "metadata":
            table = table.replace_schema_metadata({"unexpected": "value"})
        else:
            table = table.set_column(0, "record_id", pa.array([1] * table.num_rows))
        pq.write_table(table, path)
    manifest = json.loads((root / "MANIFEST.json").read_bytes())
    manifest["output_sha256"][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, _repin(root, manifest))


def test_finite_extra_metadata_and_snapshot_semantics(tmp_path: Path) -> None:
    """Finite metadata is retained; later file changes cannot mutate returned tables."""
    root, source, _ = _package(tmp_path)
    manifest = json.loads((root / "MANIFEST.json").read_bytes())
    manifest["extra"] = {"value": 1.25}
    tables, returned, receipt = read_historical_snapshot(
        root, source, _repin(root, manifest)
    )
    expected = tables["historical_facts.parquet"].to_pylist()
    (root / "historical_facts.parquet").write_bytes(b"later change")
    assert tables["historical_facts.parquet"].to_pylist() == expected
    assert returned["extra"] == {"value": 1.25}
    assert receipt["workbook_execution"] == receipt["publication"] == "not_performed"
    assert receipt["counts"] is not returned["counts"]
    assert receipt["output_sha256"] is not returned["output_sha256"]


def test_interrupt_propagates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A cancelled read is not converted into successful or resumable state."""
    root, source, pin = _package(tmp_path)

    def interrupt(*_args: object, **_kwargs: object) -> bytes:
        raise KeyboardInterrupt

    monkeypatch.setattr(historical_snapshot, "verified_snapshot", interrupt)
    with pytest.raises(KeyboardInterrupt):
        read_historical_snapshot(root, source, pin)


def test_deep_json_is_redacted(tmp_path: Path) -> None:
    """Resource-hostile nesting receives the same bounded contract error."""
    root, source, _ = _package(tmp_path)
    depth = sys.getrecursionlimit() + 100
    payload = b'{"nested":' + b"[" * depth + b"0" + b"]" * depth + b"}"
    (root / "MANIFEST.json").write_bytes(payload)
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, hashlib.sha256(payload).hexdigest())


@pytest.mark.parametrize("pin", ["", "x" * 64, "A" * 64, None])
def test_invalid_pin(tmp_path: Path, pin: str) -> None:
    """The explicit lowercase digest is mandatory, never inferred from disk."""
    root, source, _ = _package(tmp_path)
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, pin)


@pytest.mark.parametrize(
    "limit", ["MAX_TOTAL_BYTES", "MAX_EXPANDED_BYTES", "MAX_BYTES"]
)
def test_exact_cap_and_one_over(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    """Measured exact resource caps pass; one byte below required capacity fails."""
    root, source, pin = _package(tmp_path)
    if limit == "MAX_TOTAL_BYTES":
        required = sum(path.stat().st_size for path in [source, *root.iterdir()])
    elif limit == "MAX_BYTES":
        required = max(
            path.stat().st_size for path in [source, *root.glob("*.parquet")]
        )
    else:
        required = 0
        for path in root.glob("*.parquet"):
            with pq.ParquetFile(path) as file:
                required += sum(
                    file.metadata.row_group(i).total_byte_size
                    for i in range(file.metadata.num_row_groups)
                )
    monkeypatch.setattr(historical_snapshot, limit, required)
    assert (
        read_historical_snapshot(root, source, pin)[2]["status"] == "snapshot_verified"
    )
    monkeypatch.setattr(historical_snapshot, limit, required - 1)
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, pin)


def test_all_hashes_checked_before_decode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A bad final payload prevents decoding even the first good Parquet file."""
    root, source, pin = _package(tmp_path)
    (root / "cell_dispositions.parquet").write_bytes(b"changed")

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("Parquet decoding preceded complete fixity")

    monkeypatch.setattr(historical_snapshot.pq, "ParquetFile", forbidden)
    with pytest.raises(ValueError, match=r"^historical_snapshot_contract$"):
        read_historical_snapshot(root, source, pin)
