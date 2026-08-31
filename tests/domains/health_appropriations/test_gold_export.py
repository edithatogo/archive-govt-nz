"""Source-derived Gold persistence is pinned, exclusive and independently rebuildable."""

import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest
from jsonschema import Draft202012Validator

from archive_govt_nz.cli import health_appropriations_export_gold
from archive_govt_nz.domains.health_appropriations import gold_export as export


def test_dry_run_and_independent_gold_builds(
    raw_run: tuple[Path, Path, str], tmp_path: Path
) -> None:
    one, two = tmp_path / "gold-one", tmp_path / "gold-two"
    assert export.export_gold(*raw_run, one)["status"] == "planned"
    assert not one.exists()
    receipt = export.export_gold(*raw_run, one, dry_run=False)
    assert receipt["status"] == "passed"
    assert receipt["selected_facts"] == 3
    assert receipt["excluded_profiles"] == {"befu": 1, "hyefu": 1}
    assert receipt["row_counts"] == {
        "historical_nominal.parquet": 1,
        "historical_yoy.parquet": 1,
        "health_spending_gdp_share.parquet": 1,
        "recent_classification_trends.parquet": 1,
        "recent_functional_breakdown.parquet": 0,
    }
    assert export.export_gold(*raw_run, two, dry_run=False) == receipt
    assert len(list(one.iterdir())) == 8
    for path in one.iterdir():
        assert path.read_bytes() == (two / path.name).read_bytes()
    for name, digest in receipt["output_sha256"].items():
        assert hashlib.sha256((one / name).read_bytes()).hexdigest() == digest
    yoy = pq.read_table(one / "historical_yoy.parquet").to_pylist()[0]
    assert yoy["yoy_percent"] is None
    assert yoy["yoy_status"] == "no_previous_observation"
    assert str(yoy["exact_amount"]) == "605.70000000000005000"
    assert pq.read_table(one / "recent_functional_breakdown.parquet").schema.names
    assert len((one / "field_lineage.jsonl").read_text().splitlines()) == 3


def test_preserve_existing_output(
    raw_run: tuple[Path, Path, str], tmp_path: Path
) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    marker = output / "original"
    marker.write_bytes(b"keep")
    with pytest.raises(ValueError, match="gold_export_failed"):
        export.export_gold(*raw_run, output, dry_run=False)
    assert marker.read_bytes() == b"keep"


@pytest.mark.parametrize("target", [0, 1])
def test_cannot_write_inside_inputs(
    raw_run: tuple[Path, Path, str], target: int
) -> None:
    output = (raw_run[0] if target == 0 else raw_run[1]) / "bad"
    with pytest.raises(ValueError, match="gold_export_failed"):
        export.export_gold(*raw_run, output, dry_run=False)
    assert not output.exists()


def test_redacted_partial_failure(
    raw_run: tuple[Path, Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        message = "secret URL must not leak"
        raise OSError(message)

    monkeypatch.setattr(export.pq, "write_table", fail)
    output = tmp_path / "partial"
    with pytest.raises(ValueError, match=r"^gold_export_failed:OSError$"):
        export.export_gold(*raw_run, output, dry_run=False)
    failure = json.loads((output / "FAILURE.json").read_text())
    assert failure["error_class"] == "OSError"
    assert "secret" not in json.dumps(failure)
    assert not (output / "MANIFEST.json").exists()


def test_bad_pin_writes_nothing(
    raw_run: tuple[Path, Path, str], tmp_path: Path
) -> None:
    output = tmp_path / "bad-pin"
    with pytest.raises(ValueError, match="gold_export_failed"):
        export.export_gold(raw_run[0], raw_run[1], "f" * 64, output, dry_run=False)
    assert not output.exists()


def test_cli_dry_run_write_and_redacted_error(
    raw_run: tuple[Path, Path, str], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    def run(*, dry_run: bool = True) -> int:
        return health_appropriations_export_gold(
            raw_run=raw_run[0],
            store_root=raw_run[1],
            manifest_sha256=raw_run[2],
            output_dir=tmp_path / "cli",
            dry_run=dry_run,
        )

    assert run() == 0
    assert json.loads(capsys.readouterr().out)["status"] == "planned"
    assert run(dry_run=False) == 0
    assert json.loads(capsys.readouterr().out)["status"] == "passed"
    assert run(dry_run=False) == 2
    assert (
        json.loads(capsys.readouterr().out)["error"] == "gold_export_failed:ValueError"
    )


def test_manifest_schema(raw_run: tuple[Path, Path, str], tmp_path: Path) -> None:
    receipt = export.export_gold(*raw_run, tmp_path / "schema", dry_run=False)
    schema = json.loads(Path("schemas/health-raw-gold-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(receipt)


def test_symlink_output_rejected(
    raw_run: tuple[Path, Path, str], tmp_path: Path
) -> None:
    destination = tmp_path / "destination"
    destination.mkdir()
    link = tmp_path / "link"
    link.symlink_to(destination, target_is_directory=True)
    with pytest.raises(ValueError, match="gold_export_failed"):
        export.export_gold(*raw_run, link, dry_run=False)
    assert list(destination.iterdir()) == []


@pytest.mark.parametrize("profile", ["budget", "historical"])
@pytest.mark.parametrize("reserved", [None, "spoofed"])
def test_source_profile_annotation_collision_is_rejected(
    raw_run: tuple[Path, Path, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    profile: str,
    reserved: object,
) -> None:
    facts, lineage = export.read_verified_run(*raw_run)
    facts[profile][0]["input_profile"] = reserved
    monkeypatch.setattr(export, "read_verified_run", lambda *_args: (facts, lineage))
    output = tmp_path / "collision"
    with pytest.raises(ValueError, match="gold_export_failed:ValueError"):
        export.export_gold(*raw_run, output, dry_run=False)
    assert not output.exists()
