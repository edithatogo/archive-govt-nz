"""Context Gold verifies source Silver and reports exact-series coverage."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pyarrow.parquet as pq
import pytest

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
