"""Exclusive deterministic PNG derivatives of reviewed, hash-pinned Gold packages."""

from __future__ import annotations

import hashlib
import json
import math
from decimal import Decimal
from typing import TYPE_CHECKING, Any

import matplotlib as mpl
import PIL
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.ft2font import __freetype_version__
from matplotlib.ticker import FuncFormatter, MaxNLocator

from archive_govt_nz.domains.health_appropriations.gold_reader import read_verified_gold
from archive_govt_nz.domains.health_appropriations.plot_contracts import (
    build_plot_contracts,
)

if TYPE_CHECKING:
    from pathlib import Path

    from matplotlib.typing import RcKeyType

SCHEMA = "archive-govt-nz.health-source-plots/v1"
_COLORS = ("#2563eb", "#1d4ed8", "#60a5fa")
_MARKERS = ("o", "s", "^", "D", "P")
_HATCHES = ("", "//", "xx", "..", "++")
_MAX_POINTS = 10_000
_MAX_SERIES = 24
_STYLE: dict[RcKeyType, Any] = {
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "text.color": "#262626",
    "axes.labelcolor": "#262626",
    "axes.edgecolor": "#737373",
    "axes.spines.top": False,
    "axes.spines.right": False,
    "grid.color": "#dedede",
    "grid.linewidth": 0.6,
    "text.usetex": False,
    "text.parse_math": False,
}


def _label(context: dict[str, Any]) -> str:
    values = [
        str(context[key])
        for key in (
            "source_vintage",
            "amount_type",
            "accounting_basis",
            "period_end_month",
        )
        if key in context
    ]
    return " | ".join([*values, context["source_object_sha256"][:12]])


def _finite(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        message = "nonfinite_plot_value"
        raise ValueError(message)
    return result


def _draw(axis: Any, plot: dict[str, Any]) -> None:  # noqa: ANN401 - Matplotlib axes runtime interface
    series = plot["series"]
    categories = sorted({point["x"] for group in series for point in group["points"]})
    positions = {
        value: index if plot["kind"] == "barh" else value
        for index, value in enumerate(categories)
    }
    members: dict[Any, list[int]] = {}
    for index, group in enumerate(series):
        for point in group["points"]:
            members.setdefault(point["x"], []).append(index)
    for index, group in enumerate(series):
        x = [point["x"] for point in group["points"]]
        y = [_finite(point["y"]) for point in group["points"]]
        color = _COLORS[index % len(_COLORS)]
        label = _label(group["context"])
        if plot["kind"] == "line":
            axis.plot(
                x,
                y,
                color=color,
                marker=_MARKERS[index % len(_MARKERS)],
                markersize=4,
                linewidth=1.4,
                label=label,
            )
        else:
            widths = [0.8 / len(members[value]) for value in x]
            shifted = [
                positions[value]
                + (members[value].index(index) - (len(members[value]) - 1) / 2) * width
                for value, width in zip(x, widths, strict=True)
            ]
            options = {
                "color": ["white" if value < 0 else color for value in y],
                "edgecolor": "#1e3a8a",
                "linewidth": 1,
                "hatch": _HATCHES[index % len(_HATCHES)],
                "label": label,
            }
            if plot["kind"] == "barh":
                bars = axis.barh(shifted, y, height=widths, **options)
                axis.bar_label(
                    bars,
                    labels=[
                        format(Decimal(point["y"]), ",f") for point in group["points"]
                    ],
                    padding=5,
                    fontsize=9,
                )
            else:
                axis.bar(shifted, y, width=widths, **options)
    if plot["kind"] == "barh":
        axis.set_yticks(list(positions.values()), categories)
        axis.axvline(0, color="#525252", linewidth=0.8)
        axis.grid(axis="x")
        axis.margins(x=0.2)
    elif plot["kind"] == "bar":
        axis.xaxis.set_major_locator(MaxNLocator(nbins=10, integer=True))
        axis.axhline(0, color="#525252", linewidth=0.8)
        axis.grid(axis="y")
    else:
        axis.xaxis.set_major_locator(MaxNLocator(integer=True))
        axis.grid(axis="y")


def _checked_count(plot: dict[str, Any]) -> int:
    count = sum(len(group["points"]) for group in plot["series"])
    if count > _MAX_POINTS or len(plot["series"]) > _MAX_SERIES:
        message = "plot_resource_limit"
        raise ValueError(message)
    return count


def figure_for_contract(plot: dict[str, Any]) -> Figure:
    """Build an unregistered Agg figure; callers own saving/clearing it."""
    count = _checked_count(plot)
    with mpl.rc_context({**mpl.rcParamsDefault, **_STYLE}):
        figure = Figure(figsize=(14, 8), dpi=100)
        FigureCanvasAgg(figure)
        axis = figure.subplots()
        _draw(axis, plot)
        axis.set(title=plot["title"], xlabel=plot["xlabel"], ylabel=plot["ylabel"])
        axis.set_axisbelow(True)
        value_axis = axis.xaxis if plot["kind"] == "barh" else axis.yaxis
        value_axis.set_major_formatter(
            FuncFormatter(
                lambda value, _position: (
                    f"{value:,.1f}" if "%" in plot["ylabel"] else f"{value:,.0f}"
                )
            )
        )
        figure.subplots_adjust(
            left=0.30 if plot["kind"] == "barh" else 0.12,
            right=0.97,
            bottom=0.24,
            top=0.84,
        )
        figure.text(
            0.12,
            0.93,
            f"{count} plotted observations; {len(plot['omissions'])} unavailable "
            "comparisons omitted, not zero-filled",
            fontsize=10,
        )
        figure.text(
            0.12,
            0.90,
            "Source/vintage/period/basis partitions retained; period starts unverified",
            fontsize=9,
        )
        if not count:
            axis.text(
                0.5,
                0.5,
                "No eligible observations",
                transform=axis.transAxes,
                ha="center",
            )
        handles, labels = axis.get_legend_handles_labels()
        unique = dict(zip(labels, handles, strict=True))
        if unique:
            figure.legend(
                unique.values(),
                unique.keys(),
                loc="lower center",
                bbox_to_anchor=(0.5, 0.02),
                ncol=2,
                fontsize=8,
                frameon=False,
            )
        return figure


def _save_plot(plot: dict[str, Any], path: Path) -> None:
    figure = figure_for_contract(plot)
    try:
        with (
            mpl.rc_context({**mpl.rcParamsDefault, **_STYLE}),
            path.open("xb") as handle,
        ):
            figure.savefig(
                handle, format="png", dpi=100, metadata={"Software": "archive-govt-nz"}
            )
    finally:
        figure.clear()


def _write_json(path: Path, value: object) -> None:
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(
            json.dumps(
                value, sort_keys=True, ensure_ascii=False, allow_nan=False, indent=2
            )
            + "\n"
        )


def _export(gold: Path, pin: str, output: Path, *, dry_run: bool) -> dict[str, Any]:
    if (
        output.is_symlink()
        or output.resolve().is_relative_to(gold.resolve())
        or output.exists()
    ):
        message = "existing_or_input_overlapping_plot_output"
        raise ValueError(message)
    tables, parent = read_verified_gold(gold, pin)
    contracts = build_plot_contracts(tables)
    receipt = {
        "schema_version": SCHEMA,
        "status": "planned" if dry_run else "passed",
        "gold_manifest_sha256": pin,
        "raw_manifest_sha256": parent["raw_manifest_sha256"],
        "publication_state": "local_validation_only",
        "renderer": {
            "matplotlib": mpl.__version__,
            "pillow": PIL.__version__,
            "freetype": __freetype_version__,
            "backend": "Agg",
        },
        "point_counts": {
            name: _checked_count(plot) for name, plot in contracts.items()
        },
        "omission_counts": {
            name: len(plot["omissions"]) for name, plot in contracts.items()
        },
    }
    if dry_run:
        return receipt
    output.mkdir(parents=True, exist_ok=False)
    try:
        _write_json(output / "CONTRACTS.json", contracts)
        for name, plot in contracts.items():
            _save_plot(plot, output / name)
        receipt["output_sha256"] = {
            name: hashlib.sha256((output / name).read_bytes()).hexdigest()
            for name in (*contracts, "CONTRACTS.json")
        }
        _write_json(output / "MANIFEST.json", receipt)
    except Exception as error:
        _write_json(
            output / "FAILURE.json",
            {
                "schema_version": SCHEMA,
                "status": "failed",
                "error_class": type(error).__name__,
            },
        )
        raise
    return receipt


def render_plots(
    gold: Path, pin: str, output: Path, *, dry_run: bool = True
) -> dict[str, Any]:
    """Preflight or render new local plots without overwriting inputs or publishing."""
    try:
        return _export(gold, pin, output, dry_run=dry_run)
    except Exception as error:  # noqa: BLE001 - public protocol redaction boundary
        message = "plot_export_failed:" + type(error).__name__
        raise ValueError(message) from None
