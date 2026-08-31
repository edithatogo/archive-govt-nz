"""Verified synthetic raw runs export without modifying source or prior outputs."""

import hashlib
import json
import sqlite3
from contextlib import closing
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from jsonschema import Draft202012Validator

from archive_govt_nz.cli import health_appropriations_export_sqlite
from archive_govt_nz.domains.health_appropriations import compatibility_export as export
from archive_govt_nz.domains.health_appropriations import raw_reader as reader
from archive_govt_nz.domains.health_appropriations import rebuild
from archive_govt_nz.domains.health_appropriations.compatibility_export import (
    _write_database,
)
from archive_govt_nz.domains.health_appropriations.raw_reader import (
    _read_rows,
    _validate_stage,
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_export_is_deterministic_and_loss_aware(
    raw_run: tuple[Path, Path, str], tmp_path: Path
) -> None:
    one, two = tmp_path / "one", tmp_path / "two"
    before = {str(p): _hash(p) for p in raw_run[0].rglob("*") if p.is_file()}
    planned = export.export_compatibility(*raw_run, one)
    assert planned["status"] == "planned"
    assert not one.exists()
    result = export.export_compatibility(*raw_run, one, dry_run=False)
    assert result["status"] == "passed"
    assert result["facts"] == 5
    assert result["representation_changes"] == 1
    assert set(result["table_counts"].values()) == {1}
    assert export.export_compatibility(*raw_run, two, dry_run=False) == result
    assert {p.name: p.read_bytes() for p in one.iterdir()} == {
        p.name: p.read_bytes() for p in two.iterdir()
    }
    rows = [
        json.loads(line) for line in (one / "records.jsonl").read_text().splitlines()
    ]
    health = next(r for r in rows if r["table"] == "historical_health_spending")
    assert Decimal(health["exact_amount"]) == Decimal("605.70000000000005")
    assert health["sqlite_row_number"] == 1
    with closing(sqlite3.connect(one / "compatibility.sqlite")) as db:
        assert db.execute("SELECT * FROM historical_health_spending").fetchall() == [
            (1976, float(Decimal("605.70000000000005")))
        ]
        assert db.execute("PRAGMA integrity_check").fetchall() == [("ok",)]
    assert len((one / "field_lineage.jsonl").read_text().splitlines()) == 5
    assert before == {str(p): _hash(p) for p in raw_run[0].rglob("*") if p.is_file()}


def test_existing_output_never_overwritten(
    raw_run: tuple[Path, Path, str], tmp_path: Path
) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    (output / "kept").write_bytes(b"original")
    with pytest.raises(ValueError, match="compatibility_export_failed"):
        export.export_compatibility(*raw_run, output, dry_run=False)
    assert list(output.iterdir()) == [output / "kept"]
    assert (output / "kept").read_bytes() == b"original"


@pytest.mark.parametrize("target", [0, 1])
def test_output_cannot_enter_input_roots(
    raw_run: tuple[Path, Path, str], target: int
) -> None:
    output = (raw_run[0] if target == 0 else raw_run[1]) / "bad"
    with pytest.raises(ValueError, match="compatibility_export_failed"):
        export.export_compatibility(*raw_run, output, dry_run=False)
    assert not output.exists()


def test_tampered_run_fails_before_output(
    raw_run: tuple[Path, Path, str], tmp_path: Path
) -> None:
    (raw_run[0] / "budget" / "budget_facts.parquet").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="compatibility_export_failed"):
        export.export_compatibility(*raw_run, tmp_path / "bad", dry_run=False)
    assert not (tmp_path / "bad").exists()


def test_failure_retains_partial_and_redacts(
    raw_run: tuple[Path, Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(path: Path, _rows: list[dict[str, Any]]) -> None:
        path.write_bytes(b"partial")
        message = "private source diagnostic"
        raise RuntimeError(message)

    monkeypatch.setattr(export, "_write_database", fail)
    output = tmp_path / "failed"
    with pytest.raises(ValueError, match="compatibility_export_failed:RuntimeError"):
        export.export_compatibility(*raw_run, output, dry_run=False)
    assert (output / "compatibility.sqlite").read_bytes() == b"partial"
    assert not (output / "MANIFEST.json").exists()
    assert "private" not in (output / "FAILURE.json").read_text()


def _reseal(root: Path) -> str:
    receipt = json.loads((root / "MANIFEST.json").read_bytes())
    for name, profile in rebuild.PROFILES.items():
        stage = root / name
        manifest = json.loads((stage / "MANIFEST.json").read_bytes())
        manifest["output_sha256"] = {
            filename: _hash(stage / filename) for filename in profile.outputs
        }
        (stage / "MANIFEST.json").write_text(json.dumps(manifest))
        receipt["stages"][name] = _hash(stage / "MANIFEST.json")
    (root / "MANIFEST.json").write_text(json.dumps(receipt))
    return _hash(root / "MANIFEST.json")


@pytest.mark.parametrize(
    "change",
    [
        "duplicate_fact",
        "empty_facts",
        "fact_context",
        "lineage_context",
        "coordinate",
        "amount",
        "missing_amount",
        "duplicate_amount",
        "orphan",
        "cross_stage_id",
    ],
)
def test_invalid_semantics_fail_before_write(
    raw_run: tuple[Path, Path, str], tmp_path: Path, change: str
) -> None:
    root, store, _ = raw_run
    facts_path = root / "befu" / "forecast_facts.parquet"
    lineage_path = root / "befu" / "field_lineage.parquet"
    facts_table, lineage_table = pq.read_table(facts_path), pq.read_table(lineage_path)
    facts, lineage = facts_table.to_pylist(), lineage_table.to_pylist()
    if change == "duplicate_fact":
        facts.append(facts[0].copy())
    elif change == "empty_facts":
        facts.clear()
    elif change == "fact_context":
        facts[0]["source_vintage"] = "wrong"
    elif change == "lineage_context":
        lineage[0]["source_object_sha256"] = "a" * 64
    elif change == "coordinate":
        lineage[0]["source_coordinate"] = ""
    elif change == "amount":
        lineage[0]["normalized_value"] = "124"
    elif change == "missing_amount":
        lineage[0]["field"] = "year"
    elif change == "duplicate_amount":
        lineage.append(lineage[0].copy())
    elif change == "orphan":
        lineage[0]["record_id"] = "absent"
    else:
        other = pq.read_table(root / "budget" / "budget_facts.parquet").to_pylist()[0][
            "record_id"
        ]
        facts[0]["record_id"] = other
        lineage[0]["record_id"] = other
    pq.write_table(pa.Table.from_pylist(facts, schema=facts_table.schema), facts_path)
    pq.write_table(
        pa.Table.from_pylist(lineage, schema=lineage_table.schema), lineage_path
    )
    pin = _reseal(root)
    output = tmp_path / "bad"
    with pytest.raises(ValueError, match="compatibility_export_failed"):
        export.export_compatibility(root, store, pin, output, dry_run=False)
    assert not output.exists()


@pytest.mark.parametrize("limit", ["_MAX_ROWS", "_MAX_EXPANDED_BYTES", "_MAX_BYTES"])
def test_resource_limits_fail_closed(
    raw_run: tuple[Path, Path, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    limit: str,
) -> None:
    monkeypatch.setattr(reader, limit, 1)
    with pytest.raises(ValueError, match="compatibility_export_failed"):
        export.export_compatibility(*raw_run, tmp_path / "bad", dry_run=False)
    assert not (tmp_path / "bad").exists()


def test_parquet_limits_accept_exact_boundary(
    raw_run: tuple[Path, Path, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    path = raw_run[0] / "historical" / "historical_facts.parquet"
    metadata = pq.read_metadata(path)
    monkeypatch.setattr(reader, "_MAX_ROWS", metadata.num_rows)
    monkeypatch.setattr(
        reader,
        "_MAX_EXPANDED_BYTES",
        sum(
            metadata.row_group(i).total_byte_size
            for i in range(metadata.num_row_groups)
        ),
    )
    monkeypatch.setattr(reader, "_MAX_BYTES", path.stat().st_size)
    assert len(_read_rows(path, _hash(path))) == 2


def test_symlink_output_rejected(
    raw_run: tuple[Path, Path, str], tmp_path: Path
) -> None:
    target = tmp_path / "missing"
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="compatibility_export_failed"):
        export.export_compatibility(*raw_run, link, dry_run=False)
    assert not target.exists()


def test_database_integrity_failure_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = sqlite3.connect

    class Broken(sqlite3.Connection):
        def execute(
            self,
            sql: str,
            parameters: object = (),
            /,
        ) -> sqlite3.Cursor:
            if sql == "PRAGMA integrity_check":
                return super().execute("SELECT 'broken'")
            return super().execute(sql, cast("Any", parameters))

    monkeypatch.setattr(
        export,
        "sqlite3",
        SimpleNamespace(connect=lambda path: original(path, factory=Broken)),
    )
    with pytest.raises(ValueError, match="sqlite_integrity_failed"):
        _write_database(tmp_path / "bad.sqlite", [])


def test_cli_preflight_write_and_redacted_error(
    raw_run: tuple[Path, Path, str], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "cli"
    args = {
        "raw_run": raw_run[0],
        "store_root": raw_run[1],
        "manifest_sha256": raw_run[2],
        "output_dir": output,
    }
    assert health_appropriations_export_sqlite(**args) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "planned"
    assert not output.exists()
    assert health_appropriations_export_sqlite(**args, dry_run=False) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "passed"
    assert health_appropriations_export_sqlite(**args, dry_run=False) == 2
    failure = json.loads(capsys.readouterr().out)
    assert failure["status"] == "failed"
    assert failure["error"] == "compatibility_export_failed:ValueError"


def test_manifest_schema(raw_run: tuple[Path, Path, str], tmp_path: Path) -> None:
    schema = json.loads(
        (
            Path(__file__).parents[3]
            / "schemas/health-raw-compatibility-v1.schema.json"
        ).read_bytes()
    )
    receipt = export.export_compatibility(*raw_run, tmp_path / "schema", dry_run=False)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(receipt)


def _semantic_rows(
    amount: Decimal,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    context = {
        "source_object_sha256": "a" * 64,
        "source_locator": "synthetic",
        "source_vintage": "v1",
    }
    fact = {**context, "record_id": "sha256:" + "b" * 64, "amount": amount}
    lineage = {
        **context,
        "record_id": "sha256:" + "b" * 64,
        "field": "amount",
        "source_coordinate": "'Sheet'!A1",
        "normalized_value": str(amount),
    }
    return [fact], [lineage], context


@given(st.integers(min_value=-1_000_000, max_value=1_000_000))
@settings(max_examples=30)
def test_exact_amount_lineage_property(value: int) -> None:
    facts, lineage, context = _semantic_rows(Decimal(value) / 1000)
    _validate_stage(facts, lineage, context)
    lineage[0]["normalized_value"] = str(Decimal(value) / 1000 + 1)
    with pytest.raises(ValueError, match="amount_lineage_mismatch"):
        _validate_stage(facts, lineage, context)


@pytest.mark.parametrize("coordinate", [None, 1, ""])
def test_coordinate_requires_nonempty_text(coordinate: object) -> None:
    facts, lineage, context = _semantic_rows(Decimal(1))
    lineage[0]["source_coordinate"] = coordinate
    with pytest.raises(ValueError, match="lineage_context_mismatch"):
        _validate_stage(facts, lineage, context)


@pytest.mark.parametrize("identity", [None, 1, "", "one", "sha256:" + "g" * 64])
def test_raw_reader_requires_canonical_identity(identity: object) -> None:
    facts, lineage, context = _semantic_rows(Decimal(1))
    facts[0]["record_id"] = identity
    lineage[0]["record_id"] = identity
    with pytest.raises(ValueError, match="invalid_canonical_record_identity"):
        _validate_stage(facts, lineage, context)
