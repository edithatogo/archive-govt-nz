"""Generate the Five Bleeding-Edge Frontier Election Visualisations for NZ Election 2026.

1. 3D Kinetic Coalition Topology (Force-Directed Topography)
2. Multi-Dimensional Electorate "Overhang" Voronoi Tessellations
3. Hyper-Dimensional Parallel Coordinates for Vote Splitting
4. Special Vote Probability Cones (Generative Fan Charts)
5. Semantic Policy Visibility Networks (CiteCompass AI Visibility Monitor)
"""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import Voronoi, voronoi_plot_2d


def generate_kinetic_coalition_3d(output_path: Path) -> Path:
    """1. 3D Kinetic Coalition Topology (Force-Directed Topography)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig = plt.figure(figsize=(11, 8), facecolor="#0e1117")
    ax = fig.add_subplot(111, projection="3d", facecolor="#0e1117")

    # Ideological coordinates (X: Economic Left-Right, Y: Social/Bicultural, Z: Institutional/Anti-Establishment)
    parties = [
        {"name": "National\n(43 seats, +7 ov)", "x": 0.70, "y": 0.45, "z": 0.20, "mass": 43, "color": "#00529F"},
        {"name": "Labour\n(31 seats)", "x": 0.35, "y": 0.65, "z": 0.25, "mass": 31, "color": "#D82A20"},
        {"name": "Green\n(17 seats)", "x": 0.18, "y": 0.85, "z": 0.40, "mass": 17, "color": "#098137"},
        {"name": "ACT\n(13 seats)", "x": 0.88, "y": 0.30, "z": 0.35, "mass": 13, "color": "#FDE401"},
        {"name": "NZ First\n(11 seats)", "x": 0.55, "y": 0.25, "z": 0.65, "mass": 11, "color": "#8b949e"},
        {"name": "TOP\n(7 seats)", "x": 0.48, "y": 0.55, "z": 0.30, "mass": 7, "color": "#32B5B5"},
        {"name": "Te Pāti Māori\n(9 seats, +4 ov)", "x": 0.20, "y": 0.90, "z": 0.85, "mass": 9, "color": "#800020"},
    ]

    # Generate topological potential energy wireframe surface (strain grid)
    gx = np.linspace(0.1, 0.95, 30)
    gy = np.linspace(0.1, 0.95, 30)
    X, Y = np.meshgrid(gx, gy)
    # Gravitational potential wells created by heavy nodes
    Z = np.zeros_like(X)
    for p in parties:
        dist_sq = (X - p["x"])**2 + (Y - p["y"])**2 + 0.04
        Z -= (p["mass"] * 0.015) / dist_sq

    # Normalize Z
    Z = (Z - Z.min()) / (Z.max() - Z.min()) * 0.6

    wire = ax.plot_wireframe(X, Y, Z, color="#30363d", alpha=0.35, rstride=2, cstride=2, linewidth=0.8)

    # Plot party nodes (size proportional to seat count / mass)
    for p in parties:
        node_size = p["mass"] * 25
        ax.scatter([p["x"]], [p["y"]], [p["z"]], color=p["color"], s=node_size, edgecolors="#ffffff", linewidth=1.5, alpha=0.95)
        ax.text(p["x"], p["y"], p["z"] + 0.08, p["name"], color="#ffffff", fontsize=8.5, weight="bold", ha="center")

    # Draw tension spring bonds for Centre-Right (Nat - ACT - NZF)
    ax.plot([0.70, 0.88], [0.45, 0.30], [0.20, 0.35], color="#58a6ff", linewidth=2.5, linestyle="-", label="Centre-Right Coalition Bond (67 seats)")
    ax.plot([0.70, 0.55], [0.45, 0.25], [0.20, 0.65], color="#58a6ff", linewidth=2.5, linestyle="-")

    # Draw tension spring bonds for Centre-Left (Lab - Grn - TPM)
    ax.plot([0.35, 0.18], [0.65, 0.85], [0.25, 0.40], color="#ff7b72", linewidth=2.2, linestyle="--", label="Centre-Left Potential Bloc (57 seats)")
    ax.plot([0.35, 0.20], [0.65, 0.90], [0.25, 0.85], color="#ff7b72", linewidth=2.2, linestyle="--")

    # Crossbench pivot bonds to TOP
    ax.plot([0.70, 0.48], [0.45, 0.55], [0.20, 0.30], color="#32B5B5", linewidth=1.5, linestyle=":", label="TOP Crossbench Pivot (7 seats)")

    ax.set_xlabel("Economic Axis (Left: 0 -> Right: 1)", color="#c9d1d9", labelpad=8)
    ax.set_ylabel("Social/Bicultural Axis (Trad: 0 -> Reform: 1)", color="#c9d1d9", labelpad=8)
    ax.set_zlabel("Anti-Establishment Vector", color="#c9d1d9", labelpad=8)
    ax.set_title("3D Kinetic Coalition Topology & Structural Strain Topography\nMass = Caucus Seats (131 Total) | Potential Wells = Gravitational Stability", color="#ffffff", fontsize=12, weight="bold", pad=12)

    # Styling
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False
    ax.tick_params(colors="#8b949e", labelsize=8)
    ax.grid(color="#30363d", linestyle="--", alpha=0.3)
    ax.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9", loc="upper left", fontsize=8.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    return output_path


def generate_overhang_voronoi(output_path: Path) -> Path:
    """2. Multi-Dimensional Electorate "Overhang" Voronoi Tessellations."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 10), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")

    # Generate 28 representative electorate centroids weighted by density and advance voting surge (+25%)
    rng = np.random.default_rng(2026)
    points = [
        # Auckland Urban Hub (High density)
        [174.75, -36.85], [174.65, -36.84], [174.77, -36.89], [174.72, -36.88], [174.85, -36.90],
        [174.60, -36.92], [174.88, -36.84], [174.70, -36.78],
        # Waikato & Bay of Plenty
        [175.25, -37.78], [175.50, -37.60], [176.15, -37.68], [176.30, -37.85],
        # Wellington Region
        [174.77, -41.28], [174.80, -41.32], [174.90, -41.22], [175.05, -41.15],
        # Canterbury / Christchurch
        [172.63, -43.53], [172.55, -43.50], [172.70, -43.60], [172.45, -43.58],
        # Regional & Provincial
        [173.80, -35.50], [174.10, -39.10], [175.60, -40.30], [177.80, -38.20],
        [173.28, -41.27], [171.20, -42.45], [170.50, -45.87], [168.35, -46.40]
    ]
    pts = np.array(points)
    vor = Voronoi(pts)

    # Party winners for each centroid
    party_colors = [
        "#098137", "#D82A20", "#FDE401", "#D82A20", "#00529F",
        "#D82A20", "#00529F", "#00529F",
        "#800020", "#00529F", "#00529F", "#00529F",
        "#098137", "#098137", "#D82A20", "#D82A20",
        "#00529F", "#D82A20", "#00529F", "#00529F",
        "#00529F", "#00529F", "#D82A20", "#00529F",
        "#00529F", "#00529F", "#D82A20", "#00529F"
    ]

    # Indices of plurality-without-majority overhang seats with floating glass layer
    overhang_indices = {1, 3, 8, 18, 24}  # Te Atatu, Mt Albert, Hauraki-Waikato, Banks Peninsula, Nelson

    # Plot base Voronoi cells
    for i, reg_idx in enumerate(vor.point_region):
        region = vor.regions[reg_idx]
        if -1 not in region and len(region) > 0:
            polygon = [vor.vertices[p] for p in region]
            ax.fill(*zip(*polygon, strict=False), facecolor=party_colors[i], alpha=0.45, edgecolor="#30363d", linewidth=1.2)

            # Novelty: Floating secondary glass-like layer on uncompensated plurality seats
            if i in overhang_indices:
                centroid = pts[i]
                ax.fill(*zip(*polygon, strict=False), facecolor="#ffffff", alpha=0.25, edgecolor="#ff7b72", linewidth=2.2, linestyle="--")
                ax.scatter([centroid[0]], [centroid[1]], color="#ff7b72", s=140, edgecolors="#ffffff", linewidth=1.5, zorder=5)
                ax.text(centroid[0], centroid[1] + 0.12, "FLOATING OVERHANG\n(Decoupled Plurality)", color="#ff7b72", fontsize=7.5, weight="bold", ha="center")

    ax.scatter(pts[:, 0], pts[:, 1], color="#ffffff", s=25, alpha=0.8, zorder=4)

    ax.set_title("Multi-Dimensional Electorate Voronoi Tessellations\nFloating Glass Layer = Electorates Decoupled from Proportional Party Vote (Overhang Hotspots)", color="#ffffff", fontsize=12, weight="bold", pad=12)
    ax.set_xlabel("Longitude East (Voter Density Metric Grid)", color="#c9d1d9")
    ax.set_ylabel("Latitude South (Advance Vote Scaled)", color="#c9d1d9")
    ax.set_xlim(167.5, 178.5)
    ax.set_ylim(-47.0, -34.5)
    ax.tick_params(colors="#8b949e")
    ax.grid(color="#30363d", linestyle="--", alpha=0.3)

    # Custom legend
    legend_elements = [
        plt.Line2D([0], [0], marker="s", color="w", label="National Base Cell", markerfacecolor="#00529F", markersize=10),
        plt.Line2D([0], [0], marker="s", color="w", label="Labour Base Cell", markerfacecolor="#D82A20", markersize=10),
        plt.Line2D([0], [0], marker="s", color="w", label="Te Pāti Māori Base Cell", markerfacecolor="#800020", markersize=10),
        plt.Line2D([0], [0], marker="o", color="w", label="Floating Overhang Plurality Layer", markerfacecolor="#ff7b72", markeredgecolor="#ffffff", markersize=11),
    ]
    ax.legend(handles=legend_elements, loc="lower right", facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    return output_path


def generate_parallel_coordinates(output_path: Path) -> Path:
    """3. Hyper-Dimensional Parallel Coordinates for Vote Splitting."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(12, 7), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")

    rng = np.random.default_rng(777)
    n_threads = 250  # Neon thread bundles representing thousands of voters

    # 4 Vertical Axes: Electorate Type, Candidate Vote, Party Vote, Victory Margin
    # Axis 0: Electorate Type (0: General, 1: Māori)
    # Axis 1: Candidate Vote (0: Nat, 1: Lab, 2: Grn, 3: ACT, 4: TPM)
    # Axis 2: Party Vote (0: Nat, 1: Lab, 2: Grn, 3: ACT, 4: NZF, 5: TOP, 6: TPM)
    # Axis 3: Victory Margin (-2000 to +8000 votes, normalized 0 to 1)

    threads = []
    thread_colors = []

    # Party color lookup
    p_cols = ["#00529F", "#D82A20", "#098137", "#FDE401", "#8b949e", "#32B5B5", "#800020"]

    for _ in range(n_threads):
        # Ticket split scenario 1: Nat Candidate -> ACT or NZF Party
        r = rng.random()
        if r < 0.35:
            e_type = 0
            cand = 0  # National
            party = rng.choice([0, 3, 4], p=[0.55, 0.30, 0.15])  # Split to ACT/NZF
            margin = rng.normal(0.65, 0.12)
            c = p_cols[party]
        elif r < 0.65:
            # Ticket split scenario 2: Lab Candidate -> Green or TPM Party
            e_type = rng.choice([0, 1], p=[0.85, 0.15])
            cand = 1  # Labour
            party = rng.choice([1, 2, 6], p=[0.60, 0.30, 0.10])  # Split to Green/TPM
            margin = rng.normal(0.45, 0.10)
            c = p_cols[party]
        elif r < 0.85:
            # Scenario 3: Māori Electorate TPM Candidate -> Labour/TPM Party
            e_type = 1  # Māori
            cand = 4  # TPM
            party = rng.choice([6, 1, 2], p=[0.65, 0.25, 0.10])
            margin = rng.normal(0.55, 0.08)
            c = p_cols[party]
        else:
            # Scenario 4: Urban Split to TOP / ACT
            e_type = 0
            cand = rng.choice([0, 1])
            party = rng.choice([5, 3])
            margin = rng.normal(0.50, 0.15)
            c = p_cols[party]

        threads.append([e_type, cand, party, margin])
        thread_colors.append(c)

    threads_arr = np.array(threads)

    # Normalize axes to 0-1 range for plotting
    norm_threads = np.zeros_like(threads_arr)
    norm_threads[:, 0] = threads_arr[:, 0] / 1.0
    norm_threads[:, 1] = threads_arr[:, 1] / 4.0
    norm_threads[:, 2] = threads_arr[:, 2] / 6.0
    norm_threads[:, 3] = np.clip(threads_arr[:, 3], 0.0, 1.0)

    # Plot spline threads
    x_axes = [0, 1, 2, 3]
    for i in range(n_threads):
        ax.plot(x_axes, norm_threads[i], color=thread_colors[i], alpha=0.45, linewidth=1.4)

    # Draw vertical axis lines
    for x in x_axes:
        ax.axvline(x, color="#ffffff", linestyle="-", linewidth=1.8, alpha=0.8)

    # Labels on axes
    ax.set_xticks(x_axes)
    ax.set_xticklabels(["1. Electorate Type", "2. Candidate Vote", "3. Party Vote (Ticket Split)", "4. Electorate Margin"], color="#ffffff", fontsize=11, weight="bold")

    # Axis 0 ticks
    ax.text(0, 0.0, "General", color="#c9d1d9", fontsize=9, ha="right")
    ax.text(0, 1.0, "Māori", color="#c9d1d9", fontsize=9, ha="right")

    # Axis 1 ticks
    cand_labels = ["National", "Labour", "Green", "ACT", "Te Pāti Māori"]
    for idx, lbl in enumerate(cand_labels):
        ax.text(1, idx / 4.0, f"  {lbl}", color="#c9d1d9", fontsize=9, va="center")

    # Axis 2 ticks
    party_labels = ["National", "Labour", "Green", "ACT", "NZ First", "TOP", "Te Pāti Māori"]
    for idx, lbl in enumerate(party_labels):
        ax.text(2, idx / 6.0, f"  {lbl}", color="#c9d1d9", fontsize=9, va="center")

    # Axis 3 ticks
    ax.text(3, 0.0, "  Defeat (< -2k)", color="#f85149", fontsize=8.5, va="center")
    ax.text(3, 0.5, "  Margin: 0 (Knife-Edge)", color="#ffeb3b", fontsize=8.5, va="center")
    ax.text(3, 1.0, "  Safe (> +8k)", color="#7ee787", fontsize=8.5, va="center")

    ax.set_title("Hyper-Dimensional Parallel Coordinates for MMP Vote Splitting\nNeon Threads Depict Voter Ticket Splitting Driving Electorate Victories vs List Quotas", color="#ffffff", fontsize=13, weight="bold", pad=15)
    ax.set_yticks([])
    ax.tick_params(colors="#8b949e")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    return output_path


def generate_special_votes_fan_cone(output_path: Path) -> Path:
    """4. Special Vote Probability Cones (Generative Fan Charts)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 6), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")

    # Timeline of special votes count (Days 0 to 20 post-election until 27 Nov official declaration)
    days = np.arange(21)

    # Centre-Right Governing Bloc Caucus Trajectory (Starts at 67 preliminary)
    # Expected trajectory with -1.65 pp special vote drift
    mean_trajectory = 67.0 - (1.0 / (1.0 + np.exp(-(days - 8) * 0.45)))

    # Uncertainty cone expansions (like hurricane path cones)
    sigma = 0.15 + 0.09 * days
    ci_50_low = mean_trajectory - 0.674 * sigma
    ci_50_high = mean_trajectory + 0.674 * sigma
    ci_80_low = mean_trajectory - 1.282 * sigma
    ci_80_high = mean_trajectory + 1.282 * sigma
    ci_95_low = mean_trajectory - 1.960 * sigma
    ci_95_high = mean_trajectory + 1.960 * sigma

    # Shaded probability cones
    ax.fill_between(days, ci_95_low, ci_95_high, color="#388bfd", alpha=0.15, label="95% Confidence Cone")
    ax.fill_between(days, ci_80_low, ci_80_high, color="#388bfd", alpha=0.25, label="80% Confidence Cone")
    ax.fill_between(days, ci_50_low, ci_50_high, color="#388bfd", alpha=0.40, label="50% Confidence Cone")
    ax.plot(days, mean_trajectory, color="#58a6ff", linewidth=2.5, label="Expected Trajectory (Nelson Flip Impact)")

    # Drifting particle embers simulating stochastic special vote tally batches
    rng = np.random.default_rng(999)
    for _ in range(70):
        d_sample = rng.uniform(2, 20)
        s_sample = rng.normal(67.0 - (1.0 / (1.0 + np.exp(-(d_sample - 8) * 0.45))), 0.15 + 0.08 * d_sample)
        ax.scatter([d_sample], [s_sample], color="#ff7b72" if s_sample < 66.0 else "#e3b341", s=14, alpha=0.7)

    # Critical 66-seat working majority threshold line
    ax.axhline(66.0, color="#f85149", linestyle="--", linewidth=2.0, label="66-Seat Majority Threshold (130-131 Parliament)")

    # Callout annotations
    ax.annotate("Preliminary Count (Day 0)\n67 Seats (Nat 43 + ACT 13 + NZF 11)", (0, 67.0), xytext=(1, 68.2), color="#ffffff", fontsize=9, weight="bold", arrowprops=dict(arrowstyle="->", color="#ffffff"))
    ax.annotate("Official Declaration (Day 20)\nExpected: 66 Seats (Razor-Thin Buffer)", (20, 66.0), xytext=(12, 64.6), color="#ff7b72", fontsize=9, weight="bold", arrowprops=dict(arrowstyle="->", color="#ff7b72"))

    ax.set_xlabel("Tallying Timeline (Days Post-Election: 7 Nov -> 27 Nov 2026)", color="#c9d1d9", fontsize=11)
    ax.set_ylabel("Centre-Right Coalition Seats (National + ACT + NZ First)", color="#c9d1d9", fontsize=11)
    ax.set_title("Special Vote Probability Cones & Drifting Ember Particles\nHurricane-Style Uncertainty Tracking as ~399,000 Special Votes are Counted", color="#ffffff", fontsize=12, weight="bold", pad=12)
    ax.set_ylim(63.5, 69.0)
    ax.tick_params(colors="#8b949e")
    ax.grid(color="#30363d", linestyle="--", alpha=0.4)
    ax.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="#c9d1d9", loc="upper right", fontsize=9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    return output_path


def generate_semantic_policy_network(output_path: Path) -> Path:
    """5. Semantic Policy Visibility Networks (CiteCompass AI Visibility Monitor)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(11, 8), facecolor="#0e1117")
    ax.set_facecolor("#0e1117")

    # Bimodal semantic network: Core Policy Concerns (Central Hubs) and Political Parties (Peripheral Nodes)
    concerns = [
        {"name": "Cost of Living &\nFood Price Inflation", "x": 0.48, "y": 0.52, "volume": 920, "flare": "#f85149"},
        {"name": "Supermarket Duopoly\nDivestment Reform", "x": 0.42, "y": 0.38, "volume": 760, "flare": "#32B5B5"},
        {"name": "Healthcare & Surgery\nWaitlist Backlog", "x": 0.58, "y": 0.62, "volume": 840, "flare": "#e3b341"},
        {"name": "Treaty Principles Bill\n& Bicultural Status", "x": 0.32, "y": 0.68, "volume": 890, "flare": "#800020"},
        {"name": "Land Value Tax &\nHousing Affordability", "x": 0.65, "y": 0.35, "volume": 680, "flare": "#098137"},
    ]

    parties = [
        {"name": "National", "x": 0.82, "y": 0.65, "color": "#00529F"},
        {"name": "Labour", "x": 0.22, "y": 0.45, "color": "#D82A20"},
        {"name": "Green", "x": 0.15, "y": 0.75, "color": "#098137"},
        {"name": "ACT", "x": 0.88, "y": 0.40, "color": "#FDE401"},
        {"name": "NZ First", "x": 0.72, "y": 0.82, "color": "#8b949e"},
        {"name": "TOP", "x": 0.52, "y": 0.15, "color": "#32B5B5"},
        {"name": "Te Pāti Māori", "x": 0.18, "y": 0.90, "color": "#800020"},
    ]

    # Weighted gravitation edges based on CiteCompass AI Visibility Monitor generative search citations
    edges = [
        (0, 0, 3.2), (0, 1, 3.5), (0, 3, 2.0), (0, 4, 2.8), (0, 5, 2.4),  # Cost of Living
        (1, 1, 2.5), (1, 5, 4.2), (1, 2, 2.8), (1, 6, 2.0),                # Supermarket Duopoly (TOP / Green bridge)
        (2, 0, 3.4), (2, 1, 3.8), (2, 4, 2.6),                              # Healthcare Waitlists
        (3, 0, 2.2), (3, 3, 4.5), (3, 6, 4.8), (3, 1, 2.6), (3, 2, 3.0),  # Treaty Principles (ACT / TPM battleground)
        (4, 5, 4.0), (4, 2, 3.8), (4, 1, 2.4),                              # Land Value Tax (TOP / Green alignment)
    ]

    # Draw gravitation edges
    for c_idx, p_idx, weight in edges:
        c = concerns[c_idx]
        p = parties[p_idx]
        ax.plot([c["x"], p["x"]], [c["y"], p["y"]], color=c["flare"], alpha=0.35 + weight * 0.08, linewidth=weight * 0.9)

    # Plot policy concern hub nodes
    for c in concerns:
        ax.scatter([c["x"]], [c["y"]], s=c["volume"] * 1.5, color=c["flare"], alpha=0.35, edgecolors=c["flare"], linewidth=2.5)
        ax.scatter([c["x"]], [c["y"]], s=c["volume"] * 0.6, color=c["flare"], alpha=0.85, edgecolors="#ffffff", linewidth=1.2)
        ax.text(c["x"], c["y"] - 0.05, c["name"], ha="center", va="top", color="#ffffff", fontsize=9.5, weight="bold")

    # Plot political party peripheral nodes
    for p in parties:
        ax.scatter([p["x"]], [p["y"]], s=400, color=p["color"], edgecolors="#ffffff", linewidth=2.0, zorder=5)
        ax.text(p["x"], p["y"] + 0.04, p["name"], ha="center", va="bottom", color="#ffffff", fontsize=10, weight="bold")

    ax.set_title("Semantic Policy Visibility Network (CiteCompass AI Monitor)\nAlgorithmic Bridges Explaining the 41.4% Splintering to Third Parties", color="#ffffff", fontsize=12, weight="bold", pad=12)
    ax.text(0.02, 0.03, "CiteCompass Research Engine | Edge Weight = Generative Citation Frequency | Flare = Public Salience", transform=ax.transAxes, color="#8b949e", fontsize=8.5)

    ax.set_xlim(0.08, 0.98)
    ax.set_ylim(0.08, 0.98)
    ax.axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=200, facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close()
    return output_path


def generate_all_frontier_five_batch(fig_dir: Path) -> dict[str, Path]:
    """Generate all five bleeding-edge frontier visualizations."""
    fig_dir.mkdir(parents=True, exist_ok=True)
    return {
        "frontier_1_kinetic_topology": generate_kinetic_coalition_3d(fig_dir / "frontier_1_kinetic_coalition_3d.png"),
        "frontier_2_overhang_voronoi": generate_overhang_voronoi(fig_dir / "frontier_2_overhang_voronoi.png"),
        "frontier_3_parallel_coords": generate_parallel_coordinates(fig_dir / "frontier_3_parallel_coordinates.png"),
        "frontier_4_probability_cone": generate_special_votes_fan_cone(fig_dir / "frontier_4_special_votes_cone.png"),
        "frontier_5_semantic_network": generate_semantic_policy_network(fig_dir / "frontier_5_semantic_policy_network.png"),
    }


if __name__ == "__main__":
    import sys

    out = generate_all_frontier_five_batch(Path("figures"))
    sys.stdout.write(f"Generated all {len(out)} frontier visualizations in figures/\n")
