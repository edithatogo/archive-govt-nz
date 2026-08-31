"""Plot input packages must have pinned bytes, typed tables and intact sidecars."""

import hashlib
import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz.domains.health_appropriations import gold_reader as reader
from archive_govt_nz.domains.health_appropriations.gold_export import export_gold


@pytest.fixture
def gold(raw_run: tuple[Path, Path, str], tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "gold"
    export_gold(*raw_run, root, dry_run=False)
    return root, hashlib.sha256((root / "MANIFEST.json").read_bytes()).hexdigest()


def repin(root: Path, **changes: object) -> str:
    path = root / "MANIFEST.json"
    manifest = json.loads(path.read_bytes())
    manifest.update(changes)
    for name in manifest["output_sha256"]:
        manifest["output_sha256"][name] = hashlib.sha256(
            (root / name).read_bytes()
        ).hexdigest()
    path.write_text(json.dumps(manifest))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_read_complete_package(gold: tuple[Path, str]) -> None:
    tables, manifest = reader.read_verified_gold(*gold)
    assert len(tables) == 5
    assert manifest["selected_facts"] == 3
    assert tables["historical_yoy.parquet"][0]["yoy_percent"] is None


def test_wrong_pin(gold: tuple[Path, str]) -> None:
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        reader.read_verified_gold(gold[0], "f" * 64)


@pytest.mark.parametrize("kind", ["schema_version", "status", "policy"])
def test_invalid_manifest_identity(gold: tuple[Path, str], kind: str) -> None:
    pin = repin(gold[0], **{kind: "wrong"})
    with pytest.raises(ValueError, match="invalid_gold_manifest"):
        reader.read_verified_gold(gold[0], pin)


@pytest.mark.parametrize(
    "filename", ["field_lineage.jsonl", "historical_nominal.parquet"]
)
def test_tampered_payload(gold: tuple[Path, str], filename: str) -> None:
    (gold[0] / filename).write_bytes(b"tampered")
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        reader.read_verified_gold(*gold)


def test_extra_file_rejected(gold: tuple[Path, str]) -> None:
    (gold[0] / "FAILURE.json").write_text("{}")
    with pytest.raises(ValueError, match="gold_file_set"):
        reader.read_verified_gold(*gold)


@pytest.mark.parametrize("field", ["row_counts", "output_sha256"])
def test_manifest_file_set_rejected(gold: tuple[Path, str], field: str) -> None:
    pin = repin(gold[0], **{field: {}})
    with pytest.raises(ValueError, match="invalid_gold_manifest"):
        reader.read_verified_gold(gold[0], pin)


def test_symlink_rejected(gold: tuple[Path, str], tmp_path: Path) -> None:
    original = gold[0] / "input_records.jsonl"
    target = tmp_path / "original.jsonl"
    original.rename(target)
    original.symlink_to(target)
    with pytest.raises(ValueError, match="gold_file_type"):
        reader.read_verified_gold(*gold)


@pytest.mark.parametrize(
    "limit", ["MAX_BYTES", "MAX_TOTAL_BYTES", "MAX_ROWS", "MAX_EXPANDED_BYTES"]
)
def test_bounded_materialization(
    gold: tuple[Path, str], monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    monkeypatch.setattr(reader, limit, 1)
    with pytest.raises(ValueError, match=r"source_byte_limit|gold_resource_limit"):
        reader.read_verified_gold(*gold)


def test_wrong_arrow_schema(gold: tuple[Path, str]) -> None:
    pq.write_table(pa.table({"wrong": [1]}), gold[0] / "historical_nominal.parquet")
    pin = repin(gold[0])
    with pytest.raises(ValueError, match="gold_table_contract"):
        reader.read_verified_gold(gold[0], pin)


def test_wrong_table_row_count(gold: tuple[Path, str]) -> None:
    manifest = json.loads((gold[0] / "MANIFEST.json").read_bytes())
    manifest["row_counts"]["historical_nominal.parquet"] = 99
    pin = repin(gold[0], row_counts=manifest["row_counts"])
    with pytest.raises(ValueError, match="gold_table_contract"):
        reader.read_verified_gold(gold[0], pin)


@pytest.mark.parametrize("field", ["selected_facts", "field_lineage"])
def test_sidecar_count_mismatch(gold: tuple[Path, str], field: str) -> None:
    pin = repin(gold[0], **{field: 99})
    with pytest.raises(ValueError, match="gold_sidecar_contract"):
        reader.read_verified_gold(gold[0], pin)


@pytest.mark.parametrize("change", ["duplicate", "foreign_lineage", "foreign_table"])
def test_input_identity_integrity(gold: tuple[Path, str], change: str) -> None:
    root = gold[0]
    if change == "duplicate":
        path = root / "input_records.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[1]["record_id"] = rows[0]["record_id"]
        path.write_text("\n".join(json.dumps(row) for row in rows))
    elif change == "foreign_lineage":
        path = root / "field_lineage.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        rows[0]["record_id"] = "foreign"
        path.write_text("\n".join(json.dumps(row) for row in rows))
    else:
        path = root / "historical_yoy.parquet"
        table = pq.read_table(path)
        rows = table.to_pylist()
        rows[0]["yoy_input_ids"] = ["foreign"]
        pq.write_table(pa.Table.from_pylist(rows, schema=table.schema), path)
    pin = repin(root)
    with pytest.raises(ValueError, match="gold_input_identity"):
        reader.read_verified_gold(root, pin)
