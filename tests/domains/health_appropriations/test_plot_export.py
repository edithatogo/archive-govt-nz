"""Source plots are exclusive, reproducible local derivatives of pinned Gold."""

import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import pytest
from matplotlib.patches import Rectangle
from tests.domains.health_appropriations.test_plot_contracts import tables

from archive_govt_nz.domains.health_appropriations import plot_export as export
from archive_govt_nz.domains.health_appropriations.gold_export import export_gold
from archive_govt_nz.domains.health_appropriations.plot_contracts import (
    build_plot_contracts,
)


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


def test_figure_marks_preserve_zero_and_negative_values() -> None:
    contracts = build_plot_contracts(tables())
    for name, contract in contracts.items():
        figure = export.figure_for_contract(contract)
        axis = figure.axes[0]
        assert axis.get_title() == contract["title"]
        assert axis.get_xlabel() == contract["xlabel"]
        assert axis.get_ylabel() == contract["ylabel"]
        if name == "historical_health_spending_yoy_growth.png":
            assert len(axis.patches) == 1
            assert isinstance(axis.patches[0], Rectangle)
            assert axis.patches[0].get_height() == 0
        if contract["kind"] == "barh":
            assert isinstance(axis.patches[0], Rectangle)
            assert axis.patches[0].get_width() == -12.345
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


@pytest.mark.parametrize("limit", ["_MAX_POINTS", "_MAX_SERIES"])
def test_plot_resource_limit(limit: str, monkeypatch: pytest.MonkeyPatch) -> None:
    contract = build_plot_contracts(tables())["historical_health_spending_nominal.png"]
    monkeypatch.setattr(export, limit, 1)
    export.figure_for_contract(contract).clear()
    monkeypatch.setattr(export, limit, 0)
    with pytest.raises(ValueError, match="plot_resource_limit"):
        export.figure_for_contract(contract)
