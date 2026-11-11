"""Generate geographic electorate maps and longitudinal animations for NZ elections."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np


def generate_electorate_geographic_map(output_path: Path) -> Path:
    """Generate high-resolution geographic map showing electorate outcomes and overhang hotspots."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 14), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")

    # Schematic stylized New Zealand North and South Island boundary polygons
    # North Island
    ni_x = [174.0, 174.5, 175.2, 176.0, 178.5, 177.0, 175.0, 174.8, 173.0, 173.2, 174.0]
    ni_y = [-41.3, -40.5, -39.0, -37.5, -37.5, -39.5, -41.0, -41.3, -35.0, -34.5, -36.5]

    # South Island
    si_x = [174.0, 173.5, 171.0, 168.0, 166.5, 168.5, 171.0, 173.0, 174.2, 174.0]
    si_y = [-41.3, -42.0, -43.5, -46.5, -46.0, -44.0, -43.0, -41.5, -41.0, -41.3]

    ax.plot(ni_x, ni_y, color="#30363d", linewidth=1.5)
    ax.fill(ni_x, ni_y, color="#161b22", alpha=0.8)

    ax.plot(si_x, si_y, color="#30363d", linewidth=1.5)
    ax.fill(si_x, si_y, color="#161b22", alpha=0.8)

    # Key Electorate Nodes (Coordinates and party color)
    # National = #00529F, Labour = #D82A20, Greens = #098137, ACT = #FDE401, TPM = #800020
    electorates = [
        # North Island
        {
            "name": "Northland",
            "x": 173.8,
            "y": -35.5,
            "party": "National",
            "color": "#00529F",
            "seats": "General",
        },
        {
            "name": "Auckland Central",
            "x": 174.76,
            "y": -36.85,
            "party": "Green",
            "color": "#098137",
            "seats": "General",
        },
        {
            "name": "Epsom",
            "x": 174.77,
            "y": -36.89,
            "party": "ACT",
            "color": "#FDE401",
            "seats": "General",
        },
        {
            "name": "Te Atatū (Knife-Edge)",
            "x": 174.65,
            "y": -36.84,
            "party": "Labour",
            "color": "#D82A20",
            "seats": "General",
            "flag": True,
        },
        {
            "name": "Mount Albert",
            "x": 174.72,
            "y": -36.88,
            "party": "Labour",
            "color": "#D82A20",
            "seats": "General",
        },
        {
            "name": "Hauraki-Waikato",
            "x": 175.2,
            "y": -37.8,
            "party": "Te Pāti Māori",
            "color": "#800020",
            "seats": "Māori",
            "flag": True,
        },
        {
            "name": "Waikato",
            "x": 175.5,
            "y": -37.6,
            "party": "National",
            "color": "#00529F",
            "seats": "General",
        },
        {
            "name": "Bay of Plenty",
            "x": 176.3,
            "y": -37.8,
            "party": "National",
            "color": "#00529F",
            "seats": "General",
        },
        {
            "name": "East Coast",
            "x": 177.8,
            "y": -38.2,
            "party": "National",
            "color": "#00529F",
            "seats": "General",
        },
        {
            "name": "New Plymouth",
            "x": 174.1,
            "y": -39.1,
            "party": "National",
            "color": "#00529F",
            "seats": "General",
        },
        {
            "name": "Palmerston North",
            "x": 175.6,
            "y": -40.3,
            "party": "Labour",
            "color": "#D82A20",
            "seats": "General",
        },
        {
            "name": "Wellington Central",
            "x": 174.77,
            "y": -41.28,
            "party": "Green",
            "color": "#098137",
            "seats": "General",
        },
        {
            "name": "Rongotai",
            "x": 174.80,
            "y": -41.32,
            "party": "Green",
            "color": "#098137",
            "seats": "General",
        },
        {
            "name": "Remutaka",
            "x": 175.05,
            "y": -41.15,
            "party": "Labour",
            "color": "#D82A20",
            "seats": "General",
        },
        # South Island
        {
            "name": "Nelson (Knife-Edge)",
            "x": 173.28,
            "y": -41.27,
            "party": "National",
            "color": "#00529F",
            "seats": "General",
            "flag": True,
        },
        {
            "name": "West Coast-Tasman",
            "x": 172.0,
            "y": -42.2,
            "party": "National",
            "color": "#00529F",
            "seats": "General",
        },
        {
            "name": "Banks Peninsula (Knife-Edge)",
            "x": 172.7,
            "y": -43.6,
            "party": "National",
            "color": "#00529F",
            "seats": "General",
            "flag": True,
        },
        {
            "name": "Christchurch Central",
            "x": 172.64,
            "y": -43.53,
            "party": "Labour",
            "color": "#D82A20",
            "seats": "General",
        },
        {
            "name": "Waitaki",
            "x": 170.5,
            "y": -44.8,
            "party": "National",
            "color": "#00529F",
            "seats": "General",
        },
        {
            "name": "Dunedin",
            "x": 170.5,
            "y": -45.87,
            "party": "Labour",
            "color": "#D82A20",
            "seats": "General",
        },
        {
            "name": "Southland",
            "x": 168.2,
            "y": -45.8,
            "party": "National",
            "color": "#00529F",
            "seats": "General",
        },
        {
            "name": "Te Tai Tonga",
            "x": 171.5,
            "y": -43.0,
            "party": "Te Pāti Māori",
            "color": "#800020",
            "seats": "Māori",
        },
    ]

    for e in electorates:
        is_knife = e.get("flag", False)
        size = 180 if is_knife else 90
        edge = "#f85149" if is_knife else "#ffffff"
        linewidth = 2.5 if is_knife else 0.8

        ax.scatter(
            e["x"],
            e["y"],
            s=size,
            color=e["color"],
            edgecolors=edge,
            linewidths=linewidth,
            zorder=5,
        )

        # Labels
        offset_x = 0.25
        offset_y = 0.1
        weight = "bold" if is_knife else "normal"
        color = "#ff7b72" if is_knife else "#c9d1d9"
        ax.text(
            e["x"] + offset_x,
            e["y"] + offset_y,
            e["name"],
            fontsize=9,
            weight=weight,
            color=color,
            zorder=6,
        )

    # Title and Legend
    ax.set_title(
        "New Zealand 2026 Provisional Electorate Map\nOverhang Hotspots & Knife-Edge Seats",
        fontsize=15,
        color="#ffffff",
        weight="bold",
        pad=20,
    )
    ax.axis("off")

    # Custom legend
    legend_elements = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="National Party (43)",
            markerfacecolor="#00529F",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Labour Party (16)",
            markerfacecolor="#D82A20",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Te Pāti Māori (9)",
            markerfacecolor="#800020",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Green Party (3)",
            markerfacecolor="#098137",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="ACT New Zealand (1)",
            markerfacecolor="#FDE401",
            markersize=10,
        ),
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Knife-Edge Contest (< 250 margin)",
            markerfacecolor="none",
            markeredgecolor="#f85149",
            markeredgewidth=2,
            markersize=12,
        ),
    ]
    ax.legend(
        handles=legend_elements,
        loc="lower left",
        facecolor="#161b22",
        edgecolor="#30363d",
        labelcolor="#c9d1d9",
        fontsize=9,
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    return output_path


def generate_longitudinal_overhang_timeline(output_path: Path) -> Path:
    """Generate longitudinal chart showing overhang seats and expanded House sizes across 1996-2026."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    years = [1996, 1999, 2002, 2005, 2008, 2011, 2014, 2017, 2020, 2023, 2026]
    base_seats = [120] * len(years)
    overhangs = [0, 0, 0, 1, 2, 1, 1, 0, 0, 3, 11]
    house_sizes = [b + o for b, o in zip(base_seats, overhangs, strict=False)]

    fig, ax = plt.subplots(figsize=(12, 6), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")

    # Bar chart
    x = np.arange(len(years))
    width = 0.55

    ax.bar(
        x,
        base_seats,
        width,
        label="Statutory Nominal Baseline (120)",
        color="#21262d",
        edgecolor="#30363d",
    )
    ax.bar(
        x,
        overhangs,
        width,
        bottom=base_seats,
        label="Uncompensated Overhang Seats",
        color="#f85149",
        edgecolor="#da3633",
    )

    ax.set_ylabel("Total Seats in Parliament", color="#c9d1d9", fontsize=12)
    ax.set_title(
        "Longitudinal Evolution of Overhang Seats in New Zealand MMP (1996-2026)",
        color="#ffffff",
        fontsize=14,
        weight="bold",
        pad=15,
    )
    ax.set_xticks(x)
    ax.set_xticklabels([str(year) for year in years], color="#c9d1d9", fontsize=11)
    ax.set_ylim(100, 136)
    ax.tick_params(colors="#8b949e")
    ax.grid(axis="y", color="#30363d", linestyle="--", alpha=0.5)

    # Value callouts on top of bars
    for i, (size, ov) in enumerate(zip(house_sizes, overhangs, strict=False)):
        label = f"{size}" if ov == 0 else f"{size}\n(+{ov})"
        color = "#ffffff" if ov == 0 else "#ff7b72"
        ax.text(
            i,
            size + 1.0,
            label,
            ha="center",
            va="bottom",
            fontsize=10,
            weight="bold",
            color=color,
        )

    ax.legend(
        facecolor="#161b22",
        edgecolor="#30363d",
        labelcolor="#c9d1d9",
        fontsize=10,
        loc="upper left",
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    return output_path


if __name__ == "__main__":
    import sys

    p1 = Path("figures/electorate_map_2026.png")
    p2 = Path("figures/overhang_expansion_timeline.png")
    generate_electorate_geographic_map(p1)
    generate_longitudinal_overhang_timeline(p2)
    sys.stdout.write(f"Generated maps: {p1} and {p2}\n")
