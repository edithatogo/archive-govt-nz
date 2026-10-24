"""Recovery exercises canonical queries and composite metadata on rebuilt bytes."""

from __future__ import annotations

import json
import shutil
from decimal import Decimal
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from tests.domains.health_appropriations.test_canonical_gold_queries import (
    fact_package,
    repin,
    source_row,
)
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
    assert len(result["products"]) == 10
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


@pytest.mark.parametrize("case", ["correct", "wrong_slice", "reversed"])
def test_truncated_query_recovery_requires_the_ordered_source_slice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    first, second = canonical_pair(tmp_path)
    query = MODULE.canonical_gold_queries
    name, schema = query.PRODUCTS["historical"]
    rows = [
        {**source_row(schema, 2024), "period_token": f"period-{index:04}"}
        for index in reversed(range(query.MAX_QUERY_ROWS + 1))
    ]
    for root in (first, second):
        pq.write_table(
            pa.Table.from_pylist(rows, schema=schema),
            root / name,
            compression="zstd",
            use_dictionary=False,
        )
        # Row counts belong to the package contract, not just the Parquet bytes.
        marker = root / "MANIFEST.json"
        manifest = json.loads(marker.read_bytes())
        manifest["outputs"][name]["rows"] = len(rows)
        marker.write_text(json.dumps(manifest))
        repin(root)
    original_query = query.query_canonical_gold

    def altered_query(
        root: Path, pin: str, *, product: str, limit: int
    ) -> dict[str, Any]:
        result = original_query(root, pin, product=product, limit=limit)
        if result.get("product") == "historical":
            if case == "wrong_slice":
                last = dict(result["rows"][0])
                last["period_token"] = f"period-{query.MAX_QUERY_ROWS:04}"
                result["rows"] = [*result["rows"][1:], last]
            elif case == "reversed":
                result["rows"].reverse()
        return result

    monkeypatch.setattr(query, "query_canonical_gold", altered_query)
    if case == "correct":
        receipt = MODULE.canonical_query_recovery_report(first, second)
        assert receipt["products"]["historical"]["truncated"] is True
    else:
        with pytest.raises(RuntimeError, match="canonical_gold_query_recovery_failed"):
            MODULE.canonical_query_recovery_report(first, second)


def test_ordered_readback_keeps_numeric_null_list_and_duplicate_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second = canonical_pair(tmp_path)
    query = MODULE.canonical_gold_queries
    monkeypatch.setattr(query, "MAX_QUERY_ROWS", 5)
    examples = {
        "historical": [
            {"currency": currency, "amount": Decimal(amount)}
            for currency, amount in (
                (None, "-100"),
                ("AUD", "10"),
                ("AUD", "2"),
                ("AUD", "-1"),
                ("AUD", "2"),
                ("NZD", "-1000"),
            )
        ],
        "budget": [
            {"input_record_ids": ids}
            for ids in (["b"], ["a", None], ["a", "b"], ["a"], [])
        ],
    }
    for root in (first, second):
        marker = root / "MANIFEST.json"
        manifest = json.loads(marker.read_bytes())
        for product, changes in examples.items():
            name, schema = query.PRODUCTS[product]
            rows = [{**source_row(schema, 2024), **change} for change in changes]
            pq.write_table(
                pa.Table.from_pylist(rows, schema=schema),
                root / name,
                compression="zstd",
                use_dictionary=False,
            )
            manifest["outputs"][name]["rows"] = len(rows)
        marker.write_text(json.dumps(manifest))
        pin = repin(root)
    historical = query.query_canonical_gold(first, pin, product="historical", limit=5)
    assert [r["currency"] for r in historical["rows"]] == ["AUD"] * 4 + ["NZD"]
    assert [Decimal(r["amount"]) for r in historical["rows"]] == [
        Decimal(value) for value in ("-1", "2", "2", "10", "-1000")
    ]
    budget = query.query_canonical_gold(first, pin, product="budget", limit=5)
    assert [r["input_record_ids"] for r in budget["rows"]] == [
        [],
        ["a"],
        ["a", "b"],
        ["a", None],
        ["b"],
    ]
    assert MODULE.canonical_query_recovery_report(first, second)["repeat_identical"]


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
    assert result["recordsets"] == 15
    assert result["schema_version"] == "archive-govt-nz.health-gold-metadata/v4"
    assert result["rights"] == "not_evaluated"
    assert result["publication"] == "not_performed"
    assert before == (MODULE.tree(first), MODULE.tree(second))


def test_gold_inputs_bind_the_corresponding_fresh_run(tmp_path: Path) -> None:
    pharmac = tmp_path / "pharmac-silver-2"
    pharmac.mkdir()
    (pharmac / "MANIFEST.json").write_bytes(b"fresh second-run manifest")
    fresh_roots = [
        tmp_path / f"moh-{profile.replace('/', '-')}-2"
        for profile in MODULE.moh_canonical_projection.PROFILES
    ] + [tmp_path / "crown-silver-2", tmp_path / "hyefu-crown-silver-2"]
    for fresh_root in fresh_roots:
        fresh_root.mkdir()
        (fresh_root / "MANIFEST.json").write_bytes(
            f"fresh manifest for {fresh_root.name}".encode()
        )
    inputs = MODULE.canonical_gold_inputs(tmp_path, 2)
    assert inputs.pharmac is not None
    assert inputs.pharmac.root == pharmac
    assert inputs.moh is not None
    assert all(p.root.name.endswith("-2") for p in inputs.moh.packages)
    assert all(
        p.manifest_sha256 == MODULE.digest(p.root / "MANIFEST.json")
        for p in inputs.moh.packages
    )
    assert inputs.crown is not None
    assert inputs.crown.befu_root == tmp_path / "crown-silver-2"
    assert inputs.crown.hyefu_root == tmp_path / "hyefu-crown-silver-2"
    assert inputs.crown.befu_manifest_sha256 == MODULE.digest(
        inputs.crown.befu_root / "MANIFEST.json"
    )
    assert inputs.crown.hyefu_manifest_sha256 == MODULE.digest(
        inputs.crown.hyefu_root / "MANIFEST.json"
    )
