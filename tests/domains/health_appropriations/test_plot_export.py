"""Source plots are exclusive, reproducible local derivatives of pinned Gold."""

import hashlib
import json
from pathlib import Path
from typing import Any

import matplotlib as mpl
import numpy as np
import pytest
from jsonschema import Draft202012Validator
from matplotlib.colors import to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from tests.domains.health_appropriations.test_plot_contracts import (
    budget,
    historical,
    tables,
)

from archive_govt_nz.cli import health_appropriations_render_plots
from archive_govt_nz.domains.health_appropriations import plot_export as export
from archive_govt_nz.domains.health_appropriations.gold_export import export_gold
from archive_govt_nz.domains.health_appropriations.plot_contracts import (
    build_plot_contracts,
)
from archive_govt_nz.domains.health_appropriations.plot_export import _save_plot


@pytest.fixture
def gold(raw_run: tuple[Path, Path, str], tmp_path: Path) -> tuple[Path, str]:
    root = tmp_path / "gold"
    export_gold(*raw_run, root, dry_run=False)
    return root, hashlib.sha256((root / "MANIFEST.json").read_bytes()).hexdigest()


def test_preflight_and_two_reproducible_builds(
    gold: tuple[Path, str], tmp_path: Path
) -> None:
    one, two = tmp_path / "plots-one", tmp_path / "plots-two"
    assert export.render_plots(*gold, one)["status"] == "planned"
    assert not one.exists()
    receipt = export.render_plots(*gold, one, dry_run=False)
    assert receipt["status"] == "passed"
    with mpl.rc_context(
        {
            "savefig.transparent": True,
            "savefig.facecolor": "pink",
            "font.family": ["monospace"],
        }
    ):
        assert receipt == export.render_plots(*gold, two, dry_run=False)
    assert len(list(one.iterdir())) == 8
    for path in one.iterdir():
        assert path.read_bytes() == (two / path.name).read_bytes()
        if path.suffix == ".png":
            assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert receipt["gold_manifest_sha256"] == gold[1]
    assert len(receipt["output_sha256"]) == 7
    schema = json.loads(Path("schemas/health-source-plots-v1.schema.json").read_text())
    Draft202012Validator(schema).validate(receipt)


def test_figure_marks_preserve_zero_and_negative_values() -> None:
    contracts = build_plot_contracts(tables())
    for name, contract in contracts.items():
        figure = export.figure_for_contract(contract)
        axis = figure.axes[0]
        assert axis.get_title() == contract["title"]
        assert axis.get_xlabel() == contract["xlabel"]
        assert axis.get_ylabel() == contract["ylabel"]
        expected_count = sum(len(series["points"]) for series in contract["series"])
        assert (
            figure.texts[0]
            .get_text()
            .startswith(f"{expected_count} plotted observations;")
        )
        assert axis.get_axisbelow() is True
        assert not axis.spines["top"].get_visible()
        assert not axis.spines["right"].get_visible()
        assert axis.title.get_usetex() is False
        assert axis.title.get_parse_math() is False
        if not contract["series"]:
            assert "No eligible observations" in [
                text.get_text() for text in axis.texts
            ]
        if name == "historical_health_spending_yoy_growth.png":
            assert len(axis.patches) == 1
            patch = axis.patches[0]
            assert isinstance(patch, Rectangle)
            assert patch.get_height() == 0
            assert patch.get_facecolor() == to_rgba("#2563eb")
        if contract["kind"] == "barh":
            patch = axis.patches[0]
            assert isinstance(patch, Rectangle)
            assert patch.get_width() == -12.345
        figure.clear()


@pytest.mark.parametrize("mode", ["existing", "overlap", "symlink", "bad_pin"])
def test_preserved_output_and_input_boundaries(
    gold: tuple[Path, str], tmp_path: Path, mode: str
) -> None:
    output = tmp_path / "output"
    pin = gold[1]
    if mode == "existing":
        output.mkdir()
    elif mode == "overlap":
        output = gold[0] / "plots"
    elif mode == "symlink":
        output.symlink_to(gold[0], target_is_directory=True)
    else:
        pin = "f" * 64
    before = {p.name: p.read_bytes() for p in gold[0].iterdir()}
    with pytest.raises(ValueError, match="plot_export_failed"):
        export.render_plots(gold[0], pin, output, dry_run=False)
    assert {p.name: p.read_bytes() for p in gold[0].iterdir()} == before


def test_partial_failure_preserves_redacted_receipt(
    gold: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        message = "private path must not appear"
        raise OSError(message)

    monkeypatch.setattr(export, "_save_plot", fail)
    output = tmp_path / "partial"
    with pytest.raises(ValueError, match="plot_export_failed:OSError"):
        export.render_plots(*gold, output, dry_run=False)
    assert json.loads((output / "FAILURE.json").read_text())["error_class"] == "OSError"
    assert not (output / "MANIFEST.json").exists()
    assert "private" not in (output / "FAILURE.json").read_text()


@pytest.mark.parametrize("value", ["NaN", "Infinity", "1e1000"])
def test_nonfinite_display_values_rejected(value: str) -> None:
    contract = build_plot_contracts(tables())["historical_health_spending_nominal.png"]
    contract["series"][0]["points"][0]["y"] = value
    with pytest.raises(ValueError, match="nonfinite_plot_value"):
        export.figure_for_contract(contract)


def test_temporal_bar_positions_preserve_year_gaps_and_sparse_ticks() -> None:
    source = tables()
    source["historical_yoy.parquet"] = [
        historical(year) for year in range(1973, 2025) if year != 1990
    ]
    contract = build_plot_contracts(source)["historical_health_spending_yoy_growth.png"]
    figure = export.figure_for_contract(contract)
    axis = figure.axes[0]
    centers = []
    for patch in axis.patches:
        assert isinstance(patch, Rectangle)
        centers.append(patch.get_x() + patch.get_width() / 2)
    assert centers == [year for year in range(1973, 2025) if year != 1990]
    assert len(axis.get_xticks()) <= 12
    figure.clear()


def test_breakdown_has_exact_value_labels_and_contrasting_hatches() -> None:
    contract = build_plot_contracts(tables())[
        "recent_appropriations_functional_breakdown_2025_Estimated_Actual.png"
    ]
    contract["series"][0]["points"][0]["y"] = "26740144.000"
    figure = export.figure_for_contract(contract)
    axis = figure.axes[0]
    assert "26,740,144.000" in [text.get_text() for text in axis.texts]
    assert axis.patches[0].get_edgecolor() != axis.patches[0].get_facecolor()
    figure.clear()


def test_same_year_groups_do_not_overlap_and_palette_is_explicit() -> None:
    source = tables()
    source["recent_classification_trends.parquet"] = [
        budget(2024),
        budget(2024, amount_type="Main Estimates"),
    ]
    contract = build_plot_contracts(source)["recent_trends_health_classification.png"]
    for series in contract["series"]:
        series["points"][0]["y"] = "12.345"
    figure = export.figure_for_contract(contract)
    patches = figure.axes[0].patches
    assert len(patches) == 2
    for index, patch in enumerate(patches):
        assert isinstance(patch, Rectangle)
        assert patch.get_x() + patch.get_width() / 2 == pytest.approx(
            2023.8 + index * 0.4
        )
        assert patch.get_width() == pytest.approx(0.4)
        assert patch.get_facecolor() == to_rgba(("#2563eb", "#1d4ed8")[index])
        assert patch.get_hatch() == ("", "//")[index]
    assert "Estimated Actual" in figure.axes[0].get_legend_handles_labels()[1][0]
    figure.clear()


def test_segment_markers_and_labels_are_not_color_only() -> None:
    source = tables()
    source["historical_nominal.parquet"] = [
        historical(2024),
        historical(2025, accounting_basis="IFRS"),
    ]
    contract = build_plot_contracts(source)["historical_health_spending_nominal.png"]
    figure = export.figure_for_contract(contract)
    lines = figure.axes[0].lines
    assert [line.get_marker() for line in lines] == ["o", "s"]
    assert [line.get_color() for line in lines] == ["#2563eb", "#1d4ed8"]
    assert all(
        line.get_linewidth() == 1.4 and line.get_markersize() == 4 for line in lines
    )
    assert lines[0].get_label() == "2024 | Cash | 6 | aaaaaaaaaaaa"
    figure.clear()


def test_disconnected_context_keeps_style_and_matching_legend() -> None:
    source = tables()
    source["historical_nominal.parquet"] = [
        historical(2000),
        historical(2001),
        historical(2003),
        historical(2004, accounting_basis="IFRS"),
    ]
    contract = build_plot_contracts(source)["historical_health_spending_nominal.png"]
    # Canonical context identity is independent of dictionary insertion order.
    contract["series"][1]["context"] = dict(
        reversed(list(contract["series"][1]["context"].items()))
    )
    figure = export.figure_for_contract(contract)
    lines = figure.axes[0].lines
    for line, years in zip(lines, [[2000, 2001], [2003], [2004]], strict=True):
        assert np.array_equal(line.get_xdata(), years)
    assert [line.get_marker() for line in lines] == ["o", "o", "s"]
    assert [line.get_color() for line in lines] == ["#2563eb", "#2563eb", "#1d4ed8"]
    handles = figure.legends[0].legend_handles
    for handle, style in zip(
        handles, [("#2563eb", "o"), ("#1d4ed8", "s")], strict=True
    ):
        assert isinstance(handle, Line2D)
        assert (handle.get_color(), handle.get_marker()) == style
    figure.clear()


@pytest.mark.parametrize(
    "other_context",
    [
        {"source_object_sha256": "a" * 12 + "b" * 52},
        {"unlabelled_source_context": "distinct"},
    ],
)
def test_colliding_display_labels_do_not_merge_full_contexts(
    other_context: dict[str, str],
) -> None:
    contract = build_plot_contracts(tables())["historical_health_spending_nominal.png"]
    original = contract["series"][0]
    contract["series"].append(
        {
            "context": {**original["context"], **other_context},
            "points": original["points"],
        }
    )
    figure = export.figure_for_contract(contract)
    lines = figure.axes[0].lines
    assert [line.get_marker() for line in lines] == ["o", "s"]
    assert len({line.get_label() for line in lines}) == 2
    legend = figure.legends[0]
    assert len(legend.legend_handles) == 2
    assert [text.get_text() for text in legend.texts] == [
        "2024 | Cash | 6 | aaaaaaaaaaaa [context 1]",
        "2024 | Cash | 6 | aaaaaaaaaaaa [context 2]",
    ]
    figure.clear()


@pytest.mark.parametrize("limit", ["_MAX_POINTS", "_MAX_SERIES"])
def test_plot_resource_limit(limit: str, monkeypatch: pytest.MonkeyPatch) -> None:
    contract = build_plot_contracts(tables())["historical_health_spending_nominal.png"]
    monkeypatch.setattr(export, limit, 1)
    export.figure_for_contract(contract).clear()
    monkeypatch.setattr(export, limit, 0)
    with pytest.raises(ValueError, match="plot_resource_limit"):
        export.figure_for_contract(contract)


@pytest.mark.parametrize("limit", ["_MAX_POINTS", "_MAX_SERIES"])
def test_preflight_checks_render_limits(
    gold: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch, limit: str
) -> None:
    monkeypatch.setattr(export, limit, 0)
    output = tmp_path / "oversized"
    with pytest.raises(ValueError, match="plot_export_failed:ValueError"):
        export.render_plots(*gold, output)
    assert not output.exists()


def test_cli_preflight_render_and_redacted_failure(
    gold: tuple[Path, str], tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "cli-plots"
    assert (
        health_appropriations_render_plots(
            gold_dir=gold[0], manifest_sha256=gold[1], output_dir=output
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "planned"
    assert not output.exists()
    assert (
        health_appropriations_render_plots(
            gold_dir=gold[0], manifest_sha256=gold[1], output_dir=output, dry_run=False
        )
        == 0
    )
    assert json.loads(capsys.readouterr().out)["status"] == "passed"
    assert (
        health_appropriations_render_plots(
            gold_dir=gold[0], manifest_sha256=gold[1], output_dir=output, dry_run=False
        )
        == 2
    )
    assert (
        json.loads(capsys.readouterr().out)["error"] == "plot_export_failed:ValueError"
    )


def test_fast_export_protocol_and_real_single_png(
    gold: tuple[Path, str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep transaction mutation tests fast; real six-PNG rebuilds run separately."""

    def png_stub(plot: dict[str, Any], path: Path) -> None:
        path.write_bytes(
            b"\x89PNG\r\n\x1a\n" + json.dumps(plot, sort_keys=True).encode()
        )

    one, two = tmp_path / "fast-one", tmp_path / "fast-two"
    with monkeypatch.context() as context:
        context.setattr(export, "_save_plot", png_stub)
        assert export.render_plots(*gold, one)["status"] == "planned"
        assert not one.exists()
        receipt = export.render_plots(*gold, one, dry_run=False)
        assert receipt["status"] == "passed"
        assert export.render_plots(*gold, two, dry_run=False) == receipt
        assert len(list(one.iterdir())) == 8
        for path in one.iterdir():
            assert path.read_bytes() == (two / path.name).read_bytes()
        for name, digest in receipt["output_sha256"].items():
            assert hashlib.sha256((one / name).read_bytes()).hexdigest() == digest
    # Restore the real (including potentially mutated) writer before exercising it.
    contract = build_plot_contracts(tables())["historical_health_spending_nominal.png"]
    _save_plot(contract, tmp_path / "real-one.png")
    with mpl.rc_context({"savefig.transparent": True, "savefig.facecolor": "pink"}):
        _save_plot(contract, tmp_path / "real-two.png")
    assert (tmp_path / "real-one.png").read_bytes() == (
        tmp_path / "real-two.png"
    ).read_bytes()
