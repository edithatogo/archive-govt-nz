"""Recovery exercises canonical queries and composite metadata on rebuilt bytes."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from tests.domains.health_appropriations.test_canonical_gold_queries import fact_package
from tests.domains.health_appropriations.test_gold_metadata import (
    packages as legacy_packages,
)
from tests.domains.health_appropriations.test_health_recovery_assurance import MODULE


def canonical_pair(root: Path) -> tuple[Path, Path]:
    fixture_root = root / "fixture"
    fixture_root.mkdir()
    package, _pin = fact_package(fixture_root)
    first, second = root / "canonical-1", root / "canonical-2"
    shutil.copytree(package, first)
    shutil.copytree(package, second)
    return first, second


def test_recovery_queries_all_products_without_changing_gold(tmp_path: Path) -> None:
    first, second = canonical_pair(tmp_path)
    before = (MODULE.tree(first), MODULE.tree(second))
    result = MODULE.canonical_query_recovery_report(first, second)
    assert result["repeat_identical"] is True
    assert result["gold_unchanged"] is True
    assert len(result["products"]) == 8
    for product in result["products"].values():
        assert product["source_rows"] == 2
        assert product["returned_rows"] == 2
        assert product["truncated"] is False
        assert product["exact_readback"] is True
    assert before == (MODULE.tree(first), MODULE.tree(second))


def test_query_recovery_rejects_damaged_repeat_package(tmp_path: Path) -> None:
    first, second = canonical_pair(tmp_path)
    (second / "historical_observations.parquet").write_bytes(b"damaged")
    with pytest.raises(RuntimeError, match="canonical_gold_query_recovery_failed"):
        MODULE.canonical_query_recovery_report(first, second)


def test_composite_metadata_rebuilds_from_both_fresh_gold_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second = canonical_pair(tmp_path)
    fixture_root = tmp_path / "legacy-fixture"
    fixture_root.mkdir()
    packages = legacy_packages(fixture_root, monkeypatch)
    for run in ("first", "second"):
        target = tmp_path / "analytical-metadata" / run
        target.mkdir(parents=True)
        for package in packages:
            name = "gold" if package.profile == "fiscal_analytical" else "budget-gold"
            shutil.copytree(package.root, target / name)
    before = (MODULE.tree(first), MODULE.tree(second))
    result = MODULE.combined_metadata_recovery_report(tmp_path)
    assert result["repeat_identical"] is True
    assert result["metadata_reconstructed"] is True
    assert result["packages"] == 3
    assert result["recordsets"] == 13
    assert result["schema_version"] == "archive-govt-nz.health-gold-metadata/v4"
    assert result["rights"] == "not_evaluated"
    assert result["publication"] == "not_performed"
    assert before == (MODULE.tree(first), MODULE.tree(second))


def test_gold_inputs_bind_the_corresponding_fresh_run(tmp_path: Path) -> None:
    pharmac = tmp_path / "pharmac-silver-2"
    pharmac.mkdir()
    (pharmac / "MANIFEST.json").write_bytes(b"fresh second-run manifest")
    inputs = MODULE.canonical_gold_inputs(tmp_path, 2)
    assert inputs.pharmac is not None
    assert inputs.pharmac.root == pharmac
    assert inputs.moh is not None
    assert all(p.root.name.endswith("-2") for p in inputs.moh.packages)
    assert inputs.crown is not None
    assert inputs.crown.befu_root == tmp_path / "crown-silver-2"
    assert inputs.crown.hyefu_root == tmp_path / "hyefu-crown-silver-2"
