"""Context Gold verifies source Silver and reports exact-series coverage."""

from __future__ import annotations

import hashlib
import json
import runpy
import sys
from decimal import Decimal
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from archive_govt_nz.cli import app
from archive_govt_nz.domains.health_appropriations import context_gold

TRACK = Path("conductor/tracks/health_appropriations_medallion_assimilation_20260829")
EXTERNAL = Path("/Volumes/PortableSSD/ArchiveGovtNZ/health-appropriations")
_PINNED_PACKAGES = (
    "raw-cpi-20260831-v1",
    "raw-qes-2026q2-20260831-v2",
    "raw-stats-gdp-20260831-v1",
    "population-annual-mean-context-20260925-v1",
)


def _roots() -> tuple[Path, Path]:
    silver = EXTERNAL / "silver"
    source = EXTERNAL / "bronze-cas/sha256"
    if not silver.is_dir() or not source.is_dir():
        pytest.skip("retained external health source packages are unavailable")
    return silver, source


@pytest.fixture
def synthetic_packages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path]:
    """Create pinned-shape source packages without relying on a mounted archive."""
    silver = tmp_path / "silver"
    source = tmp_path / "cas"
    silver.mkdir()
    source.mkdir()
    specifications = (
        (
            "raw-cpi-20260831-v1",
            "cpi_facts.parquet",
            "cpi",
            "CPIQ.SE9A",
            "f474a6a3bfbe9b6377c3c68cc94a4cb494335130af3940fe538f5a0dd1274e9d",
            "Stats-NZ-CPI-2026-Q2",
        ),
        (
            "raw-qes-2026q2-20260831-v2",
            "qes_facts.parquet",
            "wage",
            "QEMQ.SASZ9A",
            "1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97",
            "QES-2026-Q2",
        ),
        (
            "raw-stats-gdp-20260831-v1",
            "gdp_facts.parquet",
            "gdp",
            "SNEQ/SG03AB01GE00S900",
            "a7326e84e7704446a18e5c8942f99901a452b2170af4228e8a5c242a5532ed21",
            "StatsNZ-GDP-2026Q1",
        ),
        (
            "population-annual-mean-context-20260925-v1",
            "population_facts.parquet",
            "population",
            "DPE056AA:Mean year ended:Total:Total All Ages:Annual-Jun",
            "a52e0344d1b6e707de04b7b968f2667fc969c0f0777b319921ff716ead82a1d9",
            "2026-08-18",
        ),
    )
    source_file = tmp_path / "source.bin"
    source_file.write_bytes(b"pinned source fixture")
    monkeypatch.setattr(
        context_gold, "_source_path", lambda _root, _digest: source_file
    )
    for package, facts_file, family, _series, digest, vintage in specifications:
        directory = silver / package
        directory.mkdir()
        facts = [
            {
                "record_id": f"{family}-one",
                "source_object_sha256": digest,
                "source_vintage": vintage,
                "source_locator": f"{family}!A1:A2",
                "amount": Decimal("12.5"),
                "period_token": "FY2024" if family == "population" else "2024Q1",
                "source_quarter_token": None,
                "source_year_token": None,
                "valid_time_end": None,
                "status": "FINAL",
                "raw_status": None if family == "population" else "FINAL",
                "currency": None,
                "denominator_not_selected": None,
                "raw_values_json": "{}",
                "null_reason": None,
            },
            {
                "record_id": f"{family}-two",
                "source_object_sha256": digest,
                "source_vintage": vintage,
                "source_locator": f"{family}!A1:A2",
                "amount": Decimal("13.5") if family != "wage" else None,
                "period_token": "FY2025" if family == "population" else "2024Q2",
                "source_quarter_token": None,
                "source_year_token": None,
                "valid_time_end": None,
                "status": "PRELIMINARY",
                "raw_status": "P" if family == "population" else "PRELIMINARY",
                "currency": "NZD",
                "denominator_not_selected": True,
                "raw_values_json": json.dumps({"status": "P"})
                if family == "population"
                else "{}",
                "null_reason": "not_published" if family == "wage" else None,
            },
        ]
        if family == "cpi":
            facts[1]["period_token"] = None
            facts[1]["source_quarter_token"] = None
            facts[1]["source_year_token"] = None
            facts[1]["valid_time_end"] = "2024-06-30"
        fact_path = directory / facts_file
        pq.write_table(pa.Table.from_pylist(facts), fact_path)
        lineage_path = directory / "field_lineage.parquet"
        lineage = [
            {"record_id": fact["record_id"], "field": field}
            for fact in facts
            for field in ("amount", "period_token")
        ]
        pq.write_table(pa.Table.from_pylist(lineage), lineage_path)
        products = {
            facts_file: hashlib.sha256(fact_path.read_bytes()).hexdigest(),
            "field_lineage.parquet": hashlib.sha256(
                lineage_path.read_bytes()
            ).hexdigest(),
        }
        (directory / "MANIFEST.json").write_text(
            json.dumps(
                {
                    "source_object_sha256": digest,
                    "source_vintage": vintage,
                    "rights_state": "not_evaluated",
                    "output_sha256": products,
                }
            ),
            encoding="utf-8",
        )
    return silver, source


def test_synthetic_source_packages_cover_build_contract(
    tmp_path: Path, synthetic_packages: tuple[Path, Path]
) -> None:
    silver, source = synthetic_packages
    rows, _ = context_gold._source_native_packages(silver, source)  # noqa: SLF001
    context_gold._validate_rows(rows)  # noqa: SLF001
    receipt = context_gold.export_context_gold(
        silver, source, tmp_path / "out", write=True
    )
    assert receipt["input_records"] == 8
    assert receipt["series"] == 4
    assert receipt["eligible_context_observations"] == 5
    assert receipt["excluded_observations"] == 3
    rows = pq.read_table(tmp_path / "out" / "context_observations.parquet").to_pylist()
    assert {
        row["admission_reason"] for row in rows if row["family"] == "population"
    } == {
        "source_value_admitted",
        "provisional",
    }
    assert all(
        (tmp_path / "out" / name).is_file()
        for name in (
            "context_observations.parquet",
            "context_coverage.parquet",
            "MANIFEST.json",
        )
    )


def test_output_failure_writes_bounded_failure_receipt(
    tmp_path: Path,
    synthetic_packages: tuple[Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    silver, source = synthetic_packages
    output = tmp_path / "failed"
    original_read = context_gold.pq.read_table

    def fail_on_written_table(
        path: object, *args: object, **kwargs: object
    ) -> pa.Table:
        if isinstance(path, Path) and path.parent == output:
            message = "readback failed"
            raise OSError(message)
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(context_gold.pq, "read_table", fail_on_written_table)
    with pytest.raises(ValueError, match=r"^context_gold_invalid$"):
        context_gold.export_context_gold(silver, source, output, write=True)
    failure = json.loads((output / "FAILURE.json").read_text())
    assert failure["status"] == "incomplete"
    assert failure["error_type"] == "OSError"
    assert failure["publication"] == "not_performed"


def test_context_gold_cli_dry_run_and_write_flag(
    synthetic_packages: tuple[Path, Path],
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    silver, source = synthetic_packages
    with pytest.raises(SystemExit) as result:
        app(
            [
                "health-appropriations-build-context-gold",
                "--silver-root",
                str(silver),
                "--source-root",
                str(source),
                "--output-dir",
                str(tmp_path / "cli-plan"),
            ]
        )
    assert result.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "dry_run"
    with pytest.raises(SystemExit) as result:
        app(
            [
                "health-appropriations-build-context-gold",
                "--silver-root",
                str(silver),
                "--source-root",
                str(source),
                "--output-dir",
                str(tmp_path / "cli-write"),
                "--write",
            ]
        )
    assert result.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "complete"
    with pytest.raises(SystemExit) as result:
        app(
            [
                "health-appropriations-build-context-gold",
                "--silver-root",
                str(tmp_path / "missing-silver"),
                "--source-root",
                str(source),
                "--output-dir",
                str(tmp_path / "cli-failed"),
            ]
        )
    assert result.value.code == 2
    assert json.loads(capsys.readouterr().out)["status"] == "failed"


def test_standalone_builder_cli(
    tmp_path: Path,
    synthetic_packages: tuple[Path, Path],
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    silver, source = synthetic_packages
    output = tmp_path / "standalone"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_health_context_gold",
            "--silver-root",
            str(silver),
            "--source-root",
            str(source),
            "--output",
            str(output),
        ],
    )
    script = Path(__file__).parents[3] / "tools" / "build_health_context_gold.py"
    with pytest.raises(SystemExit) as result:
        runpy.run_path(str(script), run_name="__main__")
    assert result.value.code == 0
    assert json.loads(capsys.readouterr().out)["status"] == "dry_run"


def test_retained_context_silver_build_is_repeatable_and_source_separated(
    tmp_path: Path,
) -> None:
    silver, source = _roots()
    first = tmp_path / "first"
    second = tmp_path / "second"
    planned = context_gold.export_context_gold(silver, source, first)
    assert planned["input_records"] == 554
    assert planned["series"] == 4
    assert planned["eligible_context_observations"] == 524
    assert planned["excluded_observations"] == 30
    assert (
        planned["source_family_policy"]
        == "separate_series_vintages_no_joins_or_pooling"
    )
    assert planned["rights_state"] == "not_evaluated"
    assert planned["denominator_selection"] == "not_performed"
    assert planned["publication"] == "not_performed"
    assert not first.exists()
    written = context_gold.export_context_gold(silver, source, first, write=True)
    context_gold.export_context_gold(silver, source, second, write=True)
    assert {path.name: path.read_bytes() for path in first.iterdir()} == {
        path.name: path.read_bytes() for path in second.iterdir()
    }
    observations = pq.read_table(first / "context_observations.parquet")
    coverage = pq.read_table(first / "context_coverage.parquet")
    assert observations.num_rows == 554
    assert coverage.num_rows == 4
    assert set(observations["family"].to_pylist()) == {
        "cpi",
        "wage",
        "gdp",
        "population",
    }
    assert set(observations["source_vintage"].to_pylist()) == {
        "Stats-NZ-CPI-2026-Q2",
        "QES-2026-Q2",
        "StatsNZ-GDP-2026Q1",
        "2026-08-18",
    }
    assert all(
        row["period_policy"]
        == "source_tokens_sorted_lexically_without_cross_series_alignment"
        for row in coverage.to_pylist()
    )
    assert written["products"] == planned["products"]
    manifest = json.loads((first / "MANIFEST.json").read_text())
    assert set(manifest["products"]) == {
        "context_observations.parquet",
        "context_coverage.parquet",
    }
    for name, entry in manifest["products"].items():
        payload = (first / name).read_bytes()
        assert hashlib.sha256(payload).hexdigest() == entry["sha256"]
        assert len(payload) == entry["bytes"]


def test_population_provisional_and_missing_values_are_excluded(
    tmp_path: Path,
) -> None:
    silver, source = _roots()
    out = tmp_path / "context"
    context_gold.export_context_gold(silver, source, out, write=True)
    rows = pq.read_table(out / "context_observations.parquet").to_pylist()
    population = [row for row in rows if row["family"] == "population"]
    assert len(population) == 36
    assert sum(row["admission"] == "eligible_context_only" for row in population) == 33
    assert {
        row["admission_reason"]
        for row in population
        if row["admission"] != "eligible_context_only"
    } == {
        "figure_not_available",
        "status_not_retained_in_shared_fact",
    }
    assert all(
        row["admission"] != "eligible_context_only" or row["value"] is not None
        for row in population
    )


def test_any_source_package_fixity_drift_fails_closed() -> None:
    silver, source = _roots()
    rows, _ = context_gold._source_native_packages(silver, source)  # noqa: SLF001
    rows[0]["source_sha256"] = "0" * 64
    with pytest.raises(ValueError, match=r"^context_gold_invalid$"):
        context_gold._validate_rows(rows)  # noqa: SLF001


def test_package_context_marker_is_bound_to_the_observed_digest(
    tmp_path: Path,
) -> None:
    silver, source = _roots()
    package = silver / _PINNED_PACKAGES[0]
    manifest_path = package / "MANIFEST.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["source_object_sha256"] = "0" * 64
    changed = tmp_path / "silver"
    changed.mkdir()
    new_package = changed / _PINNED_PACKAGES[0]
    new_package.mkdir()
    (new_package / "MANIFEST.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match=r"^context_gold_invalid$"):
        context_gold._fact_package(  # noqa: SLF001
            changed,
            package=_PINNED_PACKAGES[0],
            facts_file="cpi_facts.parquet",
            source_digest=json.loads(manifest_path.read_text())["source_object_sha256"],
            family="cpi",
            series_id="CPIQ.SE9A",
            source_root=source,
        )
