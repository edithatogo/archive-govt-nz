"""Contract tests for clean-room recovery receipts."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch

SCRIPT = Path(__file__).parents[3] / "tools" / "health_recovery_assurance.py"
SPEC = importlib.util.spec_from_file_location("health_recovery_assurance", SCRIPT)
assert SPEC is not None
assert SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_digest_and_tree_are_content_based(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "a").write_bytes(b"bronze")
    expected = MODULE.digest(source / "a")
    assert MODULE.tree(source) == {"a": {"bytes": 6, "sha256": expected}}


def test_repeat_build_mismatch_fails_closed(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "MANIFEST.json").write_bytes(b"first")
    (second / "MANIFEST.json").write_bytes(b"second")
    with pytest.raises(RuntimeError, match=r"^canonical_gold_repeat_mismatch$"):
        MODULE.compare_product_outputs(first, second, "canonical_gold")


def test_context_source_binding_uses_captured_source_census() -> None:
    binding = MODULE.context_source_binding("wage")
    assert binding == {
        "source_object_sha256": (
            "1af2e7e37f1c108a2656842cf1f519c903e1a982bcdc03ee02d0ad888ebc3a97"
        ),
        "source_locator": (
            "https://www.stats.govt.nz/assets/Uploads/Labour-market-statistics/"
            "Labour-market-statistics-June-2026-quarter/Download-data/"
            "quarterly-employment-survey-june-2026-quarter.xlsx"
        ),
        "source_vintage": "QES-2026-Q2",
        "observed_at": "2026-08-29T09:00:17Z",
    }


def test_context_source_binding_rejects_changed_census_pin(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(MODULE, "SOURCE_CENSUS_SHA256", "0" * 64)
    with pytest.raises(RuntimeError, match=r"^source_census_pin_mismatch$"):
        MODULE.context_source_binding("wage")


def test_clean_room_rebuilds_supported_products_and_reports_blockers(
    monkeypatch: MonkeyPatch, tmp_path: Path
) -> None:
    archive = tmp_path / "archive"
    cas = archive / "bronze-cas"
    obj_digest = "a" * 64
    obj = cas / "sha256" / obj_digest[:2] / obj_digest
    obj.parent.mkdir(parents=True)
    obj.write_bytes(b"immutable bronze")
    track = tmp_path / "track"
    track.mkdir()
    (track / "population-annual-context.json").write_text(
        '{"retrieved_at":"2026-09-25T09:37:50Z","release_date":"2026-08-18",'
        '"export_route":"https://example.test/export"}'
    )
    monkeypatch.setattr(MODULE, "ARCHIVE", archive)
    monkeypatch.setattr(MODULE, "TRACK", track)
    monkeypatch.setattr(MODULE, "CONTEXT", {})
    monkeypatch.setattr(MODULE, "canonical_inputs", lambda: ())
    monkeypatch.setattr(
        MODULE,
        "rebuild_donor_products",
        lambda _root, _index: {
            "raw": {"MANIFEST.json": {"sha256": "raw"}},
            "compatibility": {"compatibility.sqlite": {"sha256": "sqlite"}},
            "gold": {"MANIFEST.json": {"sha256": "gold"}},
            "plots": {"plot.png": {"sha256": "plot"}},
            "raw_manifest_sha256": "raw-pin",
            "compatibility_facts": 341,
            "gold_selected_facts": 321,
            "plot_count": 6,
        },
    )

    def fake_eight_stage(root: Path, index: int) -> dict[str, object]:
        output = root / f"eight-stage-{index}"
        output.mkdir()
        (output / "MANIFEST.json").write_bytes(b"fixed eight stage")
        return {
            "files": MODULE.tree(output),
            "manifest_sha256": "eight-stage-pin",
            "profile_count": 12,
            "fact_count": 739,
            "rights_state": "not_evaluated",
            "gold_selection": "not_performed",
            "publication": "not_performed",
        }

    monkeypatch.setattr(MODULE, "rebuild_eight_stage", fake_eight_stage)
    monkeypatch.setattr(
        MODULE,
        "_rebuild_pharmac_canonical",
        lambda _root, _index: {
            "source_object_sha256": "a" * 64,
            "canonical_fact_sha256": "facts",
            "canonical_lineage_sha256": "lineage",
        },
    )
    monkeypatch.setattr(
        MODULE,
        "_rebuild_qes_canonical",
        lambda _root, _index: {
            "source_object_sha256": "b" * 64,
            "canonical_fact_sha256": "qes-facts",
            "canonical_lineage_sha256": "qes-lineage",
        },
    )

    def fake_context(
        _silver_root: Path, _source_root: Path, output: Path, *, write: bool = False
    ) -> dict[str, str]:
        _ = write
        output.mkdir()
        (output / "MANIFEST.json").write_bytes(b"fixed context")
        return {"status": "complete"}

    monkeypatch.setattr(MODULE, "export_context_gold", fake_context)

    class FakeColumn:
        def to_pylist(self) -> list[str]:
            return []

    class FakeTable:
        num_rows = 0

        def column(self, _name: str) -> FakeColumn:
            return FakeColumn()

    monkeypatch.setattr(
        MODULE, "query_context_observations", lambda _root, _pin: FakeTable()
    )
    monkeypatch.setattr(
        MODULE,
        "normalize_population_annual",
        lambda _source, output, **_kwargs: (
            output.mkdir(),
            (output / "MANIFEST.json").write_bytes(b"silver"),
            {"counts": {"facts": 1}},
        )[-1],
    )
    result = MODULE.run()
    assert result["status"] == "partial_with_blockers"
    assert result["bronze_objects_unchanged"] is True
    assert result["products_rebuilt"]["canonical_gold"]["status"] == "blocked"
    assert result["products_rebuilt"]["context_gold"]["repeat_identical"] is True
    assert (
        result["products_rebuilt"]["pharmac_canonical_projection"]["repeat_identical"]
        is True
    )
    assert (
        result["products_rebuilt"]["qes_canonical_projection"]["repeat_identical"]
        is True
    )
    assert (
        result["products_rebuilt"]["canonical_context_consumer"]["status"]
        == "verified_read_only_projection"
    )
    assert result["products_rebuilt"]["donor_sqlite_gold_plots"]["repeat_identical"]
    assert result["products_rebuilt"]["donor_source_native_silver"]["repeat_identical"]
    assert (
        result["products_rebuilt"]["donor_sqlite_gold_plots"]["compatibility_facts"]
        == 341
    )
    assert "compatibility_sqlite" not in result["required_but_not_rebuilt"]
    assert "all_source_native_silver" not in result["required_but_not_rebuilt"]
    assert (
        "additional_source_native_silver_profiles_and_canonical_adapters"
        in result["required_but_not_rebuilt"]
    )
