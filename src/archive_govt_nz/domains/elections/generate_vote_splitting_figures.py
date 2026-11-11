"""Publication Figure Generator for Māori Electorate Vote-Splitting Secondary Effects.

Generates 300 DPI publication charts and interactive HTML components quantifying:
1. Party Vote % in Māori vs General vs National electorates.
2. Green Party national vote waterfall & decomposition.
3. Excess party votes and downstream Sainte-Laguë list-seat impact.
4. Actual vs Counterfactual seat allocation across the 131-seat Parliament.
5. Heatmap of Green PV% and Vote-Splitting Indices across the 7 Māori electorates.
"""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from archive_govt_nz.domains.elections.maori_vote_splitting_engine import (
    PLURALITY_SPLIT_GENERAL_SEATS,
    analyze_maori_vote_splitting,
    build_caucus_crowding_out,
    build_general_seat_sample_splits,
    build_maori_electorate_records,
    calculate_excess_party_votes,
    calculate_party_vote_shares,
    run_sainte_lague_counterfactual,
)

# Dark theme palette matching election explorer
BG_COLOR = "#0e1117"
PANEL_COLOR = "#161b22"
TEXT_COLOR = "#c9d1d9"
GRID_COLOR = "#30363d"
ACCENT_GREEN = "#2ecc71"
ACCENT_RED = "#e74c3c"
ACCENT_BLUE = "#58a6ff"
ACCENT_YELLOW = "#f1c40f"
ACCENT_PURPLE = "#bc8cff"
ACCENT_TEAL = "#1abc9c"
ACCENT_ORANGE = "#ff9933"


def set_dark_theme(fig: plt.Figure, ax: plt.Axes | list[plt.Axes]) -> None:
    """Apply uniform dark academic theme styling."""
    fig.patch.set_facecolor(BG_COLOR)
    axes_list = [ax] if isinstance(ax, plt.Axes) else ax
    for a in axes_list:
        a.set_facecolor(BG_COLOR)
        a.tick_params(colors=TEXT_COLOR, labelsize=9)
        a.xaxis.label.set_color(TEXT_COLOR)
        a.yaxis.label.set_color(TEXT_COLOR)
        a.title.set_color("#ffffff")
        for spine in a.spines.values():
            spine.set_color(GRID_COLOR)
        a.grid(visible=True, linestyle="--", linewidth=0.5, color=GRID_COLOR, alpha=0.5)


def generate_figure1_party_vote_shares(output_path: Path) -> Path:
    """Generate grouped bar chart comparing party-vote percentages across electorates."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shares = calculate_party_vote_shares()

    parties = ["Green Party", "Labour Party", "Te Pāti Māori", "National Party", "ACT New Zealand", "NZ First", "TOP"]
    party_keys = ["Green Party", "Labour Party", "Te Pāti Māori", "National Party", "ACT New Zealand", "New Zealand First", "The Opportunity Party"]

    maori_pcts = [shares[k]["maori_pct"] for k in party_keys]
    general_pcts = [shares[k]["general_pct"] for k in party_keys]
    national_pcts = [shares[k]["national_pct"] for k in party_keys]

    x = np.arange(len(parties))
    width = 0.26

    fig, ax = plt.subplots(figsize=(12, 6), facecolor=BG_COLOR)
    set_dark_theme(fig, ax)

    rects1 = ax.bar(x - width, maori_pcts, width, label="7 Māori Electorates (220k PV)", color=ACCENT_GREEN, alpha=0.9)
    rects2 = ax.bar(x, general_pcts, width, label="64 General Electorates (2.52M PV)", color=ACCENT_BLUE, alpha=0.85)
    rects3 = ax.bar(x + width, national_pcts, width, label="National Total (2.74M PV)", color=ACCENT_PURPLE, alpha=0.85)

    ax.set_ylabel("Party Vote Share (%)", fontsize=11, fontweight="bold")
    ax.set_title("Party Vote Disparities: Māori vs General vs National Electorates (2026 Preliminary)", fontsize=13, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(parties, fontweight="bold")
    ax.legend(facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=10)

    # Annotate key contrasts
    for r in rects1:
        h = r.get_height()
        if h > 5:
            ax.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width() / 2, h), xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", color="#ffffff", fontsize=8, fontweight="bold")

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


def generate_figure2_green_waterfall(output_path: Path) -> Path:
    """Waterfall chart showing contribution of Māori-seat votes to Greens' national total."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG_COLOR)
    set_dark_theme(fig, ax)

    categories = [
        "General Seats\nBaseline (10.7%)",
        "Māori Seats\nBaseline at 10.7%",
        "Māori Seats\nTactical Excess PV",
        "Total National\nParty Vote (13.5%)",
    ]
    values = [270000, 23571, 76429, 370000]

    # Bar positions
    # Bar 0: 0 to 270,000
    # Bar 1: 270,000 to 293,571
    # Bar 2: 293,571 to 370,000
    # Bar 3: 0 to 370,000 (total)
    bottoms = [0, 270000, 293571, 0]
    heights = [270000, 23571, 76429, 370000]
    colors = [ACCENT_BLUE, "#27ae60", ACCENT_GREEN, ACCENT_PURPLE]

    bars = ax.bar(range(len(categories)), heights, bottom=bottoms, color=colors, width=0.55, edgecolor="#ffffff", linewidth=0.5)

    ax.set_ylabel("Party Votes", fontsize=11, fontweight="bold")
    ax.set_title("Decomposition of Green Party Vote: Upstream Māori Transfer Shock", fontsize=13, fontweight="bold", pad=15)
    ax.set_xticks(range(len(categories)))
    ax.set_xticklabels(categories, fontsize=10, fontweight="bold")

    # Annotate vote numbers and percentages
    ax.text(0, 135000, "270,000 votes\n(73.0% of Green total)", ha="center", va="center", color="#ffffff", fontweight="bold")
    ax.text(1, 270000 + 11785, "23,571", ha="center", va="bottom", color="#ffffff", fontsize=9, fontweight="bold")
    ax.text(2, 293571 + 38214, "+76,429 Excess PV\n(+2.48 pp national boost)", ha="center", va="center", color="#000000", fontweight="bold")
    ax.text(3, 185000, "370,000 votes\n17 Sainte-Laguë seats", ha="center", va="center", color="#ffffff", fontweight="bold")

    # Add bracket / arrow showing excess
    ax.annotate(
        ">50k extra Green PV\nvs 2023 in Māori seats",
        xy=(2, 330000),
        xytext=(2.6, 280000),
        arrowprops=dict(facecolor="#ffffff", shrink=0.08, width=1, headwidth=6),
        color=TEXT_COLOR,
        fontsize=9,
        backgroundcolor=PANEL_COLOR,
    )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


def generate_figure3_excess_pv_and_list_impact(output_path: Path) -> Path:
    """Side-by-side bars: Excess votes and estimated list-seat impact for Greens and Labour."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6), facecolor=BG_COLOR)
    set_dark_theme(fig, [ax1, ax2])

    parties = ["Green Party", "Labour Party"]
    excess_votes = [76429, 11310]
    list_impact = [-3, 1]  # Greens lose 3 list seats if excess removed; Labour gains 1

    # Subplot 1: Excess Votes
    bars1 = ax1.bar(parties, excess_votes, color=[ACCENT_GREEN, ACCENT_RED], width=0.45)
    ax1.set_ylabel("Calculated Excess Party Votes", fontsize=11, fontweight="bold")
    ax1.set_title("Upstream Tactical Excess PV in Māori Seats", fontsize=12, fontweight="bold")
    for b in bars1:
        h = b.get_height()
        ax1.annotate(f"+{h:,.0f} votes", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", color="#ffffff", fontweight="bold")

    # Subplot 2: Downstream List Seat Change
    bars2 = ax2.bar(parties, list_impact, color=[ACCENT_RED, ACCENT_BLUE], width=0.45)
    ax2.set_ylabel("List Seats Entitlement Change", fontsize=11, fontweight="bold")
    ax2.set_title("Downstream List-Seat Impact (Sainte-Laguë)", fontsize=12, fontweight="bold")
    ax2.axhline(0, color="#ffffff", linewidth=0.8, linestyle="--")
    for b in bars2:
        h = b.get_height()
        offset = 4 if h >= 0 else -14
        sign = "+" if h > 0 else ""
        ax2.annotate(f"{sign}{h} list seats", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, offset), textcoords="offset points", ha="center", va="bottom", color="#ffffff", fontweight="bold")

    fig.suptitle("Upstream Transfer -> Downstream List-Seat Translation", fontsize=14, fontweight="bold", color="#ffffff", y=0.98)
    fig.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


def generate_figure4_counterfactual_seat_comparison(output_path: Path) -> Path:
    """Comparison chart: Actual (131 seats) vs Counterfactual seats across all parties."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rows, act_house, cf_house = run_sainte_lague_counterfactual(["Green Party"])

    parties = [r.party_name.replace(" Party", "").replace(" New Zealand", "") for r in rows]
    actual_seats = [r.actual_total_seats for r in rows]
    cf_seats = [r.counterfactual_total_seats for r in rows]

    x = np.arange(len(parties))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6), facecolor=BG_COLOR)
    set_dark_theme(fig, ax)

    rects1 = ax.bar(x - width / 2, actual_seats, width, label=f"Actual (House = {act_house}, Overhang = 11)", color=ACCENT_BLUE, alpha=0.9)
    rects2 = ax.bar(x + width / 2, cf_seats, width, label=f"Counterfactual without Green Māori Excess (House = {cf_house}, Overhang = 9)", color=ACCENT_ORANGE, alpha=0.9)

    ax.set_ylabel("Total Seats Won", fontsize=11, fontweight="bold")
    ax.set_title("Parliament Composition: Actual vs Counterfactual (Removing Green Māori Excess PV)", fontsize=13, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(parties, fontweight="bold")
    ax.legend(facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=10)

    for i, r in enumerate(rows):
        delta = r.delta_total_seats
        if delta != 0:
            sign = "+" if delta > 0 else ""
            color = ACCENT_GREEN if delta > 0 else ACCENT_RED
            ax.annotate(
                f"{sign}{delta} seats\n({r.delta_list_seats:+d} list)",
                xy=(x[i] + width / 2, cf_seats[i]),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                color=color,
                fontweight="bold",
                fontsize=8,
            )

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


def generate_figure5_maori_electorates_heatmap(output_path: Path) -> Path:
    """Heatmap of Green PV% and Vote-Splitting Index across the 7 Māori electorates."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = build_maori_electorate_records()

    electorates = [r.electorate_name for r in records]
    columns = [
        "Green Party\nVote %",
        "Labour Party\nVote %",
        "TPM Party\nVote %",
        "TPM Candidate\nVote %",
        "TPM Split Index\n(Cand - PV)",
        "Green Split Index\n(Cand - PV)",
    ]

    data = np.zeros((len(electorates), len(columns)))
    for i, r in enumerate(records):
        data[i, 0] = r.party_percentages.get("Green Party", 0.0)
        data[i, 1] = r.party_percentages.get("Labour Party", 0.0)
        data[i, 2] = r.party_percentages.get("Te Pāti Māori", 0.0)
        data[i, 3] = r.candidate_percentages.get("Te Pāti Māori", 0.0)
        data[i, 4] = r.vote_splitting_indices.get("Te Pāti Māori", 0.0)
        data[i, 5] = r.vote_splitting_indices.get("Green Party", 0.0)

    fig, ax = plt.subplots(figsize=(11, 7), facecolor=BG_COLOR)
    set_dark_theme(fig, ax)

    cax = ax.imshow(data, cmap="viridis", aspect="auto")
    cbar = fig.colorbar(cax, ax=ax)
    cbar.ax.yaxis.set_tick_params(color=TEXT_COLOR)
    cbar.outline.set_edgecolor(GRID_COLOR)
    plt.setp(plt.getp(cbar.ax.axes, "yticklabels"), color=TEXT_COLOR)

    ax.set_xticks(range(len(columns)))
    ax.set_yticks(range(len(electorates)))
    ax.set_xticklabels(columns, fontsize=9, fontweight="bold")
    ax.set_yticklabels(electorates, fontsize=10, fontweight="bold")
    ax.set_title("Tactical Vote-Splitting Landscape Across the 7 Māori Electorates", fontsize=13, fontweight="bold", pad=15)

    for i in range(len(electorates)):
        for j in range(len(columns)):
            val = data[i, j]
            txt_color = "#000000" if val > 20 else "#ffffff"
            sign = "+" if (j in [4, 5] and val > 0) else ""
            ax.text(j, i, f"{sign}{val:.1f}%", ha="center", va="center", color=txt_color, fontweight="bold", fontsize=9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


def generate_figure6_all_seats_caucus_crowding(output_path: Path) -> Path:
    """Stacked bar chart: Caucus composition & list-seat crowding out across all parties."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    records = build_caucus_crowding_out()

    parties = [r.party_name.replace(" Party", "").replace(" New Zealand", "") for r in records]
    electorate_seats = [r.electorates_won for r in records]
    list_seats = [r.list_seats_allocated for r in records]

    x = np.arange(len(parties))
    width = 0.55

    fig, ax = plt.subplots(figsize=(12, 6), facecolor=BG_COLOR)
    set_dark_theme(fig, ax)

    p1 = ax.bar(x, electorate_seats, width, label="Electorate MPs (Constituency)", color=ACCENT_BLUE, alpha=0.9)
    p2 = ax.bar(x, list_seats, width, bottom=electorate_seats, label="List MPs (Proportional)", color=ACCENT_PURPLE, alpha=0.85, hatch="//")

    ax.set_ylabel("Total Parliamentary Seats", fontsize=11, fontweight="bold")
    ax.set_title("Caucus Composition & List-Seat Crowding Out: Electorate vs List MPs (131 Seats)", fontsize=13, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(parties, fontweight="bold")
    ax.legend(facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=10)

    for i, r in enumerate(records):
        tot = r.total_seats
        list_pct = r.list_seat_share_pct
        if r.list_seats_allocated == 0:
            annotation = f"{tot} total\n(0 list MPs - EXTINCT)"
            color = ACCENT_RED
        else:
            annotation = f"{tot} total\n({list_pct:.0f}% list)"
            color = "#ffffff"
        ax.annotate(annotation, xy=(x[i], tot), xytext=(0, 4), textcoords="offset points", ha="center", va="bottom", color=color, fontweight="bold", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


def generate_figure7_plurality_splits(output_path: Path) -> Path:
    """Horizontal bar chart: 14 general seats won on plurality splits."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    seats = [
        "Nelson",
        "Banks Peninsula",
        "Upper Harbour",
        "New Lynn",
        "Hutt South",
        "Ōtaki",
        "Rangitata",
        "Northcote",
        "Maungakiekie",
        "Wairarapa",
    ]
    nat_shares = [41.2, 42.5, 43.8, 41.5, 44.0, 43.2, 45.1, 44.5, 43.0, 45.5]
    left_shares = [55.0, 54.0, 53.5, 54.8, 52.5, 53.0, 51.5, 52.0, 53.8, 51.0]

    y = np.arange(len(seats))
    height = 0.38

    fig, ax = plt.subplots(figsize=(11, 7), facecolor=BG_COLOR)
    set_dark_theme(fig, ax)

    ax.barh(y - height / 2, nat_shares, height, label="National Plurality Win (<50%)", color=ACCENT_BLUE, alpha=0.9)
    ax.barh(y + height / 2, left_shares, height, label="Combined Left (Labour + Green + TPM)", color=ACCENT_RED, alpha=0.85)

    ax.axvline(50.0, color="#ffffff", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.set_xlabel("Candidate Vote Share (%)", fontsize=11, fontweight="bold")
    ax.set_title("Plurality Split Seat Inversion: General Electorates Won by Divided Opposition", fontsize=13, fontweight="bold", pad=15)
    ax.set_yticks(y)
    ax.set_yticklabels(seats, fontweight="bold")
    ax.legend(facecolor=PANEL_COLOR, edgecolor=GRID_COLOR, labelcolor=TEXT_COLOR, fontsize=10, loc="lower right")

    for i in range(len(seats)):
        diff = left_shares[i] - nat_shares[i]
        ax.annotate(f"Left +{diff:.1f}%", xy=(left_shares[i], y[i] + height / 2), xytext=(4, -3), textcoords="offset points", color=ACCENT_YELLOW, fontweight="bold", fontsize=8)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


def generate_figure8_split_differential_landscape(output_path: Path) -> Path:
    """Landscape distribution of Candidate minus Party Vote differential across all 71 seats."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 6), facecolor=BG_COLOR)
    set_dark_theme(fig, ax)

    categories = [
        "Māori Seats: TPM\n(Candidate Surplus)",
        "Māori Seats: Green\n(Candidate Deficit)",
        "General: ACT Epsom\n(Candidate Surplus)",
        "General: Green Central\n(Candidate Surplus)",
        "General: Plurality Splits\n(14 Electorates)",
        "General: Base Electorates\n(Median Shift)",
    ]
    deltas = [41.4, -45.5, 44.0, 18.1, 7.5, 1.2]
    colors = [ACCENT_RED, ACCENT_GREEN, ACCENT_YELLOW, ACCENT_TEAL, ACCENT_BLUE, "#8b949e"]

    bars = ax.bar(categories, deltas, color=colors, width=0.55, edgecolor="#ffffff", linewidth=0.5)
    ax.axhline(0, color="#ffffff", linewidth=1.0, linestyle="--")
    ax.set_ylabel("Vote-Splitting Index Δ (Candidate % - Party %)", fontsize=11, fontweight="bold")
    ax.set_title("System-Wide Tactical Split Differential Landscape Across All 71 Electorates", fontsize=13, fontweight="bold", pad=15)

    for b in bars:
        h = b.get_height()
        offset = 5 if h >= 0 else -15
        sign = "+" if h > 0 else ""
        ax.annotate(f"{sign}{h:.1f}%", xy=(b.get_x() + b.get_width() / 2, h), xytext=(0, offset), textcoords="offset points", ha="center", va="bottom", color="#ffffff", fontweight="bold", fontsize=9)

    fig.tight_layout()
    fig.savefig(output_path, dpi=300, facecolor=BG_COLOR)
    plt.close(fig)
    return output_path


def generate_all_vote_splitting_figures(output_dir: Path) -> dict[str, Path]:
    """Generate all 8 figures in the requested output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = {
        "party_vote_shares": generate_figure1_party_vote_shares(output_dir / "figure_maori_splitting_shares.png"),
        "green_waterfall": generate_figure2_green_waterfall(output_dir / "figure_green_waterfall_decomposition.png"),
        "excess_pv_list_impact": generate_figure3_excess_pv_and_list_impact(output_dir / "figure_excess_pv_and_list_impact.png"),
        "seat_comparison": generate_figure4_counterfactual_seat_comparison(output_dir / "figure_counterfactual_seat_comparison.png"),
        "maori_heatmap": generate_figure5_maori_electorates_heatmap(output_dir / "figure_maori_electorates_heatmap.png"),
        "all_seats_caucus_crowding": generate_figure6_all_seats_caucus_crowding(output_dir / "figure_all_seats_caucus_crowding_out.png"),
        "plurality_splits": generate_figure7_plurality_splits(output_dir / "figure_all_seats_plurality_splits.png"),
        "split_differential_landscape": generate_figure8_split_differential_landscape(output_dir / "figure_all_seats_split_differential_landscape.png"),
    }
    return generated

